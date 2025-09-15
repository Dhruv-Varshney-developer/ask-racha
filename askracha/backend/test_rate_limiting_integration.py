"""
Integration test for rate limiting functionality.
"""
import json
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
from rate_limiter import RateLimitResult


def test_rate_limiting_integration():
    """Test rate limiting integration with the Flask app."""
    from app import app
    
    app.config['TESTING'] = True
    client = app.test_client()
    
    print("🧪 Testing rate limiting integration...")
    
    # Test 1: Health endpoint should not be rate limited
    print("1. Testing health endpoint (should not be rate limited)...")
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'healthy'
    assert 'X-RateLimit-Limit' not in response.headers
    print("   ✅ Health endpoint not rate limited")
    
    # Test 2: Mock the rate limiter for controlled testing
    print("2. Testing with mocked rate limiter...")
    
    with patch('rate_limiter.get_rate_limiter') as mock_get_rate_limiter:
        mock_rate_limiter = Mock()
        mock_get_rate_limiter.return_value = mock_rate_limiter
        
        # Allow the request for validation test
        mock_result_allow = RateLimitResult(
            allowed=True,
            remaining_seconds=0,
            reset_time=datetime.now() + timedelta(seconds=60),
            user_id='ip:127.0.0.1'
        )
        mock_rate_limiter.check_rate_limit.return_value = mock_result_allow
        
        # Test query endpoint validation
        response = client.post('/api/query', json={})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'No question provided' in data['message']
        print("   ✅ Query validation works")
    
        # Test rate limit exceeded
        print("3. Testing rate limiting behavior...")
        mock_result = RateLimitResult(
            allowed=False,
            remaining_seconds=30,
            reset_time=datetime.now() + timedelta(seconds=30),
            user_id='ip:127.0.0.1'
        )
        mock_rate_limiter.check_rate_limit.return_value = mock_result
        
        response = client.post('/api/query', json={'question': 'test question'})
        
        assert response.status_code == 429
        data = json.loads(response.data)
        assert data['error'] == 'Rate limit exceeded'
        assert data['retry_after'] == 30
        assert data['type'] == 'rate_limit'
        
        # Check rate limit headers
        assert response.headers['X-RateLimit-Limit'] == '1'
        assert response.headers['X-RateLimit-Remaining'] == '0'
        assert 'X-RateLimit-Reset' in response.headers
        assert response.headers['Retry-After'] == '30'
        
        print("   ✅ Rate limiting blocks requests correctly")
        print(f"   📊 Rate limit response: {data['message']}")
        print(f"   ⏰ Retry after: {data['retry_after']} seconds")
    
    print("\n🎉 All rate limiting integration tests passed!")
    return True


if __name__ == '__main__':
    test_rate_limiting_integration()