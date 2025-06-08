#!/usr/bin/env python3
"""
Quick test with different video
"""

import requests
import json

# Test with a different video that likely hasn't been processed
test_url = 'https://www.youtube.com/watch?v=9bZkp7q19f0'
processing_data = {
    'url': test_url,
    'use_whisper': False,
    'whisper_model': 'base'
}

print('🔍 Testing with fresh video:', test_url)
response = requests.post('http://localhost:8000/process-youtube', json=processing_data, timeout=30)
print(f'📡 Response Status: {response.status_code}')

if response.status_code == 200:
    data = response.json()
    print(f'📦 Response Data: {json.dumps(data, indent=2)}')
    print(f'🎯 video_id: {data.get("video_id")} ({type(data.get("video_id")).__name__})')
    
    # Test if video_id is valid
    video_id = data.get("video_id")
    if isinstance(video_id, int) and video_id > 0:
        print(f'✅ SUCCESS: video_id = {video_id} is valid!')
    else:
        print(f'❌ FAIL: video_id = {video_id} is invalid!')
else:
    print(f'Response: {response.text[:300]}')
