"""
API client for AskRacha communication.
Handles HTTP requests to the AskRacha RAG API with retry logic and error handling.
"""
import asyncio
import logging
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
import aiohttp
import json

logger = logging.getLogger(__name__)


@dataclass
class APIResponse:
    """Response from the AskRacha API."""
    success: bool
    answer: str
    sources: list
    response_time: float
    error_message: Optional[str] = None


class APIClient:
    """HTTP client for communicating with the AskRacha RAG API."""
    
    def __init__(self, api_url: str, timeout: int, retry_attempts: int, retry_delay: float):
        """Initialize the API client with configuration."""
        self.api_url = api_url.rstrip('/')  # Remove trailing slash
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self._session: Optional[aiohttp.ClientSession] = None
        logger.info(f"API client initialized for {api_url}")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with proper configuration."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                headers={'Content-Type': 'application/json'},
                connector=aiohttp.TCPConnector(limit=10)
            )
        return self._session
    
    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.debug("API client session closed")
    
    async def _make_request(self, endpoint: str, data: Dict[str, Any], timeout: Optional[int] = None) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic and error handling.
        
        Args:
            endpoint: API endpoint to call
            data: Request payload
            timeout: Optional timeout override
            
        Returns:
            Dict: API response data
            
        Raises:
            aiohttp.ClientError: For HTTP-related errors
            asyncio.TimeoutError: For timeout errors
            json.JSONDecodeError: For invalid JSON responses
        """
        session = await self._get_session()
        url = f"{self.api_url}{endpoint}"
        request_timeout = timeout or self.timeout
        
        for attempt in range(self.retry_attempts + 1):
            try:
                logger.debug(f"Making request to {url} (attempt {attempt + 1}/{self.retry_attempts + 1})")
                
                async with session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=request_timeout)) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        try:
                            return json.loads(response_text)
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON response from API: {e}")
                            raise
                    
                    # Handle specific HTTP error codes
                    if response.status == 404:
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message="API endpoint not found"
                        )
                    elif response.status == 429:
                        # Rate limited - wait longer before retry
                        retry_after = response.headers.get('Retry-After', str(self.retry_delay * 2))
                        wait_time = float(retry_after)
                        logger.warning(f"Rate limited by API, waiting {wait_time}s before retry")
                        await asyncio.sleep(wait_time)
                        continue
                    elif response.status >= 500:
                        # Server error - retry with exponential backoff
                        logger.warning(f"Server error {response.status}, will retry")
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=f"Server error: {response_text}"
                        )
                    else:
                        # Client error - don't retry
                        logger.error(f"Client error {response.status}: {response_text}")
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=response.status,
                            message=f"Client error: {response_text}"
                        )
            
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{self.retry_attempts + 1}): {e}")
                
                # Don't retry on the last attempt
                if attempt == self.retry_attempts:
                    raise
                
                # Exponential backoff
                wait_time = self.retry_delay * (2 ** attempt)
                logger.debug(f"Waiting {wait_time}s before retry")
                await asyncio.sleep(wait_time)
    
    async def query_rag(self, question: str) -> APIResponse:
        """
        Send question to RAG API and return response.
        
        Args:
            question: The question to send to the API
            
        Returns:
            APIResponse: The API response with answer and metadata
        """
        if not question or not question.strip():
            logger.warning("Empty question provided to query_rag")
            return APIResponse(
                success=False,
                answer="",
                sources=[],
                response_time=0.0,
                error_message="Empty question provided"
            )
        
        start_time = time.time()
        
        try:
            logger.info(f"Querying RAG API with question: {question[:100]}...")
            
            request_data = {"query": question.strip()}
            response_data = await self._make_request("/api/query", request_data)
            
            response_time = time.time() - start_time
            
            # Parse response according to expected format
            success = response_data.get("success", False)
            answer = response_data.get("answer", "")
            raw_sources = response_data.get("sources", [])
            
            # Filter out score from sources
            sources = []
            for source in raw_sources:
                if isinstance(source, dict):
                    # Create a new dict without the score field
                    filtered_source = {k: v for k, v in source.items() if k != 'score'}
                    sources.append(filtered_source)
                else:
                    # If source is not a dict, keep it as is
                    sources.append(source)
            
            if success and answer:
                logger.info(f"Successfully received answer from API (response time: {response_time:.2f}s)")
                return APIResponse(
                    success=True,
                    answer=answer,
                    sources=sources,
                    response_time=response_time
                )
            else:
                # Backend often returns 'message' on errors
                error_msg = response_data.get("error") or response_data.get("message", "API returned unsuccessful response")
                logger.warning(f"API returned unsuccessful response: {error_msg}")
                return APIResponse(
                    success=False,
                    answer="",
                    sources=[],
                    response_time=response_time,
                    error_message=error_msg
                )
        
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            logger.error(f"API request timed out after {response_time:.2f}s")
            return APIResponse(
                success=False,
                answer="",
                sources=[],
                response_time=response_time,
                error_message="Request timed out"
            )
        
        except aiohttp.ClientResponseError as e:
            response_time = time.time() - start_time
            logger.error(f"API request failed with status {e.status}: {e.message}")
            return APIResponse(
                success=False,
                answer="",
                sources=[],
                response_time=response_time,
                error_message=f"HTTP {e.status}: {e.message}"
            )
        
        except aiohttp.ClientError as e:
            response_time = time.time() - start_time
            logger.error(f"API request failed with client error: {e}")
            return APIResponse(
                success=False,
                answer="",
                sources=[],
                response_time=response_time,
                error_message=f"Connection error: {str(e)}"
            )
        
        except json.JSONDecodeError as e:
            response_time = time.time() - start_time
            logger.error(f"Failed to parse API response as JSON: {e}")
            return APIResponse(
                success=False,
                answer="",
                sources=[],
                response_time=response_time,
                error_message="Invalid response format"
            )
        
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Unexpected error during API request: {e}")
            return APIResponse(
                success=False,
                answer="",
                sources=[],
                response_time=response_time,
                error_message=f"Unexpected error: {str(e)}"
            )

    async def create_chat_session(self, metadata: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Create a new chat session and return its session_id, or None on failure."""
        try:
            payload = metadata or {}
            data = await self._make_request("/api/chat/session", payload, timeout=min(5, self.timeout))
            if data.get("success") and data.get("session_id"):
                return data["session_id"]
            logger.warning(f"Failed to create chat session: {data}")
            return None
        except Exception as e:
            logger.warning(f"Chat session creation failed: {e}")
            return None

    async def chat_query(self, session_id: str, question: str) -> APIResponse:
        """Send a contextual query to /api/chat/query and map response to APIResponse."""
        if not question or not question.strip():
            return APIResponse(False, "", [], 0.0, "Empty question provided")
        start_time = time.time()
        try:
            payload = {"session_id": session_id, "query": question.strip()}
            data = await self._make_request("/api/chat/query", payload)
            response_time = time.time() - start_time

            success = data.get("success", False)
            answer = data.get("response") or data.get("answer", "")
            raw_sources = data.get("source_nodes") or data.get("sources", [])
            sources: list = []
            for s in raw_sources or []:
                if isinstance(s, dict):
                    title = s.get("title") or s.get("node_title") or s.get("document_title") or "Untitled"
                    url = s.get("url") or s.get("link") or s.get("source_url") or ""
                    snippet = s.get("snippet") or s.get("text") or s.get("content") or ""
                    sources.append({"title": title, "url": url, "snippet": snippet})
                else:
                    sources.append(s)

            if success and answer:
                return APIResponse(True, answer, sources, response_time)

            error_msg = data.get("error") or data.get("message", "API returned unsuccessful response")
            return APIResponse(False, "", [], response_time, error_message=error_msg)

        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            return APIResponse(False, "", [], response_time, error_message="Request timed out")
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Unexpected error during chat_query: {e}")
            return APIResponse(False, "", [], response_time, error_message=f"Unexpected error: {e}")
    
    async def health_check(self) -> bool:
        """
        Check if the API is available.
        
        Returns:
            bool: True if API is healthy, False otherwise
        """
        try:
            logger.debug("Performing API health check")
            
            # Use a simple test query for health check (backend expects 'query')
            test_question = "health check"
            request_data = {"query": test_question}
            
            # Use shorter timeout for health check
            health_check_timeout = min(5, self.timeout)
            response_data = await self._make_request("/api/query", request_data, timeout=health_check_timeout)
            
            # Consider API healthy if it responds, regardless of the actual answer
            is_healthy = "success" in response_data or "answer" in response_data
            
            if is_healthy:
                logger.debug("API health check passed")
            else:
                logger.warning("API health check failed - unexpected response format")
            
            return is_healthy
        
        except asyncio.TimeoutError:
            logger.warning("API health check timed out")
            return False
        
        except aiohttp.ClientError as e:
            logger.warning(f"API health check failed with client error: {e}")
            return False
        
        except Exception as e:
            logger.warning(f"API health check failed with unexpected error: {e}")
            return False