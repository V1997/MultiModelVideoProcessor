#!/usr/bin/env python3
"""
WebSocket Integration Test
Tests the complete WebSocket functionality including:
- Connection/disconnection
- Chat session management
- Processing status broadcasts
- Visual analysis broadcasts
- Real-time updates
"""

import asyncio
import socketio
import requests
import json
import time
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketTester:
    def __init__(self, server_url="http://localhost:8000"):
        self.server_url = server_url
        self.sio = socketio.AsyncClient()
        self.events_received = []
        self.connected = False
        
        # Setup event handlers
        self._setup_event_handlers()
    
    def _setup_event_handlers(self):
        """Setup Socket.IO event handlers for testing"""
        
        @self.sio.event
        async def connect():
            logger.info("✅ Successfully connected to WebSocket server")
            self.connected = True
            
        @self.sio.event
        async def disconnect():
            logger.info("❌ Disconnected from WebSocket server")
            self.connected = False
            
        @self.sio.event
        async def connected(data):
            logger.info(f"📨 Received welcome message: {data}")
            self.events_received.append(("connected", data))
            
        @self.sio.event
        async def joined_chat_session(data):
            logger.info(f"🏠 Joined chat session: {data}")
            self.events_received.append(("joined_chat_session", data))
            
        @self.sio.event
        async def new_chat_message(data):
            logger.info(f"💬 New chat message: {data}")
            self.events_received.append(("new_chat_message", data))
            
        @self.sio.event
        async def processing_status(data):
            logger.info(f"⚙️ Processing status: {data}")
            self.events_received.append(("processing_status", data))
            
        @self.sio.event
        async def visual_analysis_result(data):
            logger.info(f"👁️ Visual analysis result: {data}")
            self.events_received.append(("visual_analysis_result", data))
            
        @self.sio.event
        async def content_analysis_update(data):
            logger.info(f"📊 Content analysis update: {data}")
            self.events_received.append(("content_analysis_update", data))
            
        @self.sio.event
        async def error(data):
            logger.error(f"❌ Error received: {data}")
            self.events_received.append(("error", data))
    
    async def connect_to_server(self):
        """Connect to the WebSocket server"""
        try:
            await self.sio.connect(
                self.server_url,
                auth={'user_id': 'test_user_123'},
                transports=['websocket']
            )
            await asyncio.sleep(1)  # Wait for connection to stabilize
            return True
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            return False
    
    async def test_chat_session_join(self):
        """Test joining a chat session"""
        logger.info("\n🧪 Testing chat session join...")
        
        test_session_id = "test_session_123"
        test_video_id = 1
        
        await self.sio.emit('join_chat_session', {
            'session_id': test_session_id,
            'video_id': test_video_id
        })
        
        await asyncio.sleep(2)  # Wait for response
        
        # Check if we received the join confirmation
        join_events = [event for event in self.events_received if event[0] == 'joined_chat_session']
        if join_events:
            logger.info("✅ Chat session join test passed")
            return True
        else:
            logger.error("❌ Chat session join test failed")
            return False
    
    async def test_processing_status_subscription(self):
        """Test subscribing to processing status updates"""
        logger.info("\n🧪 Testing processing status subscription...")
        
        test_video_id = 1
        
        await self.sio.emit('subscribe_processing_updates', {
            'video_id': test_video_id
        })
        
        await asyncio.sleep(1)
        logger.info("✅ Processing status subscription test completed")
        return True
    
    async def test_visual_analysis_subscription(self):
        """Test subscribing to visual analysis updates"""
        logger.info("\n🧪 Testing visual analysis subscription...")
        
        test_video_id = 1
        
        await self.sio.emit('subscribe_visual_analysis', {
            'video_id': test_video_id
        })
        
        await asyncio.sleep(1)
        logger.info("✅ Visual analysis subscription test completed")
        return True
    
    async def test_api_endpoints(self):
        """Test WebSocket-related API endpoints"""
        logger.info("\n🧪 Testing WebSocket API endpoints...")
        
        try:
            # Test connection count endpoint
            response = requests.get(f"{self.server_url}/api/v1/websocket/connections")
            if response.status_code == 200:
                connections = response.json()
                logger.info(f"✅ Connection count: {connections}")
            else:
                logger.error(f"❌ Connection count endpoint failed: {response.status_code}")
                return False
            
            # Test broadcasting processing status
            response = requests.post(
                f"{self.server_url}/api/v1/websocket/status",
                params={
                    "task_id": "test_task_123",
                    "status": "processing",
                    "progress": 50,
                    "message": "Test processing message"
                }
            )
            if response.status_code == 200:
                logger.info("✅ Processing status broadcast endpoint works")
            else:
                logger.error(f"❌ Processing status broadcast failed: {response.status_code}")
                return False
            
            # Test broadcasting visual analysis
            response = requests.post(
                f"{self.server_url}/api/v1/websocket/visual-analysis",
                params={"video_id": 1},
                json={
                    "frame_timestamp": 10.5,
                    "objects_detected": ["person", "chair"],
                    "confidence_scores": {"person": 0.95, "chair": 0.87}
                }
            )
            if response.status_code == 200:
                logger.info("✅ Visual analysis broadcast endpoint works")
            else:
                logger.error(f"❌ Visual analysis broadcast failed: {response.status_code}")
                return False
            
            await asyncio.sleep(2)  # Wait for broadcasts to be received
            return True
            
        except Exception as e:
            logger.error(f"❌ API endpoint test failed: {e}")
            return False
    
    async def test_disconnect_and_reconnect(self):
        """Test disconnection and reconnection"""
        logger.info("\n🧪 Testing disconnect and reconnect...")
        
        # Disconnect
        await self.sio.disconnect()
        await asyncio.sleep(1)
        
        if not self.connected:
            logger.info("✅ Disconnection successful")
        else:
            logger.error("❌ Disconnection failed")
            return False
        
        # Reconnect
        success = await self.connect_to_server()
        if success and self.connected:
            logger.info("✅ Reconnection successful")
            return True
        else:
            logger.error("❌ Reconnection failed")
            return False
    
    async def run_all_tests(self):
        """Run all WebSocket tests"""
        logger.info("🚀 Starting comprehensive WebSocket integration tests...\n")
        
        # Test connection
        if not await self.connect_to_server():
            logger.error("❌ Failed to connect to server. Is the server running?")
            return False
        
        tests = [
            ("Chat Session Join", self.test_chat_session_join),
            ("Processing Status Subscription", self.test_processing_status_subscription),
            ("Visual Analysis Subscription", self.test_visual_analysis_subscription),
            ("API Endpoints", self.test_api_endpoints),
            ("Disconnect and Reconnect", self.test_disconnect_and_reconnect),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = await test_func()
                results.append((test_name, result))
            except Exception as e:
                logger.error(f"❌ Test '{test_name}' failed with exception: {e}")
                results.append((test_name, False))
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("📊 WebSocket Integration Test Results:")
        logger.info("="*60)
        
        passed = 0
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} - {test_name}")
            if result:
                passed += 1
        
        logger.info(f"\nOverall: {passed}/{len(results)} tests passed")
        logger.info(f"Events received during testing: {len(self.events_received)}")
        
        if self.events_received:
            logger.info("\n📨 Events received:")
            for event_type, data in self.events_received:
                logger.info(f"  - {event_type}: {json.dumps(data, indent=2)}")
        
        # Clean up
        if self.connected:
            await self.sio.disconnect()
        
        return passed == len(results)

async def main():
    """Main test function"""
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code != 200:
            logger.error("❌ Server not responding. Please start the FastAPI server first.")
            return
    except Exception as e:
        logger.error(f"❌ Cannot connect to server: {e}")
        logger.error("Please make sure the FastAPI server is running on http://localhost:8000")
        return
    
    # Run tests
    tester = WebSocketTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("\n🎉 All WebSocket integration tests passed!")
    else:
        logger.info("\n⚠️ Some WebSocket integration tests failed. Check logs above.")

if __name__ == "__main__":
    asyncio.run(main())
