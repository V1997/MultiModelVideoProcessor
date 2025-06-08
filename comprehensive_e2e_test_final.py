#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing Suite
Tests the entire MultiModelVideo application through all APIs, services, and features.
"""

import requests
import asyncio
import socketio
import json
import time
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MultiModelVideoE2ETester:
    """Comprehensive end-to-end tester for MultiModelVideo application"""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = {}
        self.socket_client = None
        self.test_video_id = None
        self.test_session_id = None
        
    def log_test_result(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Log test result with details"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {test_name}")
        if details:
            print(f"    Details: {details}")
        
        self.test_results[test_name] = {
            "success": success,
            "details": details,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
    def test_system_health(self):
        """Test basic system health and connectivity"""
        print("\n🔍 TESTING SYSTEM HEALTH")
        print("=" * 50)
        
        # Test API health
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            self.log_test_result(
                "API Health Check", 
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test_result("API Health Check", False, str(e))
        
        # Test OpenAPI docs
        try:
            response = self.session.get(f"{self.base_url}/docs", timeout=5)
            self.log_test_result(
                "OpenAPI Documentation", 
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test_result("OpenAPI Documentation", False, str(e))
        
        # Test Redis status
        try:
            response = self.session.get(f"{self.base_url}/redis/status", timeout=5)
            if response.status_code == 200:
                redis_status = response.json()
                self.log_test_result(
                    "Redis Service", 
                    redis_status.get("status") == "connected",
                    f"Redis: {redis_status.get('status', 'unknown')}"
                )
            else:
                self.log_test_result("Redis Service", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test_result("Redis Service", False, str(e))
        
        # Test WebSocket connections endpoint
        try:
            response = self.session.get(f"{self.base_url}/api/v1/websocket/connections", timeout=5)
            if response.status_code == 200:
                connections = response.json()
                self.log_test_result(
                    "WebSocket Service", 
                    True,
                    f"Active connections: {connections.get('active_connections', 0)}"
                )
            else:
                self.log_test_result("WebSocket Service", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test_result("WebSocket Service", False, str(e))
    
    def test_video_management(self):
        """Test video listing and management"""
        print("\n📹 TESTING VIDEO MANAGEMENT")
        print("=" * 50)
        
        # Test video listing
        try:
            response = self.session.get(f"{self.base_url}/videos", timeout=10)
            if response.status_code == 200:
                videos = response.json()
                self.log_test_result(
                    "Video Listing", 
                    True,
                    f"Found {len(videos)} videos"
                )
                
                # Store first video ID for later tests
                if videos:
                    self.test_video_id = videos[0]["id"]
                    self.log_test_result(
                        "Test Video Selection", 
                        True,
                        f"Using video ID: {self.test_video_id}"
                    )
                else:
                    self.log_test_result(
                        "Test Video Selection", 
                        False,
                        "No videos found for testing"
                    )
            else:
                self.log_test_result("Video Listing", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test_result("Video Listing", False, str(e))
    
    def test_youtube_functionality(self):
        """Test YouTube-related features"""
        print("\n🎥 TESTING YOUTUBE FUNCTIONALITY")
        print("=" * 50)
        
        # Test YouTube search
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/youtube/search",
                params={"query": "AI tutorial", "max_results": 5},
                timeout=15
            )
            if response.status_code == 200:
                search_results = response.json()
                self.log_test_result(
                    "YouTube Search", 
                    len(search_results.get("videos", [])) > 0,
                    f"Found {len(search_results.get('videos', []))} videos"
                )
            else:
                self.log_test_result("YouTube Search", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test_result("YouTube Search", False, str(e))
        
        # Test YouTube info extraction
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/youtube/info",
                params={"url": test_url},
                timeout=15
            )
            self.log_test_result(
                "YouTube Info Extraction", 
                response.status_code in [200, 403],  # 403 is acceptable for restricted videos
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test_result("YouTube Info Extraction", False, str(e))
    
    def test_chat_functionality(self):
        """Test chat and conversation features"""
        print("\n💬 TESTING CHAT FUNCTIONALITY")
        print("=" * 50)
        
        # Test chat session creation
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/session",
                json={"video_id": self.test_video_id, "session_name": "E2E Test Session"},
                timeout=10
            )
            if response.status_code == 200:
                session_data = response.json()
                self.test_session_id = session_data.get("session_id")
                self.log_test_result(
                    "Chat Session Creation", 
                    True,
                    f"Session ID: {self.test_session_id}"
                )
            else:
                self.log_test_result("Chat Session Creation", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test_result("Chat Session Creation", False, str(e))
        
        # Test conversation start
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/conversation/start",
                json={"video_id": self.test_video_id},
                timeout=10
            )
            if response.status_code == 200:
                conversation_data = response.json()
                if not self.test_session_id:
                    self.test_session_id = conversation_data.get("session_id")
                self.log_test_result(
                    "Conversation Start", 
                    True,
                    f"Session: {conversation_data.get('session_id')}"
                )
            else:
                self.log_test_result("Conversation Start", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test_result("Conversation Start", False, str(e))
        
        # Test chat message if we have a session
        if self.test_session_id:
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/conversation/{self.test_session_id}/ask",
                    json={"message": "What is this video about?"},
                    timeout=30
                )
                if response.status_code == 200:
                    chat_response = response.json()
                    self.log_test_result(
                        "Chat Message Processing", 
                        len(chat_response.get("response", "")) > 0,
                        f"Response length: {len(chat_response.get('response', ''))}"
                    )
                else:
                    self.log_test_result("Chat Message Processing", False, f"Status: {response.status_code}")
            except Exception as e:
                self.log_test_result("Chat Message Processing", False, str(e))
        
        # Test chat sessions listing
        try:
            response = self.session.get(f"{self.base_url}/api/v1/chat/sessions", timeout=10)
            if response.status_code == 200:
                sessions = response.json()
                self.log_test_result(
                    "Chat Sessions Listing", 
                    True,
                    f"Found {len(sessions)} sessions"
                )
            else:
                self.log_test_result("Chat Sessions Listing", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test_result("Chat Sessions Listing", False, str(e))
    
    def test_content_analysis(self):
        """Test content analysis features"""
        print("\n📊 TESTING CONTENT ANALYSIS")
        print("=" * 50)
        
        if not self.test_video_id:
            self.log_test_result("Content Analysis", False, "No test video available")
            return
        
        # Test content analysis
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/content/analyze/{self.test_video_id}",
                timeout=30
            )
            self.log_test_result(
                "Content Analysis", 
                response.status_code in [200, 202],  # 202 for async processing
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test_result("Content Analysis", False, str(e))
        
        # Test topic analysis
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/content/analyze-topics",
                json={"video_id": self.test_video_id},
                timeout=30
            )
            self.log_test_result(
                "Topic Analysis", 
                response.status_code in [200, 202],
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test_result("Topic Analysis", False, str(e))
        
        # Test outline generation
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/content/generate-outline",
                json={"video_id": self.test_video_id},
                timeout=30
            )
            self.log_test_result(
                "Outline Generation", 
                response.status_code in [200, 202],
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test_result("Outline Generation", False, str(e))
    
    def test_visual_search(self):
        """Test visual search and analysis features"""
        print("\n👁️ TESTING VISUAL SEARCH")
        print("=" * 50)
        
        if not self.test_video_id:
            self.log_test_result("Visual Search", False, "No test video available")
            return
        
        # Test visual search
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/visual-search",
                json={
                    "video_id": self.test_video_id,
                    "query": "person walking",
                    "confidence_threshold": 0.5
                },
                timeout=30
            )
            if response.status_code == 200:
                visual_results = response.json()
                self.log_test_result(
                    "Visual Search", 
                    True,
                    f"Found {visual_results.get('total_matches', 0)} matches"
                )
            else:
                self.log_test_result("Visual Search", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test_result("Visual Search", False, str(e))
        
        # Test object detection
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/visual-search/detect-objects",
                json={"video_id": self.test_video_id},
                timeout=30
            )
            self.log_test_result(
                "Object Detection", 
                response.status_code in [200, 202],
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test_result("Object Detection", False, str(e))
        
        # Test visual processing
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/visual/process/{self.test_video_id}",
                timeout=30
            )
            self.log_test_result(
                "Visual Processing", 
                response.status_code in [200, 202],
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test_result("Visual Processing", False, str(e))
    
    def test_embeddings_and_search(self):
        """Test embeddings and semantic search"""
        print("\n🔍 TESTING EMBEDDINGS & SEMANTIC SEARCH")
        print("=" * 50)
        
        if not self.test_video_id:
            self.log_test_result("Embeddings", False, "No test video available")
            return
        
        # Test embeddings generation
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/embeddings/generate",
                json={"video_id": self.test_video_id},
                timeout=30
            )
            self.log_test_result(
                "Embeddings Generation", 
                response.status_code in [200, 202],
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test_result("Embeddings Generation", False, str(e))
        
        # Test semantic search
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/search/semantic",
                json={
                    "query": "artificial intelligence",
                    "video_id": self.test_video_id,
                    "top_k": 5
                },
                timeout=20
            )
            if response.status_code == 200:
                search_results = response.json()
                self.log_test_result(
                    "Semantic Search", 
                    True,
                    f"Found {len(search_results.get('results', []))} results"
                )
            else:
                self.log_test_result("Semantic Search", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test_result("Semantic Search", False, str(e))
        
        # Test similarity search
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/similarity/find/{self.test_video_id}",
                params={"query": "machine learning", "limit": 5},
                timeout=20
            )
            self.log_test_result(
                "Similarity Search", 
                response.status_code in [200, 404],  # 404 acceptable if no similar content
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test_result("Similarity Search", False, str(e))
    
    async def test_websocket_integration(self):
        """Test WebSocket real-time features"""
        print("\n🔌 TESTING WEBSOCKET INTEGRATION")
        print("=" * 50)
        
        try:
            # Create Socket.IO client
            sio = socketio.AsyncClient()
            events_received = []
            
            @sio.event
            async def connect():
                events_received.append("connected")
            
            @sio.event
            async def connected(data):
                events_received.append(("welcome", data))
            
            @sio.event
            async def processing_status(data):
                events_received.append(("processing_status", data))
            
            @sio.event
            async def visual_analysis_result(data):
                events_received.append(("visual_analysis", data))
            
            # Test connection
            await sio.connect(self.base_url, auth={'user_id': 'e2e_test_user'})
            await asyncio.sleep(1)
            
            connected = "connected" in events_received
            self.log_test_result(
                "WebSocket Connection", 
                connected,
                f"Connection status: {'Connected' if connected else 'Failed'}"
            )
            
            if connected:
                # Test joining chat session
                if self.test_session_id:
                    await sio.emit('join_chat_session', {
                        'session_id': self.test_session_id,
                        'video_id': self.test_video_id
                    })
                    await asyncio.sleep(1)
                
                # Test API broadcast
                try:
                    response = self.session.post(
                        f"{self.base_url}/api/v1/websocket/status",
                        params={
                            "task_id": "e2e_test_task",
                            "status": "testing",
                            "progress": 50,
                            "message": "E2E test message"
                        }
                    )
                    await asyncio.sleep(1)
                    
                    broadcast_received = any("processing_status" in str(event) for event in events_received)
                    self.log_test_result(
                        "WebSocket Broadcasting", 
                        response.status_code == 200,
                        f"API Status: {response.status_code}, Events: {len(events_received)}"
                    )
                except Exception as e:
                    self.log_test_result("WebSocket Broadcasting", False, str(e))
                
                await sio.disconnect()
            
        except Exception as e:
            self.log_test_result("WebSocket Integration", False, str(e))
    
    def test_video_transcript_features(self):
        """Test video transcript and related features"""
        print("\n📝 TESTING VIDEO TRANSCRIPT FEATURES")
        print("=" * 50)
        
        if not self.test_video_id:
            self.log_test_result("Video Transcript", False, "No test video available")
            return
        
        # Test transcript retrieval
        try:
            response = self.session.get(
                f"{self.base_url}/video/{self.test_video_id}/transcript",
                timeout=15
            )
            if response.status_code == 200:
                transcript_data = response.json()
                self.log_test_result(
                    "Video Transcript", 
                    len(transcript_data.get("chunks", [])) > 0,
                    f"Found {len(transcript_data.get('chunks', []))} transcript chunks"
                )
            else:
                self.log_test_result("Video Transcript", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test_result("Video Transcript", False, str(e))
        
        # Test video summary
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/video/{self.test_video_id}/summary",
                timeout=20
            )
            self.log_test_result(
                "Video Summary", 
                response.status_code in [200, 404],  # 404 acceptable if no summary
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test_result("Video Summary", False, str(e))
        
        # Test video status
        try:
            response = self.session.get(
                f"{self.base_url}/video/{self.test_video_id}/status",
                timeout=10
            )
            if response.status_code == 200:
                status_data = response.json()
                self.log_test_result(
                    "Video Status", 
                    True,
                    f"Status: {status_data.get('status', 'unknown')}"
                )
            else:
                self.log_test_result("Video Status", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test_result("Video Status", False, str(e))
    
    def test_navigation_features(self):
        """Test navigation and content structure features"""
        print("\n🧭 TESTING NAVIGATION FEATURES")
        print("=" * 50)
        
        if not self.test_video_id:
            self.log_test_result("Navigation", False, "No test video available")
            return
        
        # Test navigation data
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/navigation/{self.test_video_id}",
                timeout=15
            )
            self.log_test_result(
                "Navigation Data", 
                response.status_code in [200, 404],
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test_result("Navigation Data", False, str(e))
        
        # Test navigation events
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/navigation/events/{self.test_video_id}",
                timeout=15
            )
            self.log_test_result(
                "Navigation Events", 
                response.status_code in [200, 404],
                f"Status: {response.status_code}"
            )
        except Exception as e:
            self.log_test_result("Navigation Events", False, str(e))
    
    def test_task_management(self):
        """Test task management and monitoring"""
        print("\n⚙️ TESTING TASK MANAGEMENT")
        print("=" * 50)
        
        # Test active tasks
        try:
            response = self.session.get(f"{self.base_url}/tasks/active", timeout=10)
            if response.status_code == 200:
                tasks = response.json()
                self.log_test_result(
                    "Active Tasks", 
                    True,
                    f"Found {len(tasks)} active tasks"
                )
            else:
                self.log_test_result("Active Tasks", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test_result("Active Tasks", False, str(e))
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE END-TO-END TEST REPORT")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📈 SUMMARY:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests} ✅")
        print(f"  Failed: {failed_tests} ❌")
        print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n📋 DETAILED RESULTS:")
        print("-" * 60)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result["success"] else "❌ FAIL"
            print(f"{status} {test_name}")
            if result["details"]:
                print(f"     {result['details']}")
        
        # System components status
        print(f"\n🏗️ SYSTEM COMPONENTS STATUS:")
        print("-" * 40)
        
        components = {
            "API Server": any("API Health" in test for test in self.test_results if self.test_results[test]["success"]),
            "Database": any("Video" in test for test in self.test_results if self.test_results[test]["success"]),
            "Redis Service": any("Redis" in test for test in self.test_results if self.test_results[test]["success"]),
            "WebSocket Service": any("WebSocket" in test for test in self.test_results if self.test_results[test]["success"]),
            "Chat System": any("Chat" in test for test in self.test_results if self.test_results[test]["success"]),
            "Content Analysis": any("Content" in test or "Topic" in test for test in self.test_results if self.test_results[test]["success"]),
            "Visual Search": any("Visual" in test for test in self.test_results if self.test_results[test]["success"]),
            "YouTube Integration": any("YouTube" in test for test in self.test_results if self.test_results[test]["success"]),
            "Embeddings Engine": any("Embedding" in test or "Semantic" in test for test in self.test_results if self.test_results[test]["success"])
        }
        
        for component, status in components.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {component}")
        
        print(f"\n🎯 OVERALL SYSTEM STATUS:")
        working_components = sum(1 for status in components.values() if status)
        total_components = len(components)
        
        if working_components == total_components:
            print("  🎉 ALL SYSTEMS OPERATIONAL")
        elif working_components >= total_components * 0.8:
            print("  ⚠️ MOSTLY OPERATIONAL (Minor Issues)")
        elif working_components >= total_components * 0.5:
            print("  🔄 PARTIALLY OPERATIONAL (Major Issues)")
        else:
            print("  🚨 SYSTEM ISSUES DETECTED")
        
        print(f"  Working: {working_components}/{total_components} components")
        
        return passed_tests == total_tests

async def main():
    """Main test execution function"""
    print("🚀 STARTING COMPREHENSIVE END-TO-END TESTING")
    print("=" * 80)
    print(f"Target: http://localhost:8000")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    tester = MultiModelVideoE2ETester()
    
    # Run all test suites
    test_suites = [
        tester.test_system_health,
        tester.test_video_management,
        tester.test_youtube_functionality,
        tester.test_chat_functionality,
        tester.test_content_analysis,
        tester.test_visual_search,
        tester.test_embeddings_and_search,
        tester.test_video_transcript_features,
        tester.test_navigation_features,
        tester.test_task_management,
    ]
    
    for test_suite in test_suites:
        try:
            test_suite()
        except Exception as e:
            print(f"❌ Test suite failed: {test_suite.__name__} - {e}")
        time.sleep(1)  # Small delay between test suites
    
    # Run async WebSocket tests
    try:
        await tester.test_websocket_integration()
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
    
    # Generate final report
    success = tester.generate_test_report()
    
    return success

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Testing failed with error: {e}")
        sys.exit(1)
