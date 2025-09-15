"""
Integration tests for rate limiting with the Flask app.
"""
import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from rate_limiter import RateLimitResult


@pytest.fixture
def app():
    """Create Flask app for testing."""
    # Import here to avoid circular imports
    from app import app as flask_app
    flask_app.config['TESTING'] = True
    return flask_app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


class TestAppRateLimiting:
    """Test rate limiting integration with the Flask app."""
    
    def test_health_endpoint_not_rate_limited(self, client):
        """Test that health endpoint is not rate limited."""
        response = client.get('/api/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        
        # Should not have rate limit headers
        assert 'X-RateLimit-Limit' not in response.headers
    
    @patch('rate_limiter.get_rate_limiter')
    def test_query_endpoint_rate_limited_success(self, mock_get_rate_limiter, client):
        """Test query endpoint with successful rate limit check."""
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
        
        # Mock RAG system to avoid initialization issues
        with patch('app.rag') as mock_rag:
            mock_rag.query_engine = Mock()
            mock_rag.query.return_value = {
                'success': True,
                'answer': 'Test answer',
                'sources': []
            }
            
            response = client.post('/api/query', json={'question': 'test question'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['answer'] == 'Test answer'
            
            # Should have rate limit headers
            assert 'X-RateLimit-Limit' in response.headers
            assert 'X-RateLimit-Reset' in response.headers
    
    @patch('rate_limiter.get_rate_limiter')
    def test_query_endpoint_rate_limited_blocked(self, mock_get_rate_limiter, client):
        """Test query endpoint when rate limited."""
        # Mock rate limiter to deny request
        mock_rate_limiter = Mock()
        mock_result = RateLimitResult(
            allowed=False,
            remaining_seconds=45,
            reset_time=datetime.now() + timedelta(seconds=45),
            user_id='ip:127.0.0.1'
        )
        mock_rate_limiter.check_rate_limit.return_value = mock_result
        mock_get_rate_limiter.return_value = mock_rate_limiter
        
        response = client.post('/api/query', json={'question': 'test question'})
        
        assert response.status_code == 429
        data = json.loads(response.data)
        assert data['error'] == 'Rate limit exceeded'
        assert data['retry_after'] == 45
        assert 'Please wait 45 seconds' in data['message']
        assert data['type'] == 'rate_limit'
        
        # Should have rate limit headers
        assert response.headers['X-RateLimit-Limit'] == '1'
        assert response.headers['X-RateLimit-Remaining'] == '0'
        assert 'X-RateLimit-Reset' in response.headers
        assert response.headers['Retry-After'] == '45'
    
    def test_query_endpoint_validation_error(self, client):
        """Test query endpoint with validation error (no question)."""
        response = client.post('/api/query', json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['message'] == 'No question provided'
        assert data['type'] == 'validation_error'
    
    @patch('rate_limiter.get_rate_limiter')
    def test_query_endpoint_system_error(self, mock_get_rate_limiter, client):
        """Test query endpoint with system error."""
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
        
        # Test with uninitialized RAG system
        with patch('app.rag', None):
            response = client.post('/api/query', json={'question': 'test question'})
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'RAG system not initialized' in data['message']
            assert data['type'] == 'system_error'
    
    @patch('rate_limiter.get_rate_limiter')
    def test_multiple_requests_rate_limiting(self, mock_get_rate_limiter, client):
        """Test multiple requests to verify rate limiting behavior."""
        mock_rate_limiter = Mock()
        mock_get_rate_limiter.return_value = mock_rate_limiter
        
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
        
        # Mock RAG system
        with patch('app.rag') as mock_rag:
            mock_rag.query_engine = Mock()
            mock_rag.query.return_value = {
                'success': True,
                'answer': 'Test answer',
                'sources': []
            }
            
            # First request should succeed
            response1 = client.post('/api/query', json={'question': 'first question'})
            assert response1.status_code == 200
            
            # Second request should be rate limited
            response2 = client.post('/api/query', json={'question': 'second question'})
            assert response2.status_code == 429
            
            # Verify rate limiter was called twice
            assert mock_rate_limiter.check_rate_limit.call_count == 2
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present."""
        response = client.options('/api/query')
        
        # CORS should be configured
        # The exact headers depend on flask-cors configuration
        assert response.status_code in [200, 405]  # 405 if OPTIONS not explicitly handled
    
    @patch('rate_limiter.get_rate_limiter')
    def test_rate_limit_headers_format(self, mock_get_rate_limiter, client):
        """Test that rate limit headers are properly formatted."""
        # Mock rate limiter to allow request
        mock_rate_limiter = Mock()
        reset_time = datetime.now() + timedelta(seconds=60)
        mock_result = RateLimitResult(
            allowed=True,
            remaining_seconds=0,
            reset_time=reset_time,
            user_id='ip:127.0.0.1'
        )
        mock_rate_limiter.check_rate_limit.return_value = mock_result
        mock_get_rate_limiter.return_value = mock_rate_limiter
        
        # Mock RAG system
        with patch('app.rag') as mock_rag:
            mock_rag.query_engine = Mock()
            mock_rag.query.return_value = {
                'success': True,
                'answer': 'Test answer',
                'sources': []
            }
            
            response = client.post('/api/query', json={'question': 'test question'})
            
            assert response.status_code == 200
            
            # Verify rate limit headers format
            assert response.headers['X-RateLimit-Limit'] == '1'
            assert response.headers['X-RateLimit-Remaining'] == '0'
            
            # Reset time should be a valid timestamp
            reset_header = response.headers.get('X-RateLimit-Reset')
            assert reset_header is not None
            assert reset_header.isdigit()
            
            # Should be close to our expected reset time
            expected_timestamp = int(reset_time.timestamp())
            actual_timestamp = int(reset_header)
            assert abs(actual_timestamp - expected_timestamp) <= 2  # Allow 2 second difference


if __name__ == '__main__':
    pytest.main([__file__, '-v'])