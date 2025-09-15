"""
Integration tests for cross-platform rate limiting consistency.
Tests that rate limits work consistently across web and Discord interfaces.
"""
import pytest
import time
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from cross_platform_user_mapper import CrossPlatformUserMapper, UserIdentity
from rate_limiter import RateLimiter, RateLimitConfig, RateLimitResult

# Add bot directory to path for Discord components
bot_dir = backend_dir.parent / 'bot'
sys.path.insert(0, str(bot_dir))

from discord_rate_limiter import DiscordRateLimiter


class TestCrossPlatformUserMapper:
    """Test cross-platform user identification mapping."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mapper = CrossPlatformUserMapper()
    
    def test_web_authenticated_user_identity(self):
        """Test web authenticated user identity creation."""
        headers = {'X-User-ID': 'user123'}
        session_data = {}
        remote_addr = '192.168.1.1'
        
        identity = self.mapper.create_web_user_identity(headers, session_data, remote_addr)
        
        assert identity.platform == 'web'
        assert identity.platform_user_id == 'user123'
        assert identity.unified_user_id == 'auth:web:user123'
        assert identity.user_type == 'authenticated'
    
    def test_web_session_user_identity(self):
        """Test web session-based user identity creation."""
        headers = {}
        session_data = {'user_id': 'session456'}
        remote_addr = '192.168.1.1'
        
        identity = self.mapper.create_web_user_identity(headers, session_data, remote_addr)
        
        assert identity.platform == 'web'
        assert identity.platform_user_id == 'session456'
        assert identity.unified_user_id == 'auth:web:session456'
        assert identity.user_type == 'authenticated'
    
    def test_web_anonymous_user_identity(self):
        """Test web anonymous user identity creation."""
        headers = {}
        session_data = {}
        remote_addr = '192.168.1.1'
        
        identity = self.mapper.create_web_user_identity(headers, session_data, remote_addr)
        
        assert identity.platform == 'web'
        assert identity.platform_user_id == '192.168.1.1'
        assert identity.unified_user_id == 'anon:web:192.168.1.1'
        assert identity.user_type == 'anonymous'
    
    def test_web_proxy_ip_handling(self):
        """Test web user identity with proxy headers."""
        headers = {'X-Forwarded-For': '203.0.113.1, 192.168.1.1'}
        session_data = {}
        remote_addr = '10.0.0.1'
        
        identity = self.mapper.create_web_user_identity(headers, session_data, remote_addr)
        
        assert identity.platform_user_id == '203.0.113.1'  # First IP from X-Forwarded-For
        assert identity.unified_user_id == 'anon:web:203.0.113.1'
    
    def test_discord_user_identity(self):
        """Test Discord user identity creation."""
        discord_user_id = '123456789012345678'
        
        identity = self.mapper.create_discord_user_identity(discord_user_id)
        
        assert identity.platform == 'discord'
        assert identity.platform_user_id == discord_user_id
        assert identity.unified_user_id == f'auth:discord:{discord_user_id}'
        assert identity.user_type == 'authenticated'
    
    def test_rate_limit_key_generation(self):
        """Test rate limit key generation."""
        identity = UserIdentity(
            platform='discord',
            platform_user_id='123456789',
            unified_user_id='auth:discord:123456789',
            user_type='authenticated'
        )
        
        key = self.mapper.get_rate_limit_key(identity)
        assert key == 'auth:discord:123456789'
    
    def test_same_platform_different_users(self):
        """Test that different users on same platform get different identities."""
        # Two different Discord users
        identity1 = self.mapper.create_discord_user_identity('111111111')
        identity2 = self.mapper.create_discord_user_identity('222222222')
        
        assert identity1.unified_user_id != identity2.unified_user_id
        assert not self.mapper.can_share_rate_limit(identity1, identity2)
    
    def test_different_platforms_same_user_id(self):
        """Test that same user ID on different platforms get different identities."""
        # Same user ID on different platforms
        web_identity = self.mapper.create_web_user_identity({'X-User-ID': '123'}, {}, '1.1.1.1')
        discord_identity = self.mapper.create_discord_user_identity('123')
        
        assert web_identity.unified_user_id != discord_identity.unified_user_id
        assert not self.mapper.can_share_rate_limit(web_identity, discord_identity)


class TestCrossPlatformRateLimitingIntegration:
    """Integration tests for cross-platform rate limiting."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use in-memory Redis-like mock for testing
        self.mock_redis_data = {}
        
        # Mock Redis client
        self.mock_redis = Mock()
        self.mock_redis.get.side_effect = lambda key: self.mock_redis_data.get(key)
        self.mock_redis.setex.side_effect = lambda key, ttl, value: self.mock_redis_data.update({key: value})
        self.mock_redis.delete.side_effect = lambda key: 1 if self.mock_redis_data.pop(key, None) is not None else 0
        self.mock_redis.ping.return_value = True
        
        # Create rate limiter with mocked Redis
        config = RateLimitConfig(default_limit_seconds=60)
        self.rate_limiter = RateLimiter(config)
        self.rate_limiter._redis_client = self.mock_redis
        
        # Create Discord rate limiter with mocked dependencies
        with patch('discord_rate_limiter.get_rate_limiter', return_value=self.rate_limiter):
            self.discord_rate_limiter = DiscordRateLimiter()
    
    def test_discord_user_rate_limiting(self):
        """Test rate limiting for Discord users."""
        discord_user_id = '123456789012345678'
        
        # First request should be allowed
        result1 = self.discord_rate_limiter.check_rate_limit(discord_user_id)
        assert result1.allowed is True
        assert result1.remaining_seconds == 0
        
        # Second request should be rate limited
        result2 = self.discord_rate_limiter.check_rate_limit(discord_user_id)
        assert result2.allowed is False
        assert result2.remaining_seconds > 0
    
    def test_web_user_rate_limiting_simulation(self):
        """Test rate limiting for web users (simulated)."""
        # Simulate web user identification
        mapper = CrossPlatformUserMapper()
        web_identity = mapper.create_web_user_identity(
            {'X-User-ID': 'webuser123'}, {}, '192.168.1.1'
        )
        user_id = mapper.get_rate_limit_key(web_identity)
        
        # First request should be allowed
        result1 = self.rate_limiter.check_rate_limit(user_id)
        assert result1.allowed is True
        
        # Second request should be rate limited
        result2 = self.rate_limiter.check_rate_limit(user_id)
        assert result2.allowed is False
    
    def test_cross_platform_independence(self):
        """Test that different platforms don't interfere with each other."""
        # Same user ID on different platforms
        discord_user_id = '123456789'
        
        # Simulate web user with same ID
        mapper = CrossPlatformUserMapper()
        web_identity = mapper.create_web_user_identity(
            {'X-User-ID': discord_user_id}, {}, '192.168.1.1'
        )
        web_user_id = mapper.get_rate_limit_key(web_identity)
        
        # Rate limit Discord user
        discord_result1 = self.discord_rate_limiter.check_rate_limit(discord_user_id)
        assert discord_result1.allowed is True
        
        discord_result2 = self.discord_rate_limiter.check_rate_limit(discord_user_id)
        assert discord_result2.allowed is False
        
        # Web user with same ID should not be affected
        web_result1 = self.rate_limiter.check_rate_limit(web_user_id)
        assert web_result1.allowed is True  # Should be allowed despite Discord rate limit
        
        web_result2 = self.rate_limiter.check_rate_limit(web_user_id)
        assert web_result2.allowed is False  # Now web user is also rate limited
    
    def test_anonymous_web_users_by_ip(self):
        """Test rate limiting for anonymous web users by IP."""
        mapper = CrossPlatformUserMapper()
        
        # Two requests from same IP
        ip_address = '203.0.113.1'
        identity1 = mapper.create_web_user_identity({}, {}, ip_address)
        identity2 = mapper.create_web_user_identity({}, {}, ip_address)
        
        user_id1 = mapper.get_rate_limit_key(identity1)
        user_id2 = mapper.get_rate_limit_key(identity2)
        
        # Should be the same user ID (same IP)
        assert user_id1 == user_id2
        
        # First request allowed
        result1 = self.rate_limiter.check_rate_limit(user_id1)
        assert result1.allowed is True
        
        # Second request from same IP should be rate limited
        result2 = self.rate_limiter.check_rate_limit(user_id2)
        assert result2.allowed is False
    
    def test_different_anonymous_ips(self):
        """Test that different IP addresses get independent rate limits."""
        mapper = CrossPlatformUserMapper()
        
        # Two different IP addresses
        identity1 = mapper.create_web_user_identity({}, {}, '203.0.113.1')
        identity2 = mapper.create_web_user_identity({}, {}, '203.0.113.2')
        
        user_id1 = mapper.get_rate_limit_key(identity1)
        user_id2 = mapper.get_rate_limit_key(identity2)
        
        # Should be different user IDs
        assert user_id1 != user_id2
        
        # Rate limit first IP
        result1a = self.rate_limiter.check_rate_limit(user_id1)
        assert result1a.allowed is True
        
        result1b = self.rate_limiter.check_rate_limit(user_id1)
        assert result1b.allowed is False
        
        # Second IP should not be affected
        result2a = self.rate_limiter.check_rate_limit(user_id2)
        assert result2a.allowed is True
    
    def test_rate_limit_reset_cross_platform(self):
        """Test rate limit reset works across platforms."""
        discord_user_id = '123456789012345678'
        
        # Rate limit the user
        result1 = self.discord_rate_limiter.check_rate_limit(discord_user_id)
        assert result1.allowed is True
        
        result2 = self.discord_rate_limiter.check_rate_limit(discord_user_id)
        assert result2.allowed is False
        
        # Reset rate limit
        reset_success = self.discord_rate_limiter.reset_user_rate_limit(discord_user_id)
        assert reset_success is True
        
        # Should be allowed again
        result3 = self.discord_rate_limiter.check_rate_limit(discord_user_id)
        assert result3.allowed is True
    
    def test_rate_limit_status_check(self):
        """Test rate limit status checking."""
        discord_user_id = '123456789012345678'
        
        # No rate limit initially
        status1 = self.discord_rate_limiter.get_user_rate_limit_status(discord_user_id)
        assert status1 is None
        
        # Create rate limit
        self.discord_rate_limiter.check_rate_limit(discord_user_id)
        
        # Check status
        status2 = self.discord_rate_limiter.get_user_rate_limit_status(discord_user_id)
        assert status2 is not None
        assert status2.allowed is False
        assert status2.remaining_seconds > 0


