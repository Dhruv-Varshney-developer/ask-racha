"""
Redis-based rate limiting service for AskRacha.
Provides per-user rate limiting with configurable parameters and cross-platform consistency.
"""
import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union
import re
import os
import redis
from redis.connection import ConnectionPool


# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting parameters."""
    default_limit_seconds: int = 60  # Default 60-second rate limit
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_max_connections: int = 10
    key_prefix: str = "askracha:ratelimit"
    redis_url: Optional[str] = None  # Support for Redis URL
    
    @classmethod
    def from_env(cls) -> 'RateLimitConfig':
        """Create configuration from environment variables."""
        # Check if REDIS_URL is provided (takes precedence)
        redis_url = os.getenv('REDIS_URL')
        
        if redis_url:
            # Use Redis URL if provided
            return cls(
                default_limit_seconds=int(os.getenv('RATE_LIMIT_SECONDS', '60')),
                redis_url=redis_url,
                redis_max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', '10')),
                key_prefix=os.getenv('RATE_LIMIT_KEY_PREFIX', 'askracha:ratelimit')
            )
        else:
            # Fall back to individual parameters
            return cls(
                default_limit_seconds=int(os.getenv('RATE_LIMIT_SECONDS', '60')),
                redis_host=os.getenv('REDIS_HOST', 'localhost'),
                redis_port=int(os.getenv('REDIS_PORT', '6379')),
                redis_db=int(os.getenv('REDIS_DB', '0')),
                redis_password=os.getenv('REDIS_PASSWORD'),
                redis_max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', '10')),
                key_prefix=os.getenv('RATE_LIMIT_KEY_PREFIX', 'askracha:ratelimit')
            )


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""
    allowed: bool
    remaining_seconds: int
    reset_time: datetime
    user_id: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'allowed': self.allowed,
            'remaining_seconds': self.remaining_seconds,
            'reset_time': self.reset_time.isoformat(),
            'user_id': self.user_id
        }


