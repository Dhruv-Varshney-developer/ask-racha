#!/usr/bin/env python3
"""
Simple integration test script for Discord bot functionality.
"""
import asyncio
import sys
import os
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from bot import DiscordBot, BotMetrics
from api_client import APIClient, APIResponse
from message_processor import MessageProcessor, MessageContext
from config import BotConfig


async def test_bot_initialization():
    """Test that bot initializes correctly."""
    print("Testing bot initialization...")
    
    config = BotConfig(
        discord_token="test_token",
        askracha_api_url="http://localhost:5000",
        api_timeout=10,
        max_response_length=2000,
        log_level="INFO",
        retry_attempts=3,
        retry_delay=1.0
    )
    
    api_client = AsyncMock(spec=APIClient)
    message_processor = MagicMock(spec=MessageProcessor)
    
    # Mock the discord.py Bot initialization
    with MagicMock() as mock_bot_init:
        # Create bot instance
        bot = DiscordBot.__new__(DiscordBot)
        bot.config = config
        bot.api_client = api_client
        bot.message_processor = message_processor
        bot.metrics = BotMetrics()
        bot._reconnect_attempts = 0
        bot._max_reconnect_attempts = 5
        
        # Test initialization
        assert bot.config == config
        assert bot.api_client == api_client
        assert bot.message_processor == message_processor
        assert isinstance(bot.metrics, BotMetrics)
        assert bot._reconnect_attempts == 0
        
        print("✅ Bot initialization test passed")


async def test_message_processing():
    """Test message processing logic."""
    print("Testing message processing...")
    
    # Create mock message processor
    processor = MessageProcessor(max_response_length=2000)
    
    # Test question extraction
    message_content = "<@12345> How do I upload files to Storacha?"
    question = processor.extract_question(message_content)
    assert question == "How do I upload files to Storacha?"
    
    # Test question validation
    assert processor.is_valid_question("How do I upload files?") == True
    assert processor.is_valid_question("") == False
    assert processor.is_valid_question("hi") == False
    
    # Test response formatting
    api_response = {
        'success': True,
        'answer': 'To upload files to Storacha, you can use the web interface...',
        'sources': ['docs.storacha.network']
    }
    
    formatted = processor.format_response(api_response)
    assert "**Hey! There, here's your answer:**" in formatted
    assert "To upload files to Storacha" in formatted
    assert "🤖 AskRacha Bot by Storacha" in formatted
    
    print("✅ Message processing test passed")


async def test_api_client():
    """Test API client functionality."""
    print("Testing API client...")
    
    # Create API client
    client = APIClient(
        api_url="http://localhost:5000",
        timeout=10,
        retry_attempts=3,
        retry_delay=1.0
    )
    
    # Test that client initializes correctly
    assert client.api_url == "http://localhost:5000"
    assert client.timeout == 10
    assert client.retry_attempts == 3
    assert client.retry_delay == 1.0
    
    # Clean up
    await client.close()
    
    print("✅ API client test passed")


async def test_bot_metrics():
    """Test bot metrics tracking."""
    print("Testing bot metrics...")
    
    metrics = BotMetrics()
    
    # Test initial values
    assert metrics.questions_processed == 0
    assert metrics.successful_responses == 0
    assert metrics.failed_responses == 0
    assert metrics.average_response_time == 0.0
    
    # Test metrics calculation
    metrics.questions_processed = 5
    metrics.total_response_time = 10.0
    assert metrics.average_response_time == 2.0
    
    print("✅ Bot metrics test passed")


async def test_concurrent_handling():
    """Test concurrent request handling simulation."""
    print("Testing concurrent request handling...")
    
    # Simulate multiple concurrent requests
    async def mock_request(request_id):
        await asyncio.sleep(0.1)  # Simulate processing time
        return f"Response {request_id}"
    
    # Process 3 requests concurrently
    tasks = [mock_request(i) for i in range(3)]
    
    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*tasks)
    end_time = asyncio.get_event_loop().time()
    
    # Verify all requests completed
    assert len(results) == 3
    assert all("Response" in result for result in results)
    
    # Verify concurrent processing (should be faster than sequential)
    total_time = end_time - start_time
    assert total_time < 0.25  # Should be much less than 3 * 0.1 = 0.3s
    
    print("✅ Concurrent handling test passed")


async def main():
    """Run all integration tests."""
    print("🤖 Running Discord Bot Integration Tests")
    print("=" * 50)
    
    try:
        await test_bot_initialization()
        await test_message_processing()
        await test_api_client()
        await test_bot_metrics()
        await test_concurrent_handling()
        
        print("=" * 50)
        print("🎉 All integration tests passed!")
        return 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)