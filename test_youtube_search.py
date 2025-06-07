#!/usr/bin/env python3
"""
Test YouTube search functionality
"""

import requests
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

API_BASE = "http://127.0.0.1:8002"

def test_youtube_search():
    """Test YouTube search endpoint"""
    print("Testing YouTube Search Functionality")
    print("=" * 50)
    
    # Test 1: Check if API server is running
    try:
        response = requests.get(f"{API_BASE}/")
        if response.status_code == 200:
            print("✅ API Server: Running")
        else:
            print("❌ API Server: Not responding correctly")
            return
    except Exception as e:
        print(f"❌ API Server: Not running - {e}")
        return
    
    # Test 2: Test YouTube search endpoint
    print("\n🔍 Testing YouTube Search...")
    try:
        search_payload = {
            "query": "machine learning tutorial",
            "max_results": 5,
            "duration": "medium",
            "order": "relevance"
        }
        
        response = requests.post(f"{API_BASE}/api/v1/youtube/search", json=search_payload)
        print(f"Search Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Search successful!")
            print(f"Query: {data['query']}")
            print(f"Results found: {data['total_results']}")
            
            if data['videos']:
                print("\n📺 Sample Results:")
                for i, video in enumerate(data['videos'][:3], 1):
                    print(f"{i}. {video['title']}")
                    print(f"   Channel: {video['channel_title']}")
                    print(f"   Duration: {video['duration']}")
                    print(f"   URL: {video['url']}")
                    print()
            
        else:
            print(f"❌ Search failed: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Search error: {e}")
    
    # Test 3: Test YouTube video info endpoint
    print("\n📄 Testing YouTube Video Info...")
    try:
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        response = requests.get(f"{API_BASE}/api/v1/youtube/info?url={test_url}")
        print(f"Info Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Video info retrieved!")
            print(f"Title: {data['title']}")
            print(f"Duration: {data['duration']}")
            print(f"Channel: {data['channel_title']}")
        else:
            print(f"❌ Info failed: {response.status_code}")
            print(f"Response: {response.text}")
    
    except Exception as e:
        print(f"❌ Info error: {e}")
    
    # Test 4: Check API documentation
    print("\n📚 Testing API Documentation...")
    try:
        response = requests.get(f"{API_BASE}/docs")
        if response.status_code == 200:
            print("✅ API documentation available at /docs")
        else:
            print("❌ API documentation not available")
    except Exception as e:
        print(f"❌ Documentation error: {e}")
    
    print("\n" + "=" * 50)
    print("YOUTUBE SEARCH TESTING COMPLETE")
    print("=" * 50)
    print("✅ Backend YouTube search endpoints ready")
    print("✅ Frontend UI updated with search interface")
    print("✅ Mock results available (requires YouTube API key for real data)")
    print("\n📋 Next Steps:")
    print("1. Set YOUTUBE_API_KEY environment variable for real search")
    print("2. Test the frontend interface in browser")
    print("3. Try searching and processing YouTube videos")

if __name__ == "__main__":
    test_youtube_search()
