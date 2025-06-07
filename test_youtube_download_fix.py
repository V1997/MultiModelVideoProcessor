#!/usr/bin/env python3
"""
Test script to verify YouTube video processing with enhanced yt-dlp settings
"""

import yt_dlp
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_youtube_download_with_enhanced_settings(video_url: str):
    """Test YouTube download with enhanced settings to handle 403 errors"""
    
    # Extract video ID
    import re
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
        r'youtube\.com/watch\?.*v=([^&\n?#]+)'
    ]
    
    video_id = None
    for pattern in patterns:
        match = re.search(pattern, video_url)
        if match:
            video_id = match.group(1)
            break
    
    if not video_id:
        logger.error("Could not extract video ID from URL")
        return False
    
    logger.info(f"Testing download for video ID: {video_id}")
    
    # Create temp directory
    output_path = Path("./temp_test")
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Enhanced ydl_opts to handle YouTube restrictions
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best',
        'outtmpl': str(output_path / f"test_audio_{video_id}.%(ext)s"),
        'quiet': False,  # Enable output for debugging
        'no_warnings': False,
        # Anti-bot measures
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.youtube.com/',
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Accept-Encoding': 'gzip,deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        },
        # Additional reliability options
        'extractor_retries': 3,
        'socket_timeout': 30,
        'retries': 3,
        'fragment_retries': 3,
        'skip_unavailable_fragments': True,
    }
    
    try:
        logger.info("Attempting to extract video info...")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # First try to get info without downloading
            info = ydl.extract_info(video_url, download=False)
            
            logger.info(f"Video info extracted successfully:")
            logger.info(f"  Title: {info.get('title', 'Unknown')}")
            logger.info(f"  Duration: {info.get('duration', 0)} seconds")
            logger.info(f"  Uploader: {info.get('uploader', 'Unknown')}")
            
            # Check for age restrictions
            if info.get('age_limit', 0) > 0:
                logger.warning(f"Video has age restrictions: {info.get('age_limit')}")
            
            # Try to download (just for testing - we'll cancel it)
            logger.info("Attempting audio download...")
            try:
                # Set a smaller format for testing
                test_opts = ydl_opts.copy()
                test_opts['format'] = 'worst[ext=webm]/worst'  # Use smaller format for testing
                
                with yt_dlp.YoutubeDL(test_opts) as ydl_test:
                    ydl_test.download([video_url])
                
                logger.info("✅ Download successful!")
                
                # Check if file was created
                downloaded_files = list(output_path.glob(f"test_audio_{video_id}.*"))
                if downloaded_files:
                    logger.info(f"Downloaded file: {downloaded_files[0]}")
                    # Clean up
                    for file in downloaded_files:
                        os.remove(file)
                        logger.info(f"Cleaned up: {file}")
                
                return True
                
            except yt_dlp.DownloadError as e:
                if "403" in str(e) or "Forbidden" in str(e):
                    logger.warning("403 Forbidden error encountered - trying fallback...")
                    
                    # Try with even simpler format
                    fallback_opts = ydl_opts.copy()
                    fallback_opts['format'] = 'worst'
                    
                    with yt_dlp.YoutubeDL(fallback_opts) as ydl_fallback:
                        ydl_fallback.download([video_url])
                    
                    logger.info("✅ Fallback download successful!")
                    return True
                else:
                    raise
                    
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        return False
    
    finally:
        # Clean up temp directory
        if output_path.exists():
            import shutil
            shutil.rmtree(output_path, ignore_errors=True)

def main():
    """Test with the problematic video"""
    video_url = "https://www.youtube.com/watch?v=FRTpI2Gu1KA"
    
    logger.info("=== YouTube Download Test ===")
    logger.info(f"Testing URL: {video_url}")
    logger.info(f"yt-dlp version: {yt_dlp.version.__version__}")
    
    success = test_youtube_download_with_enhanced_settings(video_url)
    
    if success:
        logger.info("🎉 Test PASSED - YouTube processing should work!")
    else:
        logger.error("❌ Test FAILED - Additional fixes needed")
    
    return success

if __name__ == "__main__":
    main()
