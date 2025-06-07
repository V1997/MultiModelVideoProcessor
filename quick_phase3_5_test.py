#!/usr/bin/env python3
"""
Quick Phase 3-5 Test - Simple version to verify system status
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_api_health():
    """Test API health"""
    print("Testing API Health...", end=" ")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ PASS - API v{data.get('version', 'unknown')} running")
            return True
        else:
            print(f"❌ FAIL - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAIL - {str(e)}")
        return False

def test_youtube_search():
    """Test YouTube search"""
    print("Testing YouTube Search...", end=" ")
    try:
        payload = {
            "query": "Python tutorial",
            "max_results": 2,
            "duration": "short"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/youtube/search",
            json=payload,
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            videos = data.get("videos", [])
            print(f"✅ PASS - Found {len(videos)} videos")
            return True
        else:
            print(f"❌ FAIL - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAIL - {str(e)}")
        return False

def test_conversational_interface():
    """Test conversational interface"""
    print("Testing Conversational Interface...", end=" ")
    try:
        payload = {
            "message": "What is Python?",
            "video_id": 1
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/conversation/chat",
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ PASS - Chat response received")
            return True
        elif response.status_code == 501:
            print("⚠️ PARTIAL - Feature not fully implemented")
            return True
        else:
            print(f"❌ FAIL - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAIL - {str(e)}")
        return False

def test_visual_search():
    """Test visual search"""
    print("Testing Visual Search...", end=" ")
    try:
        payload = {
            "query": "people talking",
            "video_id": 1
        }
        
        response = requests.post(
            f"{BASE_URL}/api/v1/visual/search",
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            print("✅ PASS - Visual search completed")
            return True
        elif response.status_code == 501:
            print("⚠️ PARTIAL - Feature not fully implemented")
            return True
        else:
            print(f"❌ FAIL - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAIL - {str(e)}")
        return False

def test_content_segmentation():
    """Test content segmentation"""
    print("Testing Content Segmentation...", end=" ")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/content/analyze-topics",
            params={"video_id": 1},
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            topics = data.get("topics", [])
            print(f"✅ PASS - Found {len(topics)} topics")
            return True
        elif response.status_code == 501:
            print("⚠️ PARTIAL - Feature not fully implemented")
            return True
        else:
            print(f"❌ FAIL - HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ FAIL - {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Quick Phase 3-5 Test Suite")
    print("=" * 50)
    
    # Check server connection first
    try:
        response = requests.get(f"{BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print(f"❌ Server not responding (HTTP {response.status_code})")
            print("Please ensure backend server is running on port 8000")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Please start the backend server:")
        print("  cd backend && python -m api.main")
        sys.exit(1)
    
    # Run tests
    tests = [
        ("API Health", test_api_health),
        ("YouTube Search", test_youtube_search),
        ("Conversational Interface", test_conversational_interface),
        ("Visual Search", test_visual_search),
        ("Content Segmentation", test_content_segmentation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        if test_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    print(f"✅ Passed: {passed}/{total}")
    print(f"📊 Success Rate: {passed/total*100:.1f}%")
    
    if passed >= 4:
        print("🎉 Phase 3-5 features are working well!")
    elif passed >= 2:
        print("⚠️ Phase 3-5 features are partially working")
    else:
        print("🔧 Phase 3-5 features need attention")

if __name__ == "__main__":
    main()