class TestRateLimitMessageConsistency:
    """Test rate limit message consistency across platforms."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch('discord_rate_limiter.get_rate_limiter'):
            self.discord_rate_limiter = DiscordRateLimiter()
    
    def test_discord_rate_limit_message_format(self):
        """Test Discord rate limit message formatting."""
        remaining_seconds = 45
        username = "TestUser"
        
        message = self.discord_rate_limiter.create_rate_limit_message(remaining_seconds, username)
        
        # Should contain user-friendly elements
        assert username in message
        assert "45 seconds" in message
        assert any(emoji in message for emoji in ["⏰", "🚦", "⏳", "🕐"])
        assert "💡" in message
    
    def test_cross_platform_message_consistency(self):
        """Test that rate limit messages are consistent across platforms."""
        remaining_seconds = 30
        
        discord_message = self.discord_rate_limiter.create_rate_limit_message(remaining_seconds)
        cross_platform_message = self.discord_rate_limiter.create_cross_platform_message(remaining_seconds)
        
        # Both should mention the same time
        assert "30 seconds" in discord_message
        assert "30 seconds" in cross_platform_message
        
        # Cross-platform message should mention web interface
        assert "web interface" in cross_platform_message
        assert "shared between Discord" in cross_platform_message


if __name__ == "__main__":
    pytest.main([__file__])