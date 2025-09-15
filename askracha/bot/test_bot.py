"""
Integration tests for Discord bot functionality.
Tests bot message handling, concurrent requests, and error scenarios.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import discord

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from bot import DiscordBot, BotMetrics
from api_client import APIClient, APIResponse
from message_processor import MessageProcessor, MessageContext
from config import BotConfig


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return BotConfig(
        discord_token="test_token",
        askracha_api_url="http://localhost:5000",
        api_timeout=10,
        max_response_length=2000,
        log_level="INFO",
        retry_attempts=3,
        retry_delay=1.0
    )


@pytest.fixture
def mock_api_client():
    """Create a mock API client for testing."""
    client = AsyncMock(spec=APIClient)
    return client


@pytest.fixture
def mock_message_processor():
    """Create a mock message processor for testing."""
    processor = MagicMock(spec=MessageProcessor)
    processor.extract_question.return_value = "How do I upload files?"
    processor.is_valid_question.return_value = True
    processor.format_response.return_value = "Here's how to upload files..."
    return processor


@pytest.fixture
async def discord_bot(mock_config, mock_api_client, mock_message_processor):
    """Create a Discord bot instance for testing."""
    with patch('bot.commands.Bot.__init__'):
        bot = DiscordBot(mock_config, mock_api_client, mock_message_processor)
        bot.user = MagicMock()
        bot.user.id = 12345
        yield bot


class TestDiscordBot:
    """Test cases for Discord bot functionality."""
    
    @pytest.mark.asyncio
    async def test_bot_initialization(self, mock_config, mock_api_client, mock_message_processor):
        """Test bot initializes correctly with all components."""
        with patch('bot.commands.Bot.__init__'):
            bot = DiscordBot(mock_config, mock_api_client, mock_message_processor)
            
            assert bot.config == mock_config
            assert bot.api_client == mock_api_client
            assert bot.message_processor == mock_message_processor
            assert isinstance(bot.metrics, BotMetrics)
            assert bot._reconnect_attempts == 0
    
    @pytest.mark.asyncio
    async def test_on_ready_logs_guild_info(self, discord_bot):
        """Test that on_ready logs guild information correctly."""
        # Mock guilds
        guild1 = MagicMock()
        guild1.name = "Test Guild 1"
        guild1.id = 111
        guild1.member_count = 100
        
        guild2 = MagicMock()
        guild2.name = "Test Guild 2"
        guild2.id = 222
        guild2.member_count = 200
        
        discord_bot.guilds = [guild1, guild2]
        discord_bot.user.id = 12345
        discord_bot.user.__str__ = lambda: "TestBot"
        
        # Mock API health check
        discord_bot.api_client.health_check.return_value = True
        
        with patch('bot.logger') as mock_logger:
            await discord_bot.on_ready()
            
            # Verify logging calls
            mock_logger.info.assert_any_call("✅ Bot is ready! Logged in as TestBot (ID: 12345)")
            mock_logger.info.assert_any_call("Connected to 2 guild(s)")
            mock_logger.info.assert_any_call("✅ AskRacha API health check passed")
    
    @pytest.mark.asyncio
    async def test_on_message_ignores_bot_messages(self, discord_bot):
        """Test that bot ignores messages from itself and other bots."""
        # Test ignoring own messages
        message = MagicMock()
        message.author = discord_bot.user
        
        await discord_bot.on_message(message)
        discord_bot.message_processor.extract_question.assert_not_called()
        
        # Test ignoring other bot messages
        message.author = MagicMock()
        message.author.bot = True
        discord_bot.user = MagicMock()
        
        await discord_bot.on_message(message)
        discord_bot.message_processor.extract_question.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_on_message_ignores_non_mentions(self, discord_bot):
        """Test that bot ignores messages that don't mention it."""
        message = MagicMock()
        message.author = MagicMock()
        message.author.bot = False
        message.mentions = []  # No mentions
        
        await discord_bot.on_message(message)
        discord_bot.message_processor.extract_question.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_on_message_processes_valid_mention(self, discord_bot):
        """Test that bot processes valid mentions correctly."""
        # Setup message mock
        message = MagicMock()
        message.author = MagicMock()
        message.author.bot = False
        message.author.id = 67890
        message.author.display_name = "TestUser"
        message.mentions = [discord_bot.user]
        message.content = "<@12345> How do I upload files?"
        message.guild = MagicMock()
        message.guild.id = 111
        message.guild.name = "Test Guild"
        message.channel = MagicMock()
        message.channel.id = 222
        message.id = 333
        message.created_at = datetime.now()
        
        # Setup mocks
        discord_bot.message_processor.extract_question.return_value = "How do I upload files?"
        discord_bot.message_processor.is_valid_question.return_value = True
        
        with patch.object(discord_bot, 'handle_mention') as mock_handle:
            await discord_bot.on_message(message)
            
            # Verify handle_mention was called
            mock_handle.assert_called_once()
            call_args = mock_handle.call_args
            assert call_args[0][0] == message  # First argument is the message
            
            # Verify context was created correctly
            context = call_args[0][1]
            assert isinstance(context, MessageContext)
            assert context.user_id == "67890"
            assert context.username == "TestUser"
            assert context.question == "How do I upload files?"
    
    @pytest.mark.asyncio
    async def test_handle_mention_successful_response(self, discord_bot):
        """Test successful question processing and response."""
        # Setup message and context
        message = MagicMock()
        message.channel = MagicMock()
        message.channel.typing.return_value.__aenter__ = AsyncMock()
        message.channel.typing.return_value.__aexit__ = AsyncMock()
        message.reply = AsyncMock()
        
        context = MessageContext(
            user_id="123",
            username="TestUser",
            channel_id="456",
            guild_id="789",
            message_id="999",
            timestamp=datetime.now(),
            question="How do I upload files?"
        )
        
        # Setup successful API response
        api_response = APIResponse(
            success=True,
            answer="To upload files, use the web interface...",
            sources=["docs.storacha.network"],
            response_time=1.5
        )
        discord_bot.api_client.query_rag.return_value = api_response
        
        # Setup message processor response
        formatted_response = "**Hey! There, here's your answer:**\n\nTo upload files, use the web interface..."
        discord_bot.message_processor.format_response.return_value = formatted_response
        
        with patch.object(discord_bot, '_send_response') as mock_send:
            await discord_bot.handle_mention(message, context)
            
            # Verify API was called
            discord_bot.api_client.query_rag.assert_called_once_with("How do I upload files?")
            
            # Verify response was formatted and sent
            discord_bot.message_processor.format_response.assert_called_once()
            mock_send.assert_called_once_with(message, formatted_response)
            
            # Verify metrics were updated
            assert discord_bot.metrics.successful_responses == 1
            assert discord_bot.metrics.questions_processed == 1
    
    @pytest.mark.asyncio
    async def test_handle_mention_api_failure(self, discord_bot):
        """Test handling of API failures."""
        # Setup message and context
        message = MagicMock()
        message.channel = MagicMock()
        message.channel.typing.return_value.__aenter__ = AsyncMock()
        message.channel.typing.return_value.__aexit__ = AsyncMock()
        
        context = MessageContext(
            user_id="123",
            username="TestUser",
            channel_id="456",
            guild_id="789",
            message_id="999",
            timestamp=datetime.now(),
            question="How do I upload files?"
        )
        
        # Setup failed API response
        api_response = APIResponse(
            success=False,
            answer="",
            sources=[],
            response_time=0.0,
            error_message="Connection timeout"
        )
        discord_bot.api_client.query_rag.return_value = api_response
        
        with patch.object(discord_bot, '_send_response') as mock_send:
            await discord_bot.handle_mention(message, context)
            
            # Verify error response was sent
            mock_send.assert_called_once()
            error_response = mock_send.call_args[0][1]
            assert "taking longer than usual" in error_response
            
            # Verify metrics were updated
            assert discord_bot.metrics.failed_responses == 1
            assert discord_bot.metrics.questions_processed == 1
    
    @pytest.mark.asyncio
    async def test_concurrent_request_handling(self, discord_bot):
        """Test that bot handles multiple simultaneous requests."""
        # Setup multiple messages
        messages = []
        contexts = []
        
        for i in range(3):
            message = MagicMock()
            message.channel = MagicMock()
            message.channel.typing.return_value.__aenter__ = AsyncMock()
            message.channel.typing.return_value.__aexit__ = AsyncMock()
            messages.append(message)
            
            context = MessageContext(
                user_id=str(100 + i),
                username=f"User{i}",
                channel_id=str(200 + i),
                guild_id="789",
                message_id=str(300 + i),
                timestamp=datetime.now(),
                question=f"Question {i}?"
            )
            contexts.append(context)
        
        # Setup API responses with delays
        async def mock_query_rag(question):
            await asyncio.sleep(0.1)  # Simulate API delay
            return APIResponse(
                success=True,
                answer=f"Answer for {question}",
                sources=[],
                response_time=0.1
            )
        
        discord_bot.api_client.query_rag.side_effect = mock_query_rag
        
        with patch.object(discord_bot, '_send_response') as mock_send:
            # Process all requests concurrently
            tasks = [
                discord_bot.handle_mention(msg, ctx) 
                for msg, ctx in zip(messages, contexts)
            ]
            
            start_time = asyncio.get_event_loop().time()
            await asyncio.gather(*tasks)
            end_time = asyncio.get_event_loop().time()
            
            # Verify all requests were processed
            assert mock_send.call_count == 3
            assert discord_bot.metrics.successful_responses == 3
            assert discord_bot.metrics.questions_processed == 3
            
            # Verify concurrent processing (should be faster than sequential)
            total_time = end_time - start_time
            assert total_time < 0.25  # Should be much less than 3 * 0.1 = 0.3s


if __name__ == "__main__":
    pytest.main([__file__])