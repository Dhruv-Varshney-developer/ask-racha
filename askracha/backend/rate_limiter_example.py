"""
Example usage of the RateLimiter class.
This demonstrates how to use the rate limiting functionality.
"""
import time
from rate_limiter import RateLimiter, RateLimitConfig, get_rate_limiter


def main():
    """Demonstrate rate limiter usage."""
    print("=== AskRacha Rate Limiter Demo ===\n")
    
    # Create a rate limiter with custom config for demo (5 second limit)
    config = RateLimitConfig(default_limit_seconds=5)
    rate_limiter = RateLimiter(config)
    
    # Test user
    user_id = "demo_user"
    
    print("1. First request (should be allowed):")
    result = rate_limiter.check_rate_limit(user_id)
    print(f"   Allowed: {result.allowed}")
    print(f"   User: {result.user_id}")
    print(f"   Reset time: {result.reset_time}")
    
    print("\n2. Immediate second request (should be denied):")
    result = rate_limiter.check_rate_limit(user_id)
    print(f"   Allowed: {result.allowed}")
    print(f"   Remaining seconds: {result.remaining_seconds}")
    
    print("\n3. Check status without affecting rate limit:")
    status = rate_limiter.get_user_rate_limit_status(user_id)
    if status:
        print(f"   User is rate limited for {status.remaining_seconds} more seconds")
    else:
        print("   User has no active rate limit")
    
    print("\n4. Reset user rate limit (admin function):")
    reset_success = rate_limiter.reset_user_rate_limit(user_id)
    print(f"   Reset successful: {reset_success}")
    
    print("\n5. Request after reset (should be allowed):")
    result = rate_limiter.check_rate_limit(user_id)
    print(f"   Allowed: {result.allowed}")
    
    print("\n6. Health check:")
    is_healthy = rate_limiter.health_check()
    print(f"   Redis connection healthy: {is_healthy}")
    
    print("\n7. Using global singleton:")
    global_limiter = get_rate_limiter()
    result = global_limiter.check_rate_limit("another_user")
    print(f"   Global limiter result: {result.allowed}")
    
    # Clean up
    rate_limiter.close()
    
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    main()