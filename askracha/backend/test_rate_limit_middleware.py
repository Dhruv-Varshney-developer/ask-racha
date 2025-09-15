"""
Unit tests for Flask rate limiting middleware.
"""
import pytest
import time
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask, jsonify, g
from rate_limit_middleware import RateLimitMiddleware, rate_limit_required, create_rate_limit_middleware
from rate_limiter import RateLimitResult, RateLimitConfig
from datetime import datetime, timedelta


@pytest.fixture
def app():
    """Create Flask app for testing."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    
    # Initialize middleware
    middleware = RateLimitMiddleware(app)
    
    # Add test routes
    @app.route('/api/query', methods=['POST'])
    def query_documents():
        return jsonify({'success': True, 'message': 'Query processed'})
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy'})
    
    @app.route('/api/test-rate-limit', methods=['POST'])
    @rate_limit_required
    def test_rate_limit():
        return jsonify({'success': True, 'message': 'Rate limit test'})
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def middleware(app):
    """Create middleware instance."""
    return RateLimitMiddleware(app)


class TestRateLimitMiddleware:
    """Test cases for RateLimitMiddleware."""
    
    def test_init_without_app(self):
        """Test middleware initialization without Flask app."""
        middleware = RateLimitMiddleware()
        assert middleware.app is None
        assert middleware.rate_limiter is not None
        assert 'query_documents' in middleware.rate_limited_endpoints
    
    def test_init_with_app(self, app):
        """Test middleware initialization with Flask app."""
        middleware = RateLimitMiddleware(app)
        assert middleware.app == app
        assert middleware.rate_limiter is not None
    
    def test_factory_function(self, app):
        """Test factory function for creating middleware."""
        middleware = create_rate_limit_middleware(app)
        assert isinstance(middleware, RateLimitMiddleware)
        assert middleware.app == app
    
    def test_get_user_identifier_with_header(self, app, client):
        """Test user identification from X-User-ID header."""
        with app.test_request_context('/api/query', headers={'X-User-ID': 'test-user-123'}):
            middleware = RateLimitMiddleware()
            from flask import request
            user_id = middleware._get_user_identifier(request)
            assert user_id == 'user:test-user-123'
    
    def test_get_user_identifier_with_ip_fallback(self, app):
        """Test user identification fallback to IP address."""
        with app.test_request_context('/api/query', environ_base={'REMOTE_ADDR': '192.168.1.100'}):
            middleware = RateLimitMiddleware()
            from flask import request
            user_id = middleware._get_user_identifier(request)
            assert user_id == 'ip:192.168.1.100'
    
    def test_get_user_identifier_with_forwarded_ip(self, app):
        """Test user identification with X-Forwarded-For header."""
        headers = {'X-Forwarded-For': '203.0.113.1, 192.168.1.100'}
        with app.test_request_context('/api/query', headers=headers):
            middleware = RateLimitMiddleware()
            from flask import request
            user_id = middleware._get_user_identifier(request)
            assert user_id == 'ip:203.0.113.1'
    
    def test_should_rate_limit_endpoint(self, middleware):
        """Test endpoint rate limiting detection."""
        assert middleware._should_rate_limit_endpoint('query_documents') is True
        assert middleware._should_rate_limit_endpoint('health_check') is False
        assert middleware._should_rate_limit_endpoint(None) is False
        assert middleware._should_rate_limit_endpoint('unknown_endpoint') is False
    
    @patch('rate_limiter.get_rate_limiter')
    def test_successful_request_within_rate_limit(self, mock_get_rate_limiter, client):
        """Test successful request when within rate limit."""
        # Mock rate limiter to allow request
        mock_rate_limiter = Mock()
        mock_result = RateLimitResult(
            allowed=True,
            remaining_seconds=0,
            reset_time=datetime.now() + timedelta(seconds=60),
            user_id='ip:127.0.0.1'
        )
        mock_rate_limiter.check_rate_limit.return_value = mock_result
        mock_get_rate_limiter.return_value = mock_rate_limiter
        
        # Make request
        response = client.post('/api/query', json={'question': 'test question'})
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        
        # Verify rate limit headers
        assert 'X-RateLimit-Limit' in response.headers
        assert 'X-RateLimit-Remaining' in response.headers
        assert 'X-RateLimit-Reset' in response.headers
        
        # Verify rate limiter was called
        mock_rate_limiter.check_rate_limit.assert_called_once()
    
    def test_request_exceeds_rate_limit(self, client):
        """Test request that exceeds rate limit."""
        # Mock rate limiter to deny request
        mock_rate_limiter = Mock()
        mock_result = RateLimitResult(
            allowed=False,
            remaining_seconds=45,
            reset_time=datetime.now() + timedelta(seconds=45),
            user_id='ip:127.0.0.1'
        )
        mock_rate_limiter.check_rate_limit.return_value = mock_result
        
        # Patch the middleware's rate limiter directly
        with patch.object(client.application.before_request_funcs[None][0].__self__, 'rate_limiter', mock_rate_limiter):
            # Make request
            response = client.post('/api/query', json={'question': 'test question'})
            
            # Verify response
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
    
    def test_non_rate_limited_endpoint_not_affected(self, client):
        """Test that non-rate-limited endpoints are not affected."""
        response = client.get('/api/health')
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        
        # Verify no rate limit headers
        assert 'X-RateLimit-Limit' not in response.headers
    
    def test_options_request_not_rate_limited(self, client):
        """Test that OPTIONS requests (CORS preflight) are not rate limited."""
        response = client.options('/api/query')
        
        # Should not be rate limited regardless of rate limit status
        assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly handled
    
    @patch('rate_limiter.get_rate_limiter')
    def test_rate_limiter_exception_fails_open(self, mock_get_rate_limiter, client):
        """Test that rate limiter exceptions result in allowing the request."""
        # Mock rate limiter to raise exception
        mock_rate_limiter = Mock()
        mock_rate_limiter.check_rate_limit.side_effect = Exception("Redis connection failed")
        mock_get_rate_limiter.return_value = mock_rate_limiter
        
        # Make request
        response = client.post('/api/query', json={'question': 'test question'})
        
        # Should succeed despite rate limiter failure
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True


class TestRateLimitDecorator:
    """Test cases for rate_limit_required decorator."""
    
    @patch('rate_limiter.get_rate_limiter')
    def test_decorator_allows_request_within_limit(self, mock_get_rate_limiter, client):
        """Test decorator allows request when within rate limit."""
        # Mock rate limiter to allow request
        mock_rate_limiter = Mock()
        mock_result = RateLimitResult(
            allowed=True,
            remaining_seconds=0,
            reset_time=datetime.now() + timedelta(seconds=60),
            user_id='ip:127.0.0.1'
        )
        mock_rate_limiter.check_rate_limit.return_value = mock_result
        mock_get_rate_limiter.return_value = mock_rate_limiter
        
        # Make request to decorated endpoint
        response = client.post('/api/test-rate-limit', json={'test': 'data'})
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == 'Rate limit test'
        
        # Verify rate limit headers
        assert 'X-RateLimit-Limit' in response.headers
        assert 'X-RateLimit-Reset' in response.headers
    
    @patch('rate_limiter.get_rate_limiter')
    def test_decorator_blocks_request_over_limit(self, mock_get_rate_limiter, client):
        """Test decorator blocks request when over rate limit."""
        # Mock rate limiter to deny request
        mock_rate_limiter = Mock()
        mock_result = RateLimitResult(
            allowed=False,
            remaining_seconds=30,
            reset_time=datetime.now() + timedelta(seconds=30),
            user_id='ip:127.0.0.1'
        )
        mock_rate_limiter.check_rate_limit.return_value = mock_result
        mock_get_rate_limiter.return_value = mock_rate_limiter
        
        # Make request to decorated endpoint
        response = client.post('/api/test-rate-limit', json={'test': 'data'})
        
        # Verify response
        assert response.status_code == 429
        data = json.loads(response.data)
        assert data['error'] == 'Rate limit exceeded'
        assert data['retry_after'] == 30
        assert 'Please wait 30 seconds' in data['message']
    
    @patch('rate_limiter.get_rate_limiter')
    def test_decorator_fails_open_on_exception(self, mock_get_rate_limiter, client):
        """Test decorator fails open when rate limiter raises exception."""
        # Mock rate limiter to raise exception
        mock_rate_limiter = Mock()
        mock_rate_limiter.check_rate_limit.side_effect = Exception("Rate limiter error")
        mock_get_rate_limiter.return_value = mock_rate_limiter
        
        # Make request to decorated endpoint
        response = client.post('/api/test-rate-limit', json={'test': 'data'})
        
        # Should succeed despite rate limiter failure
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True


class TestMiddlewareIntegration:
    """Integration tests for middleware with Flask app."""
    
    def test_middleware_integration_with_real_app(self):
        """Test middleware integration with a real Flask app."""
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        # Add middleware
        middleware = RateLimitMiddleware(app)
        
        @app.route('/api/query', methods=['POST'])
        def query_documents():
            return jsonify({'success': True})
        
        client = app.test_client()
        
        # Verify middleware is properly integrated
        assert middleware.app == app
        
        # Test that before_request and after_request handlers are registered
        # This is implicit - if the middleware works, the handlers are registered
        with app.test_request_context('/api/query', method='POST'):
            assert middleware._should_rate_limit_endpoint('query_documents') is True
    
    def test_multiple_requests_same_user(self, app, client):
        """Test multiple requests from the same user."""
        # This test would require a real Redis instance or better mocking
        # For now, we'll test the logic flow
        with patch('rate_limiter.get_rate_limiter') as mock_get_rate_limiter:
            mock_rate_limiter = Mock()
            
            # First request - allowed
            mock_result1 = RateLimitResult(
                allowed=True,
                remaining_seconds=0,
                reset_time=datetime.now() + timedelta(seconds=60),
                user_id='ip:127.0.0.1'
            )
            
            # Second request - denied
            mock_result2 = RateLimitResult(
                allowed=False,
                remaining_seconds=55,
                reset_time=datetime.now() + timedelta(seconds=55),
                user_id='ip:127.0.0.1'
            )
            
            mock_rate_limiter.check_rate_limit.side_effect = [mock_result1, mock_result2]
            mock_get_rate_limiter.return_value = mock_rate_limiter
            
            # First request should succeed
            response1 = client.post('/api/query', json={'question': 'first question'})
            assert response1.status_code == 200
            
            # Second request should be rate limited
            response2 = client.post('/api/query', json={'question': 'second question'})
            assert response2.status_code == 429
            
            # Verify rate limiter was called twice
            assert mock_rate_limiter.check_rate_limit.call_count == 2


if __name__ == '__main__':
    pytest.main([__file__])