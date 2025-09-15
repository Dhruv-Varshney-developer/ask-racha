"""
Simple test to verify middleware functionality.
"""
import pytest
import json
from unittest.mock import Mock, patch
from flask import Flask, jsonify
from rate_limit_middleware import RateLimitMiddleware
from rate_limiter import RateLimitResult
from datetime import datetime, timedelta


def test_middleware_rate_limit_integration():
    """Test middleware integration with mocked rate limiter."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    # Create middleware instance
    middleware = RateLimitMiddleware()
    
    # Mock the rate limiter
    mock_rate_limiter = Mock()
    middleware.rate_limiter = mock_rate_limiter
    
    # Initialize middleware with app
    middleware.init_app(app)
    
    @app.route('/api/query', methods=['POST'])
    def query_documents():
        return jsonify({'success': True, 'message': 'Query processed'})
    
    client = app.test_client()
    
    # Test 1: Rate limit exceeded
    mock_result = RateLimitResult(
        allowed=False,
        remaining_seconds=45,
        reset_time=datetime.now() + timedelta(seconds=45),
        user_id='ip:127.0.0.1'
    )
    mock_rate_limiter.check_rate_limit.return_value = mock_result
    
    response = client.post('/api/query', json={'question': 'test question'})
    
    assert response.status_code == 429
    data = json.loads(response.data)
    assert data['error'] == 'Rate limit exceeded'
    assert data['retry_after'] == 45
    assert 'Please wait 45 seconds' in data['message']
    assert data['type'] == 'rate_limit'
    
    # Verify rate limit headers
    assert response.headers['X-RateLimit-Limit'] == '1'
    assert response.headers['X-RateLimit-Remaining'] == '0'
    assert 'X-RateLimit-Reset' in response.headers
    assert response.headers['Retry-After'] == '45'
    
    # Test 2: Request allowed
    mock_result = RateLimitResult(
        allowed=True,
        remaining_seconds=0,
        reset_time=datetime.now() + timedelta(seconds=60),
        user_id='ip:127.0.0.1'
    )
    mock_rate_limiter.check_rate_limit.return_value = mock_result
    
    response = client.post('/api/query', json={'question': 'test question'})
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['success'] is True
    
    # Verify rate limit headers are added
    assert response.headers['X-RateLimit-Limit'] == '1'
    assert response.headers['X-RateLimit-Remaining'] == '0'
    assert 'X-RateLimit-Reset' in response.headers
    
    print("✅ Middleware integration test passed!")


if __name__ == '__main__':
    test_middleware_rate_limit_integration()