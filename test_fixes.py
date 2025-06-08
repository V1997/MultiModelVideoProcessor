#!/usr/bin/env python3
"""
Quick test to validate the fixes we implemented
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_api_health():
    """Test API health"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ API Health: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ API Health Error: {e}")
        return False

def test_chat_session():
    """Test chat session creation"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/sessions?video_id=1&title=Quick%20Test", 
            timeout=5
        )
        print(f"✅ Chat Session: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Session ID: {data.get('session_id', 'N/A')[:8]}...")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Chat Session Error: {e}")
        return False

def test_youtube_duplicate():
    """Test YouTube duplicate handling"""
    try:
        response = requests.post(
            f"{BASE_URL}/process-youtube",
            json={
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", 
                "use_whisper": False
            },
            timeout=5
        )
        print(f"✅ YouTube Processing: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Status: {data.get('status', 'N/A')}")
            print(f"   Message: {data.get('message', 'N/A')}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ YouTube Processing Error: {e}")
        return False

def main():
    print("🧪 TESTING FIXES")
    print("=" * 50)
    
    results = []
    results.append(test_api_health())
    results.append(test_chat_session())
    results.append(test_youtube_duplicate())
    
    print("\n📊 RESULTS")
    print("=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        print("✅ Fixes are working correctly!")
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total})")
        print("❌ Some issues remain")
    
    return passed == total

if __name__ == "__main__":
    main()
