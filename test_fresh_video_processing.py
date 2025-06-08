#!/usr/bin/env python3
"""
Test fresh video processing to validate video_id fix
"""
import requests
import json
import sys

def test_fresh_video_processing():
    """Test processing a fresh YouTube video"""
    
    # Test with a different video that likely hasn't been processed
    test_url = 'https://www.youtube.com/watch?v=jNQXAC9IVRw'
    processing_data = {
        'url': test_url,
        'use_whisper': False,
        'whisper_model': 'base'
    }
    
    print(f'🎯 Testing with fresh video: {test_url}')
    
    try:
        response = requests.post(
            'http://localhost:8000/process-youtube', 
            json=processing_data, 
            timeout=30
        )
        print(f'📡 Response Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            print(f'📊 Response Data: {json.dumps(data, indent=2)}')
            
            video_id = data.get('video_id')
            print(f'🆔 video_id: {video_id} (type: {type(video_id).__name__})')
            
            if video_id is not None and isinstance(video_id, int):
                print('✅ SUCCESS: video_id is properly returned as integer!')
                  # Test chat session creation with this video_id
                print('\n🗨️ Testing chat session creation...')
                
                chat_response = requests.post(
                    f'http://localhost:8000/api/v1/chat/sessions?video_id={video_id}&title=Test Session for Video {video_id}',
                    headers={'Content-Type': 'application/json'},
                    timeout=10
                )
                
                print(f'💬 Chat Session Status: {chat_response.status_code}')
                if chat_response.status_code == 200:
                    chat_result = chat_response.json()
                    print(f'💬 Chat Session Created: {json.dumps(chat_result, indent=2)}')
                    print('✅ COMPLETE SUCCESS: End-to-end workflow working!')
                else:
                    print(f'❌ Chat Session Failed: {chat_response.text[:200]}')
            else:
                print(f'❌ FAILED: video_id is {video_id} (should be integer)')
        else:
            print(f'❌ Processing Failed: {response.text[:300]}')
            
    except requests.exceptions.RequestException as e:
        print(f'❌ Request Error: {e}')
    except Exception as e:
        print(f'❌ Unexpected Error: {e}')

if __name__ == '__main__':
    print('=' * 60)
    print('🔍 FRESH VIDEO PROCESSING TEST')
    print('=' * 60)
    test_fresh_video_processing()
    print('=' * 60)
