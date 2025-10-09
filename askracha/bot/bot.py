"""
Discord bot client implementation.
Handles Discord WebSocket connection, message events, and bot lifecycle.
"""
import logging
import asyncio
from typing import Optional
import discord
from discord.ext import commands
import time
from dataclasses import dataclass

from api_client import APIClient, APIResponse
from message_processor import MessageProcessor, MessageContext
from config import BotConfig
from discord_rate_limiter import DiscordRateLimiter

logger = logging.getLogger(__name__)


@dataclass
class BotMetrics:
    """Bot performance metrics."""
    questions_processed: int = 0
    successful_responses: int = 0
    failed_responses: int = 0
    total_response_time: float = 0.0
    start_time: float = 0.0
    
    @property
    def average_response_time(self) -> float:
        """Calculate average response time."""
        if self.questions_processed == 0:
            return 0.0
        return self.total_response_time / self.questions_processed
    
    @property
    def uptime(self) -> float:
        """Calculate bot uptime in seconds."""
        if self.start_time == 0:
            return 0.0
        return time.time() - self.start_time


class DiscordBot(commands.Bot):
    """Main Discord bot client with event handling and message processing."""
    
    def __init__(self, config: BotConfig, api_client: APIClient, message_processor: MessageProcessor):
        """Initialize the Discord bot with configuration and dependencies."""
        # Configure bot intents
        intents = discord.Intents.default()
        intents.message_content = True  # Required to read message content
        
        # Initialize the bot with command prefix (though we won't use commands)
        super().__init__(command_prefix='!', intents=intents, help_command=None)
        
        self.config = config
        self.api_client = api_client
        self.message_processor = message_processor
        self.discord_rate_limiter = DiscordRateLimiter()
        self.metrics = BotMetrics()
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self.channel_sessions: dict[int, str] = {}
        
        logger.info("Discord bot client initialized with rate limiting")
    
    def _is_bot_mentioned(self, message: discord.Message) -> bool:
        """Return True if the bot user or its managed role is mentioned in the message."""
        try:
            if self.user in getattr(message, 'mentions', []):
                return True
            
            for role in getattr(message, 'role_mentions', []) or []:
                tags = getattr(role, 'tags', None)
                bot_id = getattr(tags, 'bot_id', None) if tags else None
                if bot_id and int(bot_id) == self.user.id:
                    return True
        except Exception:
            return False
        return False
    
    async def _get_or_create_session(self, channel_id: int) -> Optional[str]:
        """Return cached session_id for channel or create a new one via API."""
        session_id = self.channel_sessions.get(channel_id)
        if session_id:
            return session_id
        new_session = await self.api_client.create_chat_session({"channel_id": str(channel_id)})
        if new_session:
            self.channel_sessions[channel_id] = new_session
            logger.debug(f"Created new chat session for channel {channel_id}: {new_session}")
            return new_session
        logger.warning(f"Failed to create chat session for channel {channel_id}")
        return None

    async def _answer_with_chat_or_legacy(self, message: discord.Message, question: str) -> None:
        """Answer using chat context if enabled, otherwise legacy; with graceful fallback."""
        channel_id = message.channel.id
        use_context = getattr(self.config, 'use_chat_context', False)

        if not use_context:
            api_response = await self.api_client.query_rag(question)
            if api_response.success:
                await self._send_response(message, self.message_processor.format_response({
                    'success': True,
                    'answer': api_response.answer,
                    'sources': api_response.sources,
                }))
            else:
                await self._send_response(message, self._get_error_response(api_response.error_message))
            return

        session_id = await self._get_or_create_session(channel_id)
        if session_id:
            api_response = await self.api_client.chat_query(session_id, question)
            if api_response.success:
                await self._send_response(message, self.message_processor.format_response({
                    'success': True,
                    'answer': api_response.answer,
                    'sources': api_response.sources,
                }))
                return
            if api_response.error_message and (
                'invalid session' in api_response.error_message.lower() or
                'missing session' in api_response.error_message.lower()
            ):
                logger.info(f"Session invalid for channel {channel_id}, recreating...")
                self.channel_sessions.pop(channel_id, None)
                session_id = await self._get_or_create_session(channel_id)
                if session_id:
                    retry_resp = await self.api_client.chat_query(session_id, question)
                    if retry_resp.success:
                        await self._send_response(message, self.message_processor.format_response({
                            'success': True,
                            'answer': retry_resp.answer,
                            'sources': retry_resp.sources,
                        }))
                        return
                    logger.warning(f"chat_query retry failed: {retry_resp.error_message}")

        legacy_resp = await self.api_client.query_rag(question)
        if legacy_resp.success:
            await self._send_response(message, self.message_processor.format_response({
                'success': True,
                'answer': legacy_resp.answer,
                'sources': legacy_resp.sources,
            }))
        else:
            await self._send_response(message, self._get_error_response(legacy_resp.error_message))

    async def setup_hook(self):
        """Called when the bot is starting up."""
        logger.info("Setting up Discord bot...")
        self.metrics.start_time = time.time()
    
    async def on_ready(self):
        """Handle bot ready event."""
        logger.info(f"✅ Bot is ready! Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")
        
        # Log guild information
        for guild in self.guilds:
            logger.info(f"  - {guild.name} (ID: {guild.id}, Members: {guild.member_count})")
        
        # Reset reconnect attempts on successful connection
        self._reconnect_attempts = 0
        
        # Perform API health check
        try:
            is_healthy = await self.api_client.health_check()
            if is_healthy:
                logger.info("✅ AskRacha API health check passed")
            else:
                logger.warning("⚠️ AskRacha API health check failed - bot will still start")
        except Exception as e:
            logger.warning(f"⚠️ API health check error: {e} - bot will still start")
    
    async def on_disconnect(self):
        """Handle bot disconnect event."""
        logger.warning("Bot disconnected from Discord")
    
    async def on_resumed(self):
        """Handle bot resume event after reconnection."""
        logger.info("Bot connection resumed")
        self._reconnect_attempts = 0
    
    async def on_error(self, event, *args, **kwargs):
        """Handle general bot errors."""
        logger.error(f"Bot error in event {event}", exc_info=True)
    
    async def on_message(self, message: discord.Message):
        """Handle incoming Discord messages."""
        # Ignore messages from the bot itself
        if message.author == self.user:
            return
        
        # Ignore messages from other bots
        if message.author.bot:
            return
        
        if not self._is_bot_mentioned(message):
            logger.debug("Message ignored: bot not mentioned (no user or managed role mention)")
            return
        
        logger.debug(f"Received mention from {message.author} in {message.guild.name if message.guild else 'DM'}")
        
        # Extract question from the message
        question = self.message_processor.extract_question(message.content)
        
        if not question:
            await self._send_clarification_request(message)
            return
        
        if not self.message_processor.is_valid_question(question):
            await self._send_clarification_request(message)
            return
        
        # Create message context
        context = MessageContext(
            user_id=str(message.author.id),
            username=message.author.display_name,
            channel_id=str(message.channel.id),
            guild_id=str(message.guild.id) if message.guild else "DM",
            message_id=str(message.id),
            timestamp=message.created_at,
            question=question
        )
        
        # Check rate limit before processing
        await self.handle_mention_with_rate_limit(message, context)
    
    async def handle_mention_with_rate_limit(self, message: discord.Message, context: MessageContext):
        """Process @racha mentions with rate limiting check."""
        try:
            # Check rate limit first
            rate_result = self.discord_rate_limiter.check_rate_limit(context.user_id)
            
            if not rate_result.allowed:
                # User is rate limited, send rate limit message
                await self.discord_rate_limiter.handle_rate_limited_user(message, rate_result)
                logger.info(f"Rate limited user {context.username} ({context.user_id}), {rate_result.remaining_seconds}s remaining")
                return
            
            # Rate limit check passed, process the question
            await self.handle_mention(message, context)
            
        except Exception as e:
            logger.error(f"Error in rate limit check for {context.username}: {e}")
            # Fail open - process the question if rate limiting fails
            await self.handle_mention(message, context)

    async def handle_mention(self, message: discord.Message, context: MessageContext):
        """Process @racha mentions with concurrent handling."""
        start_time = time.time()
        
        try:
            logger.info(f"Processing question from {context.username}: {context.question[:100]}...")
            
            # Show typing indicator while processing
            async with message.channel.typing():
                await self._answer_with_chat_or_legacy(message, context.question)
        
        except discord.HTTPException as e:
            logger.error(f"Discord API error while responding to {context.username}: {e}")
            self.metrics.failed_responses += 1
            
            # Try to send a simple error message
            try:
                await message.channel.send("I encountered an error while trying to respond. Please try again! 🔧")
            except discord.HTTPException:
                logger.error("Failed to send error message due to Discord API issues")
        
        except discord.Forbidden:
            logger.error(f"Missing permissions to respond in channel {context.channel_id}")
            self.metrics.failed_responses += 1
        
        except Exception as e:
            logger.error(f"Unexpected error while handling mention from {context.username}: {e}", exc_info=True)
            self.metrics.failed_responses += 1
            
            # Try to send a generic error message
            try:
                await message.channel.send("I encountered an unexpected error. Please try again later! 🔧")
            except discord.HTTPException:
                logger.error("Failed to send error message due to Discord API issues")
        
        finally:
            # Update metrics
            response_time = time.time() - start_time
            self.metrics.questions_processed += 1
            self.metrics.total_response_time += response_time
            
            logger.debug(f"Total processing time for {context.username}: {response_time:.2f}s")
    
    async def _send_response(self, message: discord.Message, response: str):
        """Send response to Discord with error handling."""
        try:
            # Try to reply to the original message
            await message.reply(response, mention_author=False)
        except discord.HTTPException as e:
            if e.status == 413:  # Payload too large
                # Try sending without reply
                truncated = self.message_processor.truncate_response(response, max_length=1900)
                await message.channel.send(truncated)
            else:
                raise
    
    async def _send_clarification_request(self, message: discord.Message):
        """Send a clarification request for invalid questions."""
        clarification_msg = "I'd love to help! Could you please ask a more specific question about Storacha? 🤔"
        
        try:
            await message.reply(clarification_msg, mention_author=False)
            logger.debug(f"Sent clarification request to {message.author}")
        except discord.HTTPException as e:
            logger.error(f"Failed to send clarification request: {e}")
    
    def _get_error_response(self, error_message: Optional[str]) -> str:
        """Get appropriate error response based on error type."""
        if not error_message:
            return "I'm having trouble processing your question right now. Please try again later! 🔧"
        
        error_lower = error_message.lower()
        
        if "timeout" in error_lower:
            return "I'm taking longer than usual to process your question. Please try asking again! ⏱️"
        elif "connection" in error_lower or "unavailable" in error_lower:
            return "I'm having trouble connecting to my knowledge base right now. Please try again in a few minutes! 🔧"
        elif "rate limit" in error_lower:
            return "I'm receiving a lot of questions right now. Please wait a moment and try again! 🚦"
        else:
            return "I'm having trouble processing your question right now. Please try again later! 🔧"
    
    async def start_bot(self):
        """Start the Discord bot with error handling."""
        try:
            logger.info("Starting Discord bot...")
            await self.start(self.config.discord_token)
        except discord.LoginFailure:
            logger.error("❌ Failed to login to Discord - check your DISCORD_TOKEN")
            raise
        except discord.HTTPException as e:
            logger.error(f"❌ Discord HTTP error during startup: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error during bot startup: {e}")
            raise
    
    async def close_bot(self):
        """Gracefully close the bot and cleanup resources."""
        logger.info("Shutting down Discord bot...")
        
        # Close API client session
        await self.api_client.close()
        
        # Close Discord connection
        await self.close()
        
        # Log final metrics
        uptime = self.metrics.uptime
        logger.info(f"Bot shutdown complete. Final metrics:")
        logger.info(f"  - Uptime: {uptime:.1f}s")
        logger.info(f"  - Questions processed: {self.metrics.questions_processed}")
        logger.info(f"  - Successful responses: {self.metrics.successful_responses}")
        logger.info(f"  - Failed responses: {self.metrics.failed_responses}")
        if self.metrics.questions_processed > 0:
            success_rate = (self.metrics.successful_responses / self.metrics.questions_processed) * 100
            logger.info(f"  - Success rate: {success_rate:.1f}%")
            logger.info(f"  - Average response time: {self.metrics.average_response_time:.2f}s")
    
    async def reconnect(self):
        """Handle connection recovery with exponential backoff."""
        if self._reconnect_attempts >= self._max_reconnect_attempts:
            logger.error(f"Max reconnection attempts ({self._max_reconnect_attempts}) reached")
            return False
        
        self._reconnect_attempts += 1
        wait_time = min(60, 2 ** self._reconnect_attempts)  # Exponential backoff, max 60s
        
        logger.info(f"Attempting to reconnect (attempt {self._reconnect_attempts}/{self._max_reconnect_attempts}) in {wait_time}s...")
        await asyncio.sleep(wait_time)
        
        try:
            await self.start_bot()
            return True
        except Exception as e:
            logger.error(f"Reconnection attempt {self._reconnect_attempts} failed: {e}")
            return False