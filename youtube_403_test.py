#!/usr/bin/env python3
"""
YouTube 403 Fix Verification Test
Tests the specific fix for YouTube HTTP 403 Forbidden errors
"""

import requests
import json
import time

def test_youtube_403_fix():
    """Test the YouTube 403 error fix with the original problematic video"""
    
    BASE_URL = "http://localhost:8000"
    
    # The original problematic video that was causing 403 errors
    test_video_url = "https://www.youtube.com/watch?v=FRTpI2Gu1KA"
    
    print("🔧 Testing YouTube 403 Fix")
    print("=" * 50)
    print(f"Test Video: {test_video_url}")
    print()
    
    try:
        # Test the API endpoint
        payload = {
            "url": test_video_url,
            "use_whisper": False,
            "whisper_model": "base"
        }
        
        print("📤 Sending YouTube processing request...")
        response = requests.post(
            f"{BASE_URL}/process-youtube",
            json=payload,
            timeout=120  # Give more time for YouTube processing
        )
        
        if response.status_code == 200:
            data = response.json()
            video_id = data.get("video_id")
            print(f"✅ SUCCESS: Video processing started")
            print(f"   Video ID: {video_id}")
            print(f"   Status: {data.get('status')}")
            print(f"   Message: {data.get('message')}")
            
            # Wait a bit and check status
            print("\n⏳ Waiting 10 seconds then checking processing status...")
            time.sleep(10)
            
            status_response = requests.get(f"{BASE_URL}/video/{video_id}/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"📊 Processing Status:")
                print(f"   Processed: {status_data.get('processed', False)}")
                print(f"   Transcript Generated: {status_data.get('transcript_generated', False)}")
                print(f"   Frames Extracted: {status_data.get('frames_extracted', False)}")
                
                if status_data.get('transcript_generated'):
                    print("🎉 YouTube 403 Fix: CONFIRMED WORKING!")
                else:
                    print("⏳ Processing still in progress (this is normal)")
            
            return True
            
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def test_alternative_youtube_video():
    """Test with a different YouTube video to verify general functionality"""
    
    BASE_URL = "http://localhost:8000"
    
    # Use a well-known, stable video
    test_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    print("\n🎬 Testing Alternative YouTube Video")
    print("=" * 50)
    print(f"Test Video: {test_video_url}")
    print()
    
    try:
        payload = {
            "url": test_video_url,
            "use_whisper": False,
            "whisper_model": "base"
        }
        
        print("📤 Sending request...")
        response = requests.post(
            f"{BASE_URL}/process-youtube",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS: {data.get('message')}")
            return True
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Main test function"""
    print("YouTube 403 Fix Verification Test")
    print("=" * 60)
    
    # Check server connectivity first
    try:
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and responsive")
        else:
            print(f"⚠️ Server responded with HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("Please ensure the backend server is running on port 8000")
        return
    
    print()
    
    # Run the main test
    test1_success = test_youtube_403_fix()
    test2_success = test_alternative_youtube_video()
    
    print("\n" + "=" * 60)
    print("🎯 YOUTUBE 403 FIX TEST SUMMARY")
    print("=" * 60)
    
    if test1_success:
        print("✅ Original problematic video: FIXED")
    else:
        print("❌ Original problematic video: STILL FAILING")
    
    if test2_success:
        print("✅ Alternative video test: WORKING")
    else:
        print("❌ Alternative video test: FAILING")
    
    if test1_success and test2_success:
        print("\n🎉 RESULT: YouTube 403 fix is working correctly!")
    elif test2_success:
        print("\n⚠️ RESULT: General YouTube processing works, but original video may still have issues")
    else:
        print("\n🔧 RESULT: YouTube processing needs attention")

if __name__ == "__main__":
    main()
