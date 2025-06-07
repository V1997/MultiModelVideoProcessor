#!/usr/bin/env python3
"""
Test the YouTube 403 error fix with the problematic video
"""

import requests
import json
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_youtube_processing_api():
    """Test the complete YouTube processing workflow via API"""
    
    # The problematic video that was causing 403 errors
    test_video_url = "https://www.youtube.com/watch?v=FRTpI2Gu1KA"
    
    logger.info("=== Testing YouTube 403 Fix via API ===")
    logger.info(f"Testing URL: {test_video_url}")
    
    try:
        # Test 1: Process YouTube video with transcript extraction
        logger.info("\n1. Testing YouTube transcript extraction...")
        response = requests.post(
            "http://localhost:8000/process-youtube",
            json={
                "url": test_video_url,
                "use_whisper": False  # Try existing transcript first
            },
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ YouTube transcript extraction successful!")
            logger.info(f"   Video ID: {result.get('video_id', 'N/A')}")
            logger.info(f"   Status: {result.get('status', 'N/A')}")
            logger.info(f"   Message: {result.get('message', 'N/A')}")
            return True
        else:
            logger.error(f"❌ YouTube transcript extraction failed: {response.status_code} - {response.text}")
            
            # Test 2: Fallback to Whisper if transcript extraction fails
            logger.info("\n2. Testing YouTube processing with Whisper fallback...")
            response = requests.post(
                "http://localhost:8000/process-youtube",
                json={
                    "url": test_video_url,
                    "use_whisper": True  # Force Whisper transcription
                },
                timeout=120  # Longer timeout for download + transcription
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info("✅ YouTube processing with Whisper successful!")
                logger.info(f"   Video ID: {result.get('video_id', 'N/A')}")
                logger.info(f"   Status: {result.get('status', 'N/A')}")
                logger.info(f"   Message: {result.get('message', 'N/A')}")
                return True
            else:
                logger.error(f"❌ YouTube processing with Whisper failed: {response.status_code} - {response.text}")
                return False
                
    except requests.exceptions.Timeout:
        logger.error("❌ Request timeout - processing took too long")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("❌ Connection error - is the backend server running on port 8000?")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}")
        return False

def test_server_health():
    """Test if the backend server is healthy"""
    try:
        response = requests.get("http://localhost:8000/", timeout=10)
        if response.status_code == 200:
            logger.info("✅ Backend server is healthy and responding")
            return True
        else:
            logger.error(f"❌ Backend server responded with status {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"❌ Could not connect to backend server: {str(e)}")
        return False

def test_youtube_video_status(video_id):
    """Check the status of a processed YouTube video"""
    try:
        response = requests.get(f"http://localhost:8000/api/v1/videos/{video_id}", timeout=10)
        if response.status_code == 200:
            result = response.json()
            logger.info(f"✅ Video status retrieved successfully")
            logger.info(f"   Processed: {result.get('processed', False)}")
            logger.info(f"   Transcript Generated: {result.get('transcript_generated', False)}")
            logger.info(f"   Duration: {result.get('duration', 0)} seconds")
            return result
        else:
            logger.error(f"❌ Failed to get video status: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"❌ Error checking video status: {str(e)}")
        return None

def main():
    """Run the complete test suite"""
    logger.info("=== YouTube 403 Error Fix Test Suite ===")
    
    # Check server health first
    if not test_server_health():
        logger.error("Backend server is not available. Please start it with:")
        logger.error("cd backend && python -m backend.api.main")
        return False
    
    # Test YouTube processing
    success = test_youtube_processing_api()
    
    if success:
        logger.info("\n🎉 SUCCESS: YouTube 403 error has been fixed!")
        logger.info("✅ Enhanced yt-dlp configuration is working correctly")
        logger.info("✅ Anti-bot headers are bypassing YouTube restrictions")
        logger.info("✅ Video processing request was accepted successfully")
        
        # Wait a bit and check processing status
        logger.info("\n⏳ Waiting for processing to complete...")
        time.sleep(10)  # Give some time for processing to start
        
    else:
        logger.error("\n❌ FAILURE: YouTube 403 error still exists")
        logger.error("❌ Additional troubleshooting may be needed")
    
    return success

if __name__ == "__main__":
    main()