class RateLimiter:
    """Redis-based rate limiter with per-user tracking."""
    
    def __init__(self, config: Optional[RateLimitConfig] = None):
        """Initialize rate limiter with configuration."""
        self.config = config or RateLimitConfig.from_env()
        self._redis_pool: Optional[ConnectionPool] = None
        self._redis_client: Optional[redis.Redis] = None
        
    def _get_redis_client(self) -> redis.Redis:
        """Get Redis client with connection pooling."""
        if self._redis_client is None:
            if self._redis_pool is None:
                # Use Redis URL if provided, otherwise use individual parameters
                if self.config.redis_url:
                    self._redis_pool = ConnectionPool.from_url(
                        self.config.redis_url,
                        max_connections=self.config.redis_max_connections,
                        decode_responses=True
                    )
                else:
                    self._redis_pool = ConnectionPool(
                        host=self.config.redis_host,
                        port=self.config.redis_port,
                        db=self.config.redis_db,
                        password=self.config.redis_password,
                        max_connections=self.config.redis_max_connections,
                        decode_responses=True
                    )
            self._redis_client = redis.Redis(connection_pool=self._redis_pool)
        return self._redis_client
    
    def _get_rate_limit_key(self, user_id: str) -> str:
        """Generate Redis key for user rate limit."""
        # Sanitize user_id to prevent Redis key injection
        sanitized_user_id = re.sub(r'[^a-zA-Z0-9_\-@.]', '_', user_id)
        return f"{self.config.key_prefix}:{sanitized_user_id}"
    
    def check_rate_limit(self, user_id: str, limit_seconds: Optional[int] = None) -> RateLimitResult:
        """
        Check if user is within rate limit.
        
        Args:
            user_id: Unique identifier for the user
            limit_seconds: Custom rate limit duration (uses default if None)
            
        Returns:
            RateLimitResult with rate limit status and timing information
        """
        if not user_id:
            raise ValueError("user_id cannot be empty")
            
        limit_seconds = limit_seconds or self.config.default_limit_seconds
        redis_client = self._get_redis_client()
        key = self._get_rate_limit_key(user_id)
        
        try:
            # Get current timestamp
            current_time = time.time()
            
            # Check if user has an existing rate limit entry
            last_request_time = redis_client.get(key)
            
            if last_request_time is None:
                # No previous request, allow and set timestamp
                redis_client.setex(key, limit_seconds, str(current_time))
                reset_time = datetime.fromtimestamp(current_time + limit_seconds)
                return RateLimitResult(
                    allowed=True,
                    remaining_seconds=0,
                    reset_time=reset_time,
                    user_id=user_id
                )
            
            # Calculate time since last request
            last_time = float(last_request_time)
            time_elapsed = current_time - last_time
            
            if time_elapsed >= limit_seconds:
                # Rate limit period has passed, allow and update timestamp
                redis_client.setex(key, limit_seconds, str(current_time))
                reset_time = datetime.fromtimestamp(current_time + limit_seconds)
                return RateLimitResult(
                    allowed=True,
                    remaining_seconds=0,
                    reset_time=reset_time,
                    user_id=user_id
                )
            else:
                # Still within rate limit period, deny request
                remaining_seconds = int(limit_seconds - time_elapsed)
                reset_time = datetime.fromtimestamp(last_time + limit_seconds)
                return RateLimitResult(
                    allowed=False,
                    remaining_seconds=remaining_seconds,
                    reset_time=reset_time,
                    user_id=user_id
                )
                
        except redis.RedisError as e:
            logger.error(f"Redis error in rate limiting for user {user_id}: {e}")
            # Fail open - allow request if Redis is unavailable
            return RateLimitResult(
                allowed=True,
                remaining_seconds=0,
                reset_time=datetime.now() + timedelta(seconds=limit_seconds),
                user_id=user_id
            )
        except Exception as e:
            logger.error(f"Unexpected error in rate limiting for user {user_id}: {e}")
            # Fail open - allow request on unexpected errors
            return RateLimitResult(
                allowed=True,
                remaining_seconds=0,
                reset_time=datetime.now() + timedelta(seconds=limit_seconds),
                user_id=user_id
            )
    
    def reset_user_rate_limit(self, user_id: str) -> bool:
        """
        Reset rate limit for a specific user (admin function).
        
        Args:
            user_id: User identifier to reset
            
        Returns:
            True if reset successful, False otherwise
        """
        if not user_id:
            return False
            
        try:
            redis_client = self._get_redis_client()
            key = self._get_rate_limit_key(user_id)
            result = redis_client.delete(key)
            logger.info(f"Rate limit reset for user {user_id}")
            return result > 0
        except redis.RedisError as e:
            logger.error(f"Redis error resetting rate limit for user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error resetting rate limit for user {user_id}: {e}")
            return False
    
    def get_user_rate_limit_status(self, user_id: str) -> Optional[RateLimitResult]:
        """
        Get current rate limit status for a user without affecting the limit.
        
        Args:
            user_id: User identifier to check
            
        Returns:
            RateLimitResult if user has active rate limit, None otherwise
        """
        if not user_id:
            return None
            
        try:
            redis_client = self._get_redis_client()
            key = self._get_rate_limit_key(user_id)
            
            last_request_time = redis_client.get(key)
            if last_request_time is None:
                return None
                
            current_time = time.time()
            last_time = float(last_request_time)
            time_elapsed = current_time - last_time
            
            if time_elapsed >= self.config.default_limit_seconds:
                return None
                
            remaining_seconds = int(self.config.default_limit_seconds - time_elapsed)
            reset_time = datetime.fromtimestamp(last_time + self.config.default_limit_seconds)
            
            return RateLimitResult(
                allowed=False,
                remaining_seconds=remaining_seconds,
                reset_time=reset_time,
                user_id=user_id
            )
            
        except redis.RedisError as e:
            logger.error(f"Redis error checking rate limit status for user {user_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error checking rate limit status for user {user_id}: {e}")
            return None
    
    def health_check(self) -> bool:
        """
        Check if Redis connection is healthy.
        
        Returns:
            True if Redis is accessible, False otherwise
        """
        try:
            redis_client = self._get_redis_client()
            redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    def close(self):
        """Close Redis connections."""
        if self._redis_client:
            self._redis_client.close()
        if self._redis_pool:
            self._redis_pool.disconnect()


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get global rate limiter instance (singleton pattern)."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter