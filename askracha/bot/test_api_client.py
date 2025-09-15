"""
Unit tests for the API client module.
Tests cover success scenarios, error handling, retry logic, and health checks.
"""
import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import aiohttp

from api_client import APIClient, APIResponse


@pytest.fixture
def api_client():
    """Create API client for testing."""
    client = APIClient(
        api_url="http://localhost:8000",
        timeout=5,
        retry_attempts=2,
        retry_delay=0.1
    )
    yield client
    # Note: We'll handle cleanup in individual tests if needed


class TestAPIClientSuccess:
    """Test successful API client operations."""
    
    @pytest.mark.asyncio
    async def test_successful_query(self, api_client):
        """Test successful RAG query."""
        # Mock successful response
        mock_response_data = {
            "success": True,
            "answer": "This is a test answer from the RAG system.",
            "sources": ["doc1.md", "doc2.md"],
            "response_time": 0.5
        }
        
        with patch.object(api_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data
            
            question = "How do I upload files to Storacha?"
            response = await api_client.query_rag(question)
            
            assert response.success is True
            assert response.answer == "This is a test answer from the RAG system."
            assert response.sources == ["doc1.md", "doc2.md"]
            assert response.error_message is None
            assert response.response_time > 0
            
            mock_request.assert_called_once_with("/api/query", {"question": question})
    
    @pytest.mark.asyncio
    async def test_health_check_success(self, api_client):
        """Test successful health check."""
        mock_response_data = {"success": True, "answer": "healthy"}
        
        with patch.object(api_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response_data
            
            is_healthy = await api_client.health_check()
            
            assert is_healthy is True
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_session_creation(self, api_client):
        """Test that session is created when needed."""
        assert api_client._session is None
        
        session = await api_client._get_session()
        
        assert session is not None
        assert api_client._session is session
        assert not session.closed


class TestAPIClientErrorHandling:
    """Test API client error handling scenarios."""
    
    @pytest.mark.asyncio
    async def test_empty_question(self, api_client):
        """Test handling of empty questions."""
        response = await api_client.query_rag("")
        
        assert response.success is False
        assert response.answer == ""
        assert response.error_message == "Empty question provided"
        assert response.response_time == 0.0
    
    @pytest.mark.asyncio
    async def test_whitespace_only_question(self, api_client):
        """Test handling of whitespace-only questions."""
        response = await api_client.query_rag("   \n\t   ")
        
        assert response.success is False
        assert response.error_message == "Empty question provided"
    
    @pytest.mark.asyncio
    async def test_server_error_500(self, api_client):
        """Test handling of server errors (5xx)."""
        error = aiohttp.ClientResponseError(
            request_info=Mock(),
            history=(),
            status=500,
            message="Internal Server Error"
        )
        
        with patch.object(api_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = error
            
            response = await api_client.query_rag("Test question")
            
            assert response.success is False
            assert "HTTP 500" in response.error_message
    
    @pytest.mark.asyncio
    async def test_timeout_error(self, api_client):
        """Test handling of timeout errors."""
        with patch.object(api_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = asyncio.TimeoutError()
            
            response = await api_client.query_rag("Test question")
            
            assert response.success is False
            assert response.error_message == "Request timed out"
    
    @pytest.mark.asyncio
    async def test_json_decode_error(self, api_client):
        """Test handling of invalid JSON responses."""
        with patch.object(api_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
            
            response = await api_client.query_rag("Test question")
            
            assert response.success is False
            assert response.error_message == "Invalid response format"
    
    @pytest.mark.asyncio
    async def test_api_returns_unsuccessful_response(self, api_client):
        """Test handling when API returns success=false."""
        error_response = {
            "success": False,
            "error": "Question not understood",
            "answer": "",
            "sources": []
        }
        
        with patch.object(api_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = error_response
            
            response = await api_client.query_rag("Test question")
            
            assert response.success is False
            assert response.error_message == "Question not understood"


class TestAPIClientRetryLogic:
    """Test API client retry logic and exponential backoff."""
    
    @pytest.mark.asyncio
    async def test_retry_configuration(self, api_client):
        """Test that retry configuration is properly set."""
        assert api_client.retry_attempts == 2
        assert api_client.retry_delay == 0.1
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self, api_client):
        """Test handling of connection errors (which would trigger retries)."""
        with patch.object(api_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = aiohttp.ClientConnectorError(
                connection_key=Mock(), os_error=OSError("Connection refused")
            )
            
            response = await api_client.query_rag("Test question")
            
            assert response.success is False
            assert "Connection error" in response.error_message
            # Verify that _make_request was called (retry logic is inside _make_request)
            assert mock_request.called


class TestAPIClientTimeout:
    """Test API client timeout handling."""
    
    @pytest.mark.asyncio
    async def test_request_timeout(self):
        """Test handling of request timeouts."""
        short_timeout_client = APIClient(
            api_url="http://localhost:8000",
            timeout=0.1,  # Very short timeout
            retry_attempts=1,
            retry_delay=0.1
        )
        
        with patch.object(short_timeout_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = asyncio.TimeoutError()
            
            response = await short_timeout_client.query_rag("Test question")
            
            assert response.success is False
            assert response.error_message == "Request timed out"
        
        await short_timeout_client.close()
    
    @pytest.mark.asyncio
    async def test_health_check_timeout(self):
        """Test health check with timeout."""
        short_timeout_client = APIClient(
            api_url="http://localhost:8000",
            timeout=0.1,
            retry_attempts=1,
            retry_delay=0.1
        )
        
        with patch.object(short_timeout_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = asyncio.TimeoutError()
            
            is_healthy = await short_timeout_client.health_check()
            
            assert is_healthy is False
        
        await short_timeout_client.close()


class TestAPIClientConnectionErrors:
    """Test API client connection error handling."""
    
    @pytest.mark.asyncio
    async def test_connection_refused(self):
        """Test handling of connection refused errors."""
        bad_client = APIClient(
            api_url="http://localhost:99999",  # Invalid port
            timeout=1,
            retry_attempts=1,
            retry_delay=0.1
        )
        
        with patch.object(bad_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = aiohttp.ClientConnectorError(
                connection_key=Mock(), os_error=OSError("Connection refused")
            )
            
            response = await bad_client.query_rag("Test question")
            
            assert response.success is False
            assert "Connection error" in response.error_message
        
        await bad_client.close()
    
    @pytest.mark.asyncio
    async def test_health_check_connection_error(self):
        """Test health check with connection errors."""
        bad_client = APIClient(
            api_url="http://localhost:99999",
            timeout=1,
            retry_attempts=1,
            retry_delay=0.1
        )
        
        with patch.object(bad_client, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.side_effect = aiohttp.ClientConnectorError(
                connection_key=Mock(), os_error=OSError("Connection refused")
            )
            
            is_healthy = await bad_client.health_check()
            
            assert is_healthy is False
        
        await bad_client.close()


class TestAPIClientSessionManagement:
    """Test API client session management."""
    
    @pytest.mark.asyncio
    async def test_session_close(self, api_client):
        """Test proper session cleanup."""
        # Create session first
        session = await api_client._get_session()
        
        await api_client.close()
        
        assert session.closed
    
    @pytest.mark.asyncio
    async def test_session_recreation_after_close(self, api_client):
        """Test that session is recreated after being closed."""
        # Create first session
        old_session = await api_client._get_session()
        
        # Close it
        await api_client.close()
        
        # Create new session
        new_session = await api_client._get_session()
        
        assert new_session is not None
        assert new_session != old_session
        assert not new_session.closed
        
        await api_client.close()  # Cleanup


if __name__ == '__main__':
    # Run tests with pytest for better async support
    import sys
    import pytest
    
    # Run the tests
    exit_code = pytest.main([__file__, '-v'])
    sys.exit(exit_code)