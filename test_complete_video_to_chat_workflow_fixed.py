#!/usr/bin/env python3
"""
Test complete video-to-chat workflow
Tests the full pipeline: video loading → chat session creation → video-to-chat flow
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any

# Configuration
API_BASE = "http://localhost:8000"

class VideoToChatWorkflowTester:
    def __init__(self):
        self.session = None
        self.available_videos = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def check_health(self) -> bool:
        """Check if the backend is healthy"""
        try:
            async with self.session.get(f"{API_BASE}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Backend healthy: {data['status']}")
                    return True
                return False
        except Exception as e:
            print(f"❌ Backend health check failed: {e}")
            return False
    
    async def load_videos(self) -> bool:
        """Load available videos"""
        try:
            async with self.session.get(f"{API_BASE}/videos") as response:
                if response.status == 200:
                    data = await response.json()
                    self.available_videos = data.get('videos', [])
                    processed_videos = [v for v in self.available_videos if v.get('processed', False)]
                    
                    print(f"📹 Found {len(self.available_videos)} total videos")
                    print(f"✅ {len(processed_videos)} processed videos available")
                    
                    if processed_videos:
                        print("\n📋 Processed Videos:")
                        for video in processed_videos:
                            duration = self.format_duration(video.get('duration', 0))
                            title = video.get('original_filename', video.get('filename', f"Video {video['id']}"))
                            print(f"  • ID {video['id']}: {title} ({duration})")
                    
                    return len(processed_videos) > 0
                return False
        except Exception as e:
            print(f"❌ Failed to load videos: {e}")
            return False
    
    async def test_video_metadata_access(self, video_id: int) -> Dict[str, Any]:
        """Test accessing video metadata (simulating loadVideo() function)"""
        print(f"\n🎬 Testing video metadata access for video {video_id}...")
        
        # Method 1: From loaded videos (simulating window.allVideos)
        video_data = None
        for video in self.available_videos:
            if video['id'] == video_id:
                video_data = video
                break
        
        if video_data:
            title = video_data.get('original_filename', video_data.get('filename', f"Video {video_id}"))
            duration = self.format_duration(video_data.get('duration', 0))
            processed = video_data.get('processed', False)
            
            print(f"✅ Video metadata found:")
            print(f"  • Title: {title}")
            print(f"  • Duration: {duration}")
            print(f"  • Processed: {processed}")
            
            return {
                'id': video_id,
                'title': title,
                'duration': video_data.get('duration', 0),
                'processed': processed
            }
        
        print(f"❌ No metadata found for video {video_id}")
        return None
    
    async def test_chat_session_creation(self, video_id: int) -> str:
        """Test creating a chat session for a video"""
        print(f"\n💬 Testing chat session creation for video {video_id}...")
        
        try:
            url = f"{API_BASE}/api/v1/chat/sessions"
            params = {
                'video_id': video_id,
                'title': 'Test Chat Session'
            }
            
            async with self.session.post(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    session_id = data.get('session_id')
                    print(f"✅ Chat session created: {session_id}")
                    return session_id
                else:
                    error_text = await response.text()
                    print(f"❌ Failed to create chat session: {response.status} - {error_text}")
                    return None
        except Exception as e:
            print(f"❌ Error creating chat session: {e}")
            return None
    
    async def test_chat_message(self, session_id: str, message: str) -> bool:
        """Test sending a message in the chat session"""
        print(f"\n📤 Testing chat message: '{message}'...")
        
        try:
            url = f"{API_BASE}/api/v1/chat/sessions/{session_id}/messages"
            payload = {'message': message}
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Chat response received:")
                    print(f"  • Response: {data.get('response', 'No response')[:100]}...")
                    
                    citations = data.get('timestamp_citations', [])
                    if citations:
                        print(f"  • Citations: {len(citations)} timestamp(s)")
                        for cite in citations[:3]:  # Show first 3
                            timestamp = self.format_duration(cite.get('timestamp', 0))
                            confidence = cite.get('confidence', 0)
                            print(f"    - {timestamp} (confidence: {confidence:.1%})")
                    
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Chat message failed: {response.status} - {error_text}")
                    return False
        except Exception as e:
            print(f"❌ Error sending chat message: {e}")
            return False
    
    def format_duration(self, seconds: float) -> str:
        """Format duration in seconds to human readable format"""
        if seconds == 0:
            return "0:00"
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    async def run_complete_workflow_test(self):
        """Run the complete video-to-chat workflow test"""
        print("🚀 Starting Complete Video-to-Chat Workflow Test")
        print("=" * 60)
        
        # Step 1: Health check
        if not await self.check_health():
            print("❌ Backend is not healthy. Cannot proceed.")
            return False
        
        # Step 2: Load videos
        if not await self.load_videos():
            print("❌ No processed videos available. Cannot proceed.")
            return False
        
        # Step 3: Select a processed video for testing
        processed_videos = [v for v in self.available_videos if v.get('processed', False)]
        test_video = processed_videos[0]  # Use first processed video
        video_id = test_video['id']
        
        print(f"\n🎯 Testing with video ID {video_id}")
        
        # Step 4: Test video metadata access (simulating loadVideo())
        video_metadata = await self.test_video_metadata_access(video_id)
        if not video_metadata:
            print("❌ Failed to access video metadata. Cannot proceed.")
            return False
        
        # Step 5: Test chat session creation
        session_id = await self.test_chat_session_creation(video_id)
        if not session_id:
            print("❌ Failed to create chat session. Cannot proceed.")
            return False
        
        # Step 6: Test chat messages
        test_messages = [
            "What is this video about?",
            "Can you summarize the main points?",
            "Show me key timestamps"
        ]
        
        all_messages_passed = True
        for message in test_messages:
            success = await self.test_chat_message(session_id, message)
            if not success:
                all_messages_passed = False
        
        # Final results
        print("\n" + "=" * 60)
        print("🏁 WORKFLOW TEST RESULTS")
        print("=" * 60)
        
        if all_messages_passed:
            print("✅ Complete video-to-chat workflow: SUCCESS")
            print("🎉 All components working correctly!")
            print(f"   • Video loading: ✅ Working ({video_metadata['title']})")
            print(f"   • Chat session: ✅ Working ({session_id})")
            print(f"   • Chat messages: ✅ Working ({len(test_messages)} tested)")
            return True
        else:
            print("❌ Complete video-to-chat workflow: PARTIAL FAILURE")
            print("⚠️ Some components need attention")
            return False

async def main():
    """Main test function"""
    async with VideoToChatWorkflowTester() as tester:
        success = await tester.run_complete_workflow_test()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
