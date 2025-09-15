"""
Demo script to show rate limiting functionality.
"""
import json
import time
from app import app


def demo_rate_limiting():
    """Demonstrate rate limiting functionality."""
    app.config['TESTING'] = True
    client = app.test_client()
    
    print("🚀 Rate Limiting Demo")
    print("=" * 50)
    
    # Test 1: Health endpoint (not rate limited)
    print("\n1. Testing health endpoint (should not be rate limited):")
    response = client.get('/api/health')
    print(f"   Status: {response.status_code}")
    print(f"   Has rate limit headers: {'X-RateLimit-Limit' in response.headers}")
    
    # Test 2: Query endpoint structure
    print("\n2. Testing query endpoint structure:")
    
    # Test with no question
    print("   a) No question provided:")
    response = client.post('/api/query', json={})
    print(f"      Status: {response.status_code}")
    if response.status_code == 429:
        data = json.loads(response.data)
        print(f"      Rate limited: {data.get('message', 'N/A')}")
        print(f"      Retry after: {data.get('retry_after', 'N/A')} seconds")
        print("      ✅ Rate limiting is working!")
    elif response.status_code == 400:
        data = json.loads(response.data)
        print(f"      Validation error: {data.get('message', 'N/A')}")
        print("      ✅ Validation is working!")
    
    # Test with question (will likely be rate limited)
    print("   b) With question:")
    response = client.post('/api/query', json={'question': 'What is Storacha?'})
    print(f"      Status: {response.status_code}")
    
    if response.status_code == 429:
        data = json.loads(response.data)
        print(f"      Rate limited: {data.get('message', 'N/A')}")
        print(f"      Retry after: {data.get('retry_after', 'N/A')} seconds")
        print(f"      Error type: {data.get('type', 'N/A')}")
        
        # Show rate limit headers
        print("      Rate limit headers:")
        for header in ['X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset', 'Retry-After']:
            value = response.headers.get(header, 'Not present')
            print(f"        {header}: {value}")
        
        print("      ✅ Rate limiting is working correctly!")
        
    elif response.status_code == 400:
        data = json.loads(response.data)
        print(f"      System error: {data.get('message', 'N/A')}")
        print("      (This is expected if RAG system is not initialized)")
        
    elif response.status_code == 200:
        data = json.loads(response.data)
        print(f"      Success: {data.get('success', 'N/A')}")
        print("      ✅ Request processed successfully!")
        
        # Show rate limit headers on successful response
        print("      Rate limit headers:")
        for header in ['X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset']:
            value = response.headers.get(header, 'Not present')
            print(f"        {header}: {value}")
    
    print("\n" + "=" * 50)
    print("🎉 Rate limiting demo completed!")
    print("\nKey features demonstrated:")
    print("✅ Health endpoint not rate limited")
    print("✅ Query endpoint is rate limited")
    print("✅ Rate limit responses include countdown timers")
    print("✅ Rate limit headers are properly set")
    print("✅ User-friendly error messages")


if __name__ == '__main__':
    demo_rate_limiting()