"""
Flask middleware for rate limiting enforcement.
Integrates with the existing Flask application to provide transparent rate limiting.
"""
import logging
from functools import wraps
from typing import Optional, Dict, Any, Callable
from flask import Flask, request, jsonify, g, Response
from .rate_limiter import get_rate_limiter, RateLimitResult
from .cross_platform_user_mapper import get_user_mapper


# Configure logging
logger = logging.getLogger(__name__)


class RateLimitMiddleware:
    """Flask middleware for rate limiting enforcement."""
    
    def __init__(self, app: Optional[Flask] = None):
        """Initialize middleware with optional Flask app."""
        self.app = app
        self.rate_limiter = get_rate_limiter()
        self.user_mapper = get_user_mapper()
        self.rate_limited_endpoints = {
            'query_documents',
            'create_chat_session',
            'chat_query',
        }
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize middleware with Flask app."""
        self.app = app
        
        # Register before_request handler
        @app.before_request
        def before_request_handler():
            return self._before_request_handler()
        
        # Register after_request handler for rate limit headers
        @app.after_request
        def after_request_handler(response):
            return self._after_request_handler(response)
    
    def _get_user_identifier(self, request_obj) -> str:
        """
        Extract user identifier from Flask request using cross-platform mapping.
        """
        # Extract request data
        headers = dict(request_obj.headers)
        session_data = getattr(request_obj, 'session', {})
        remote_addr = request_obj.remote_addr or 'unknown'
        
        # Create user identity using cross-platform mapper
        identity = self.user_mapper.create_web_user_identity(
            headers, session_data, remote_addr
        )
        
        return self.user_mapper.get_rate_limit_key(identity)
    
    def _should_rate_limit_endpoint(self, endpoint: Optional[str]) -> bool:
        """Check if the current endpoint should be rate limited."""
        if not endpoint:
            return False
        return endpoint in self.rate_limited_endpoints
    
    def _create_rate_limit_response(self, result: RateLimitResult) -> Response:
        """Create JSON response for rate limit violations."""
        response_data = {
            'error': 'Rate limit exceeded',
            'message': f'Please wait {result.remaining_seconds} seconds before asking another question',
            'retry_after': result.remaining_seconds,
            'reset_time': result.reset_time.isoformat(),
            'type': 'rate_limit'
        }
        
        response = jsonify(response_data)
        response.status_code = 429
        
        # Add standard rate limit headers
        response.headers['X-RateLimit-Limit'] = '1'  # 1 request per period
        response.headers['X-RateLimit-Remaining'] = '0'
        response.headers['X-RateLimit-Reset'] = str(int(result.reset_time.timestamp()))
        response.headers['Retry-After'] = str(result.remaining_seconds)
        
        return response
    
    def _before_request_handler(self):
        """Handle rate limiting before each request."""
        # Skip rate limiting for non-rate-limited endpoints
        if not self._should_rate_limit_endpoint(request.endpoint):
            return None
        
        # Skip rate limiting for OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return None
        
        try:
            # Get user identifier
            user_id = self._get_user_identifier(request)
            
            # Check rate limit
            result = self.rate_limiter.check_rate_limit(user_id)
            
            # Store result in Flask's g object for use in after_request
            g.rate_limit_result = result
            g.rate_limit_user_id = user_id
            
            # If rate limited, return error response
            if not result.allowed:
                logger.info(f"Rate limit exceeded for user {user_id}, {result.remaining_seconds}s remaining")
                return self._create_rate_limit_response(result)
            
            logger.debug(f"Rate limit check passed for user {user_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error in rate limit middleware: {e}")
            # Fail open - allow request if rate limiting fails
            return None
    
    def _after_request_handler(self, response: Response) -> Response:
        """Add rate limit headers to successful responses."""
        try:
            # Only add headers for rate-limited endpoints
            if not self._should_rate_limit_endpoint(request.endpoint):
                return response
            
            # Get rate limit result from g object
            result = getattr(g, 'rate_limit_result', None)
            user_id = getattr(g, 'rate_limit_user_id', None)
            
            if result and user_id:
                # Add rate limit headers to successful responses
                response.headers['X-RateLimit-Limit'] = '1'  # 1 request per period
                
                if result.allowed:
                    # For successful requests, remaining is 0 until reset
                    response.headers['X-RateLimit-Remaining'] = '0'
                    response.headers['X-RateLimit-Reset'] = str(int(result.reset_time.timestamp()))
                else:
                    # This shouldn't happen for successful responses, but handle it
                    response.headers['X-RateLimit-Remaining'] = '0'
                    response.headers['X-RateLimit-Reset'] = str(int(result.reset_time.timestamp()))
            
            return response
            
        except Exception as e:
            logger.error(f"Error adding rate limit headers: {e}")
            return response


def rate_limit_required(f: Callable) -> Callable:
    """
    Decorator to enforce rate limiting on specific Flask routes.
    Alternative to middleware for more granular control.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        rate_limiter = get_rate_limiter()
        
        try:
            # Get user identifier using the same logic as middleware
            middleware = RateLimitMiddleware()
            user_id = middleware._get_user_identifier(request)
            
            # Check rate limit
            result = rate_limiter.check_rate_limit(user_id)
            
            if not result.allowed:
                logger.info(f"Rate limit exceeded for user {user_id}, {result.remaining_seconds}s remaining")
                response_data = {
                    'error': 'Rate limit exceeded',
                    'message': f'Please wait {result.remaining_seconds} seconds before asking another question',
                    'retry_after': result.remaining_seconds,
                    'reset_time': result.reset_time.isoformat(),
                    'type': 'rate_limit'
                }
                
                response = jsonify(response_data)
                response.status_code = 429
                response.headers['X-RateLimit-Limit'] = '1'
                response.headers['X-RateLimit-Remaining'] = '0'
                response.headers['X-RateLimit-Reset'] = str(int(result.reset_time.timestamp()))
                response.headers['Retry-After'] = str(result.remaining_seconds)
                
                return response
            
            # Store rate limit info for potential use in the route
            g.rate_limit_result = result
            g.rate_limit_user_id = user_id
            
            # Call the original function
            response = f(*args, **kwargs)
            
            # Add rate limit headers to successful responses
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = '1'
                response.headers['X-RateLimit-Remaining'] = '0'
                response.headers['X-RateLimit-Reset'] = str(int(result.reset_time.timestamp()))
            
            return response
            
        except Exception as e:
            logger.error(f"Error in rate limit decorator: {e}")
            # Fail open - allow request if rate limiting fails
            return f(*args, **kwargs)
    
    return decorated_function


def create_rate_limit_middleware(app: Flask) -> RateLimitMiddleware:
    """Factory function to create and initialize rate limit middleware."""
    return RateLimitMiddleware(app)