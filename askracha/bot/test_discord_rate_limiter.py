"""
Unit tests for Discord bot rate limiting integration.
"""
import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

# Add bot directory to path
bot_dir = Path(__file__).parent
sys.path.insert(0, str(bot_dir))

from discord_rate_limiter import DiscordRateLimiter


class TestDiscordRateLimiter:
    """Test Discord rate limiting functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a real instance for testing message formatting
        # (tests that need mocking will patch individually)
        with patch('discord_rate_limiter.get_rate_limiter') as mock_get_rate_limiter:
            self.mock_rate_limiter = Mock()
            mock_get_rate_limiter.return_value = self.mock_rate_limiter
            self.discord_rate_limiter = DiscordRateLimiter()
    
    def test_get_user_identifier(self):
        """Test Discord user ID to cross-platform rate limit identifier conversion."""
        discord_user_id = "123456789"
        expected = "auth:discord:123456789"  # Updated for cross-platform consistency
        
        result = self.discord_rate_limiter.get_user_identifier(discord_user_id)
        
        assert result == expected
    
    def test_check_rate_limit(self):
        """Test rate limit checking for Discord users."""
        # Mock rate limit result
        from rate_limiter import RateLimitResult
        mock_result = RateLimitResult(
            allowed=True,
            remaining_seconds=0,
            reset_time=datetime.now() + timedelta(seconds=60),
            user_id="auth:discord:123456789"  # Updated for cross-platform consistency
        )
        self.mock_rate_limiter.check_rate_limit.return_value = mock_result
        
        # Test rate limit check
        discord_user_id = "123456789"
        result = self.discord_rate_limiter.check_rate_limit(discord_user_id)
        
        # Verify rate limiter was called with correct user ID
        self.mock_rate_limiter.check_rate_limit.assert_called_once_with("auth:discord:123456789")
        assert result == mock_result
    
    def test_create_rate_limit_message_seconds(self):
        """Test rate limit message creation for seconds."""
        remaining_seconds = 30
        username = "TestUser"
        
        message = self.discord_rate_limiter.create_rate_limit_message(remaining_seconds, username)
        
        assert "TestUser" in message
        assert "30 seconds" in message
        assert "⏰" in message or "🚦" in message or "⏳" in message or "🕐" in message
        assert "💡" in message
    
    def test_create_rate_limit_message_minutes(self):
        """Test rate limit message creation for minutes."""
        remaining_seconds = 90  # 1 minute 30 seconds
        
        message = self.discord_rate_limiter.create_rate_limit_message(remaining_seconds)
        
        assert "1 minute" in message
        assert "30 seconds" in message
        assert "💡" in message
    
    def test_create_rate_limit_message_exact_minute(self):
        """Test rate limit message creation for exact minutes."""
        remaining_seconds = 120  # 2 minutes exactly
        
        message = self.discord_rate_limiter.create_rate_limit_message(remaining_seconds)
        
        assert "2 minutes" in message
        assert "seconds" not in message.split("2 minutes")[1]  # No seconds after minutes
    
    def test_create_rate_limit_message_singular(self):
        """Test rate limit message creation for singular values."""
        # Test 1 second
        message = self.discord_rate_limiter.create_rate_limit_message(1)
        assert "1 second" in message
        assert "1 seconds" not in message
        
        # Test 1 minute
        message = self.discord_rate_limiter.create_rate_limit_message(60)
        assert "1 minute" in message
        assert "1 minutes" not in message
    
    def test_create_cross_platform_message(self):
        """Test cross-platform rate limit message creation."""
        remaining_seconds = 45
        
        message = self.discord_rate_limiter.create_cross_platform_message(remaining_seconds)
        
        assert "web interface" in message
        assert "45 seconds" in message
        assert "shared between Discord" in message
        assert "⏰" in message
        assert "🔗" in message
    
    @pytest.mark.asyncio
    async def test_handle_rate_limited_user(self):
        """Test handling of rate limited users."""
        # Mock Discord message
        mock_message = Mock()
        mock_message.author.display_name = "TestUser"
        mock_message.author.id = 123456789
        mock_message.reply = AsyncMock()
        
        # Mock rate limit result
        from rate_limiter import RateLimitResult
        rate_result = RateLimitResult(
            allowed=False,
            remaining_seconds=30,
            reset_time=datetime.now() + timedelta(seconds=30),
            user_id="discord:123456789"
        )
        
        # Handle rate limited user
        await self.discord_rate_limiter.handle_rate_limited_user(mock_message, rate_result)
        
        # Verify reply was called
        mock_message.reply.assert_called_once()
        call_args = mock_message.reply.call_args
        message_sent = call_args[0][0]
        
        assert "TestUser" in message_sent
        assert "30 seconds" in message_sent
        assert call_args[1]['mention_author'] is False
    
    @pytest.mark.asyncio
    async def test_handle_rate_limited_user_discord_error(self):
        """Test handling Discord errors when sending rate limit messages."""
        import discord
        
        # Mock Discord message that raises HTTPException
        mock_message = Mock()
        mock_message.author.display_name = "TestUser"
        mock_message.author.id = 123456789
        mock_message.reply = AsyncMock(side_effect=discord.HTTPException(Mock(), "Test error"))
        
        # Mock rate limit result
        from rate_limiter import RateLimitResult
        rate_result = RateLimitResult(
            allowed=False,
            remaining_seconds=30,
            reset_time=datetime.now() + timedelta(seconds=30),
            user_id="discord:123456789"
        )
        
        # Should not raise exception
        await self.discord_rate_limiter.handle_rate_limited_user(mock_message, rate_result)
        
        # Verify reply was attempted
        mock_message.reply.assert_called_once()
    
    def test_reset_user_rate_limit(self):
        """Test resetting user rate limit."""
        self.mock_rate_limiter.reset_user_rate_limit.return_value = True
        
        discord_user_id = "123456789"
        result = self.discord_rate_limiter.reset_user_rate_limit(discord_user_id)
        
        # Verify rate limiter was called with correct user ID
        self.mock_rate_limiter.reset_user_rate_limit.assert_called_once_with("auth:discord:123456789")
        assert result is True
    
    def test_get_user_rate_limit_status(self):
        """Test getting user rate limit status."""
        from rate_limiter import RateLimitResult
        mock_result = RateLimitResult(
            allowed=False,
            remaining_seconds=30,
            reset_time=datetime.now() + timedelta(seconds=30),
            user_id="discord:123456789"
        )
        self.mock_rate_limiter.get_user_rate_limit_status.return_value = mock_result
        
        discord_user_id = "123456789"
        result = self.discord_rate_limiter.get_user_rate_limit_status(discord_user_id)
        
        # Verify rate limiter was called with correct user ID
        self.mock_rate_limiter.get_user_rate_limit_status.assert_called_once_with("discord:123456789")
        assert result == mock_result
    
    def test_health_check(self):
        """Test health check functionality."""
        self.mock_rate_limiter.health_check.return_value = True
        
        result = self.discord_rate_limiter.health_check()
        
        self.mock_rate_limiter.health_check.assert_called_once()
        assert result is True


class TestDiscordRateLimiterIntegration:
    """Integration tests for Discord rate limiter."""
    
    @pytest.mark.asyncio
    async def test_message_consistency(self):
        """Test that rate limit messages are consistent for the same cooldown."""
        discord_rate_limiter = DiscordRateLimiter()
        
        # Same remaining seconds should produce the same message
        remaining_seconds = 42
        message1 = discord_rate_limiter.create_rate_limit_message(remaining_seconds, "User1")
        message2 = discord_rate_limiter.create_rate_limit_message(remaining_seconds, "User2")
        
        # Messages should have the same structure (same emoji/template)
        # but different usernames
        assert "User1" in message1
        assert "User2" in message2
        
        # Extract the template by removing usernames
        template1 = message1.replace("User1, ", "")
        template2 = message2.replace("User2, ", "")
        
        assert template1 == template2


if __name__ == "__main__":
    pytest.main([__file__])