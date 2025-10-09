"""
Discord bot rate limiting integration.
Provides rate limiting functionality specifically for Discord bot interactions.
"""
import logging
from typing import Optional
from datetime import datetime
import discord

from rate_limiter import get_rate_limiter, RateLimitResult
from cross_platform_user_mapper import get_user_mapper


logger = logging.getLogger(__name__)


class DiscordRateLimiter:
    """Discord-specific rate limiting functionality."""
    
    def __init__(self):
        """Initialize Discord rate limiter."""
        self.rate_limiter = get_rate_limiter()
        self.user_mapper = get_user_mapper()
        logger.info("Discord rate limiter initialized with cross-platform support")
    
    def get_user_identifier(self, discord_user_id: str) -> str:
        """
        Convert Discord user ID to cross-platform rate limit identifier.
        
        Args:
            discord_user_id: Discord user ID (string)
            
        Returns:
            Cross-platform user identifier for rate limiting
        """
        identity = self.user_mapper.create_discord_user_identity(discord_user_id)
        return self.user_mapper.get_rate_limit_key(identity)
    
    def check_rate_limit(self, discord_user_id: str) -> RateLimitResult:
        """
        Check rate limit for Discord user.
        
        Args:
            discord_user_id: Discord user ID
            
        Returns:
            RateLimitResult with rate limit status
        """
        user_id = self.get_user_identifier(discord_user_id)
        return self.rate_limiter.check_rate_limit(user_id)
    
    def create_rate_limit_message(self, remaining_seconds: int, username: str = None) -> str:
        """
        Create Discord-friendly rate limit message with emojis and countdown.
        
        Args:
            remaining_seconds: Seconds until user can ask again
            username: Optional username for personalization
            
        Returns:
            Formatted Discord message
        """
        # Format time in a user-friendly way
        if remaining_seconds < 60:
            time_str = f"{remaining_seconds} second{'s' if remaining_seconds != 1 else ''}"
        else:
            minutes = remaining_seconds // 60
            seconds = remaining_seconds % 60
            if seconds == 0:
                time_str = f"{minutes} minute{'s' if minutes != 1 else ''}"
            else:
                time_str = f"{minutes} minute{'s' if minutes != 1 else ''} and {seconds} second{'s' if seconds != 1 else ''}"
        
        # Create personalized message
        greeting = f"{username}, " if username else ""
        
        messages = [
            f"⏰ {greeting}you're asking questions a bit too quickly! Please wait **{time_str}** before asking another question.",
            f"🚦 {greeting}slow down there! You can ask your next question in **{time_str}**.",
            f"⏳ {greeting}you're on cooldown! Please wait **{time_str}** before asking again.",
            f"🕐 {greeting}take a breather! You can ask another question in **{time_str}**."
        ]
        
        # Use hash of remaining seconds to consistently pick the same message for the same cooldown
        message_index = remaining_seconds % len(messages)
        base_message = messages[message_index]
        
        # Add helpful tip
        tip = "\n💡 *This helps me provide better responses to everyone!*"
        
        return base_message + tip
    
    def create_cross_platform_message(self, remaining_seconds: int) -> str:
        """
        Create message explaining cross-platform rate limiting.
        
        Args:
            remaining_seconds: Seconds until user can ask again
            
        Returns:
            Formatted message explaining cross-platform limits
        """
        time_str = f"{remaining_seconds} second{'s' if remaining_seconds != 1 else ''}"
        
        return (
            f"⏰ You recently asked a question on the web interface! "
            f"Please wait **{time_str}** before asking another question.\n\n"
            f"🔗 *Rate limits are shared between Discord and the web interface to ensure fair usage.*"
        )
    
    async def handle_rate_limited_user(self, message: discord.Message, rate_result: RateLimitResult) -> None:
        """
        Handle rate limited user by sending appropriate message.
        
        Args:
            message: Discord message that triggered rate limit
            rate_result: Rate limit result with timing information
        """
        try:
            # Determine if this is likely a cross-platform rate limit
            # (if the user hasn't used Discord recently, it might be from web)
            user_id = self.get_user_identifier(str(message.author.id))
            
            # Create appropriate message
            username = message.author.display_name
            rate_limit_msg = self.create_rate_limit_message(
                rate_result.remaining_seconds, 
                username
            )
            
            # Send rate limit message
            await message.reply(rate_limit_msg, mention_author=False)
            
            logger.info(
                f"Rate limit message sent to {message.author} ({message.author.id}), "
                f"{rate_result.remaining_seconds}s remaining"
            )
            
        except discord.HTTPException as e:
            logger.error(f"Failed to send rate limit message to {message.author}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error handling rate limited user {message.author}: {e}")
    
    def reset_user_rate_limit(self, discord_user_id: str) -> bool:
        """
        Reset rate limit for Discord user (admin function).
        
        Args:
            discord_user_id: Discord user ID
            
        Returns:
            True if reset successful
        """
        user_id = self.get_user_identifier(discord_user_id)
        return self.rate_limiter.reset_user_rate_limit(user_id)
    
    def get_user_rate_limit_status(self, discord_user_id: str) -> Optional[RateLimitResult]:
        """
        Get rate limit status for Discord user.
        
        Args:
            discord_user_id: Discord user ID
            
        Returns:
            RateLimitResult if user has active rate limit, None otherwise
        """
        user_id = self.get_user_identifier(discord_user_id)
        return self.rate_limiter.get_user_rate_limit_status(user_id)
    
    def health_check(self) -> bool:
        """
        Check if rate limiting system is healthy.
        
        Returns:
            True if system is healthy
        """
        return self.rate_limiter.health_check()