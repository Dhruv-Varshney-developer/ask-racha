"""
Unit tests for the Redis-based rate limiting service.
"""
import time
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import redis

from rate_limiter import RateLimiter, RateLimitConfig, RateLimitResult, get_rate_limiter


class TestRateLimitConfig(unittest.TestCase):
    """Test rate limit configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = RateLimitConfig()
        self.assertEqual(config.default_limit_seconds, 60)
        self.assertEqual(config.redis_host, "localhost")
        self.assertEqual(config.redis_port, 6379)
        self.assertEqual(config.redis_db, 0)
        self.assertIsNone(config.redis_password)
        self.assertEqual(config.redis_max_connections, 10)
        self.assertEqual(config.key_prefix, "askracha:ratelimit")
    
    @patch.dict('os.environ', {
        'RATE_LIMIT_SECONDS': '30',
        'REDIS_HOST': 'redis.example.com',
        'REDIS_PORT': '6380',
        'REDIS_DB': '1',
        'REDIS_PASSWORD': 'secret',
        'REDIS_MAX_CONNECTIONS': '20',
        'RATE_LIMIT_KEY_PREFIX': 'test:ratelimit'
    })
    def test_config_from_env(self):
        """Test configuration from environment variables."""
        config = RateLimitConfig.from_env()
        self.assertEqual(config.default_limit_seconds, 30)
        self.assertEqual(config.redis_host, 'redis.example.com')
        self.assertEqual(config.redis_port, 6380)
        self.assertEqual(config.redis_db, 1)
        self.assertEqual(config.redis_password, 'secret')
        self.assertEqual(config.redis_max_connections, 20)
        self.assertEqual(config.key_prefix, 'test:ratelimit')


class TestRateLimitResult(unittest.TestCase):
    """Test rate limit result data class."""
    
    def test_to_dict(self):
        """Test conversion to dictionary."""
        reset_time = datetime.now()
        result = RateLimitResult(
            allowed=False,
            remaining_seconds=45,
            reset_time=reset_time,
            user_id="test_user"
        )
        
        result_dict = result.to_dict()
        self.assertEqual(result_dict['allowed'], False)
        self.assertEqual(result_dict['remaining_seconds'], 45)
        self.assertEqual(result_dict['reset_time'], reset_time.isoformat())
        self.assertEqual(result_dict['user_id'], "test_user")


class TestRateLimiter(unittest.TestCase):
    """Test rate limiter functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config = RateLimitConfig(
            default_limit_seconds=60,
            redis_host="localhost",
            redis_port=6379,
            redis_db=0
        )
        self.rate_limiter = RateLimiter(self.config)
        
        # Mock Redis client
        self.mock_redis = Mock(spec=redis.Redis)
        self.rate_limiter._redis_client = self.mock_redis
    
    def test_get_rate_limit_key(self):
        """Test Redis key generation."""
        key = self.rate_limiter._get_rate_limit_key("user123")
        self.assertEqual(key, "askracha:ratelimit:user123")
        
        # Test key sanitization
        key = self.rate_limiter._get_rate_limit_key("user@example.com")
        self.assertEqual(key, "askracha:ratelimit:user@example.com")
        
        key = self.rate_limiter._get_rate_limit_key("user with spaces!")
        self.assertEqual(key, "askracha:ratelimit:user_with_spaces_")
    
    def test_check_rate_limit_first_request(self):
        """Test rate limit check for first request."""
        self.mock_redis.get.return_value = None
        self.mock_redis.setex.return_value = True
        
        with patch('time.time', return_value=1000.0):
            result = self.rate_limiter.check_rate_limit("user123")
        
        self.assertTrue(result.allowed)
        self.assertEqual(result.remaining_seconds, 0)
        self.assertEqual(result.user_id, "user123")
        self.mock_redis.setex.assert_called_once_with(
            "askracha:ratelimit:user123", 60, "1000.0"
        )
    
    def test_check_rate_limit_within_limit(self):
        """Test rate limit check when user is within rate limit."""
        # Simulate last request 30 seconds ago
        self.mock_redis.get.return_value = "970.0"  # 1000 - 30
        
        with patch('time.time', return_value=1000.0):
            result = self.rate_limiter.check_rate_limit("user123")
        
        self.assertFalse(result.allowed)
        self.assertEqual(result.remaining_seconds, 30)  # 60 - 30
        self.assertEqual(result.user_id, "user123")
        self.mock_redis.setex.assert_not_called()
    
    def test_check_rate_limit_expired(self):
        """Test rate limit check when rate limit has expired."""
        # Simulate last request 70 seconds ago
        self.mock_redis.get.return_value = "930.0"  # 1000 - 70
        self.mock_redis.setex.return_value = True
        
        with patch('time.time', return_value=1000.0):
            result = self.rate_limiter.check_rate_limit("user123")
        
        self.assertTrue(result.allowed)
        self.assertEqual(result.remaining_seconds, 0)
        self.assertEqual(result.user_id, "user123")
        self.mock_redis.setex.assert_called_once_with(
            "askracha:ratelimit:user123", 60, "1000.0"
        )
    
    def test_check_rate_limit_custom_duration(self):
        """Test rate limit check with custom duration."""
        self.mock_redis.get.return_value = None
        self.mock_redis.setex.return_value = True
        
        with patch('time.time', return_value=1000.0):
            result = self.rate_limiter.check_rate_limit("user123", limit_seconds=30)
        
        self.assertTrue(result.allowed)
        self.mock_redis.setex.assert_called_once_with(
            "askracha:ratelimit:user123", 30, "1000.0"
        )
    
    def test_check_rate_limit_empty_user_id(self):
        """Test rate limit check with empty user ID."""
        with self.assertRaises(ValueError):
            self.rate_limiter.check_rate_limit("")
    
    def test_check_rate_limit_redis_error(self):
        """Test rate limit check when Redis is unavailable."""
        self.mock_redis.get.side_effect = redis.RedisError("Connection failed")
        
        with patch('time.time', return_value=1000.0):
            result = self.rate_limiter.check_rate_limit("user123")
        
        # Should fail open (allow request)
        self.assertTrue(result.allowed)
        self.assertEqual(result.user_id, "user123")
    
    def test_reset_user_rate_limit(self):
        """Test resetting user rate limit."""
        self.mock_redis.delete.return_value = 1
        
        result = self.rate_limiter.reset_user_rate_limit("user123")
        
        self.assertTrue(result)
        self.mock_redis.delete.assert_called_once_with("askracha:ratelimit:user123")
    
    def test_reset_user_rate_limit_not_found(self):
        """Test resetting rate limit for user with no existing limit."""
        self.mock_redis.delete.return_value = 0
        
        result = self.rate_limiter.reset_user_rate_limit("user123")
        
        self.assertFalse(result)
    
    def test_reset_user_rate_limit_empty_user_id(self):
        """Test resetting rate limit with empty user ID."""
        result = self.rate_limiter.reset_user_rate_limit("")
        self.assertFalse(result)
    
    def test_get_user_rate_limit_status_no_limit(self):
        """Test getting rate limit status for user with no active limit."""
        self.mock_redis.get.return_value = None
        
        result = self.rate_limiter.get_user_rate_limit_status("user123")
        
        self.assertIsNone(result)
    
    def test_get_user_rate_limit_status_active_limit(self):
        """Test getting rate limit status for user with active limit."""
        self.mock_redis.get.return_value = "970.0"  # 30 seconds ago
        
        with patch('time.time', return_value=1000.0):
            result = self.rate_limiter.get_user_rate_limit_status("user123")
        
        self.assertIsNotNone(result)
        self.assertFalse(result.allowed)
        self.assertEqual(result.remaining_seconds, 30)
        self.assertEqual(result.user_id, "user123")
    
    def test_get_user_rate_limit_status_expired(self):
        """Test getting rate limit status for user with expired limit."""
        self.mock_redis.get.return_value = "930.0"  # 70 seconds ago
        
        with patch('time.time', return_value=1000.0):
            result = self.rate_limiter.get_user_rate_limit_status("user123")
        
        self.assertIsNone(result)
    
    def test_health_check_success(self):
        """Test successful health check."""
        self.mock_redis.ping.return_value = True
        
        result = self.rate_limiter.health_check()
        
        self.assertTrue(result)
        self.mock_redis.ping.assert_called_once()
    
    def test_health_check_failure(self):
        """Test failed health check."""
        self.mock_redis.ping.side_effect = redis.RedisError("Connection failed")
        
        result = self.rate_limiter.health_check()
        
        self.assertFalse(result)


class TestGlobalRateLimiter(unittest.TestCase):
    """Test global rate limiter singleton."""
    
    def test_get_rate_limiter_singleton(self):
        """Test that get_rate_limiter returns the same instance."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        
        self.assertIs(limiter1, limiter2)
        self.assertIsInstance(limiter1, RateLimiter)


if __name__ == '__main__':
    unittest.main()