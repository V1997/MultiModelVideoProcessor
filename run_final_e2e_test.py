#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing Suite for MultiModelVideo Application
This script tests all major components through automated API calls and WebSocket connections.
"""

import asyncio
import aiohttp
import websockets
import json
import time
from typing import Dict, List, Any
import traceback
import sys

class MultiModelVideoE2ETester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.websocket_url = "ws://localhost:8000/api/v1/websocket"
        self.test_results = {}
        self.failed_tests = []
        self.passed_tests = []

    async def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test results"""
        self.test_results[test_name] = {"status": status, "details": details}
        if status == "PASS":
            self.passed_tests.append(test_name)
            print(f"[PASS] {test_name}")
        else:
            self.failed_tests.append(test_name)
            print(f"[FAIL] {test_name}: {details}")
        
        if details:
            print(f"       Details: {details}")

    async def test_system_health(self):
        """Test basic system health"""
        print("\n=== SYSTEM HEALTH TESTS ===")
        
        async with aiohttp.ClientSession() as session:
            # Test health endpoint
            try:
                async with session.get(f"{self.base_url}/health") as response:
                    if response.status == 200:
                        await self.log_test("Health Check", "PASS")
                    else:
                        await self.log_test("Health Check", "FAIL", f"Status: {response.status}")
            except Exception as e:
                await self.log_test("Health Check", "FAIL", str(e))

            # Test Redis status
            try:
                async with session.get(f"{self.base_url}/redis/status") as response:
                    if response.status == 200:
                        data = await response.json()
                        await self.log_test("Redis Status", "PASS", f"Status: {data}")
                    else:
                        await self.log_test("Redis Status", "FAIL", f"Status: {response.status}")
            except Exception as e:
                await self.log_test("Redis Status", "FAIL", str(e))

    async def test_video_management(self):
        """Test video management endpoints"""
        print("\n=== VIDEO MANAGEMENT TESTS ===")
        
        async with aiohttp.ClientSession() as session:
            # Test video listing
            try:
                async with session.get(f"{self.base_url}/videos") as response:
                    if response.status == 200:
                        videos = await response.json()
                        await self.log_test("Video Listing", "PASS", f"Found {len(videos)} videos")
                    else:
                        await self.log_test("Video Listing", "FAIL", f"Status: {response.status}")
            except Exception as e:
                await self.log_test("Video Listing", "FAIL", str(e))

    async def test_chat_system(self):
        """Test chat and conversation endpoints"""
        print("\n=== CHAT SYSTEM TESTS ===")
        
        async with aiohttp.ClientSession() as session:
            # Test conversation listing
            try:
                async with session.get(f"{self.base_url}/api/v1/conversation/list") as response:
                    if response.status == 200:
                        conversations = await response.json()
                        await self.log_test("Conversation Listing", "PASS", f"Found {len(conversations)} conversations")
                    else:
                        await self.log_test("Conversation Listing", "FAIL", f"Status: {response.status}")
            except Exception as e:
                await self.log_test("Conversation Listing", "FAIL", str(e))

            # Test chat models
            try:
                async with session.get(f"{self.base_url}/api/v1/chat/models") as response:
                    if response.status == 200:
                        models = await response.json()
                        await self.log_test("Chat Models", "PASS", f"Available models: {len(models)}")
                    else:
                        await self.log_test("Chat Models", "FAIL", f"Status: {response.status}")
            except Exception as e:
                await self.log_test("Chat Models", "FAIL", str(e))

    async def test_youtube_integration(self):
        """Test YouTube integration"""
        print("\n=== YOUTUBE INTEGRATION TESTS ===")
        
        async with aiohttp.ClientSession() as session:
            # Test YouTube search
            try:
                search_params = {"query": "python tutorial", "max_results": 3}
                async with session.get(f"{self.base_url}/api/v1/youtube/search", params=search_params) as response:
                    if response.status == 200:
                        results = await response.json()
                        await self.log_test("YouTube Search", "PASS", f"Found {len(results)} results")
                    else:
                        await self.log_test("YouTube Search", "FAIL", f"Status: {response.status}")
            except Exception as e:
                await self.log_test("YouTube Search", "FAIL", str(e))

    async def test_content_analysis(self):
        """Test content analysis endpoints"""
        print("\n=== CONTENT ANALYSIS TESTS ===")
        
        async with aiohttp.ClientSession() as session:
            # Test content topics
            try:
                async with session.get(f"{self.base_url}/api/v1/content/topics") as response:
                    if response.status == 200:
                        topics = await response.json()
                        await self.log_test("Content Topics", "PASS", f"Found {len(topics)} topics")
                    else:
                        await self.log_test("Content Topics", "FAIL", f"Status: {response.status}")
            except Exception as e:
                await self.log_test("Content Topics", "FAIL", str(e))

    async def test_websocket_connection(self):
        """Test WebSocket functionality"""
        print("\n=== WEBSOCKET TESTS ===")
        
        try:
            # Test WebSocket connection
            async with websockets.connect(self.websocket_url) as websocket:
                await self.log_test("WebSocket Connection", "PASS", "Successfully connected")
                
                # Test sending a message
                test_message = {"type": "test", "data": "Hello WebSocket"}
                await websocket.send(json.dumps(test_message))
                
                # Wait for response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    await self.log_test("WebSocket Message", "PASS", f"Received: {response}")
                except asyncio.TimeoutError:
                    await self.log_test("WebSocket Message", "FAIL", "No response received within 5 seconds")
                    
        except Exception as e:
            await self.log_test("WebSocket Connection", "FAIL", str(e))

    async def test_embeddings_and_search(self):
        """Test embeddings and semantic search"""
        print("\n=== EMBEDDINGS & SEARCH TESTS ===")
        
        async with aiohttp.ClientSession() as session:
            # Test embeddings status
            try:
                async with session.get(f"{self.base_url}/api/v1/embeddings/status") as response:
                    if response.status == 200:
                        status = await response.json()
                        await self.log_test("Embeddings Status", "PASS", f"Status: {status}")
                    else:
                        await self.log_test("Embeddings Status", "FAIL", f"Status: {response.status}")
            except Exception as e:
                await self.log_test("Embeddings Status", "FAIL", str(e))

            # Test semantic search
            try:
                search_data = {"query": "machine learning", "limit": 5}
                async with session.post(f"{self.base_url}/api/v1/search/semantic", json=search_data) as response:
                    if response.status == 200:
                        results = await response.json()
                        await self.log_test("Semantic Search", "PASS", f"Found {len(results)} results")
                    else:
                        await self.log_test("Semantic Search", "FAIL", f"Status: {response.status}")
            except Exception as e:
                await self.log_test("Semantic Search", "FAIL", str(e))

    async def test_visual_analysis(self):
        """Test visual analysis endpoints"""
        print("\n=== VISUAL ANALYSIS TESTS ===")
        
        async with aiohttp.ClientSession() as session:
            # Test visual search capabilities
            try:
                async with session.get(f"{self.base_url}/api/v1/visual/models") as response:
                    if response.status == 200:
                        models = await response.json()
                        await self.log_test("Visual Models", "PASS", f"Available models: {len(models)}")
                    else:
                        await self.log_test("Visual Models", "FAIL", f"Status: {response.status}")
            except Exception as e:
                await self.log_test("Visual Models", "FAIL", str(e))

    async def run_all_tests(self):
        """Run comprehensive test suite"""
        print("=" * 60)
        print("MULTIMODELVIDEO COMPREHENSIVE E2E TEST SUITE")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all test categories
        await self.test_system_health()
        await self.test_video_management()
        await self.test_chat_system()
        await self.test_youtube_integration()
        await self.test_content_analysis()
        await self.test_embeddings_and_search()
        await self.test_visual_analysis()
        await self.test_websocket_connection()
        
        # Generate final report
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("FINAL TEST RESULTS")
        print("=" * 60)
        print(f"Total Tests Run: {len(self.test_results)}")
        print(f"Passed: {len(self.passed_tests)}")
        print(f"Failed: {len(self.failed_tests)}")
        print(f"Success Rate: {(len(self.passed_tests) / len(self.test_results)) * 100:.1f}%")
        print(f"Test Duration: {duration:.2f} seconds")
        
        if self.failed_tests:
            print(f"\nFailed Tests:")
            for test in self.failed_tests:
                details = self.test_results[test]["details"]
                print(f"  - {test}: {details}")
        
        print(f"\nPassed Tests:")
        for test in self.passed_tests:
            print(f"  - {test}")
        
        print("\n" + "=" * 60)
        
        # Return overall success status
        return len(self.failed_tests) == 0

async def main():
    """Main test execution"""
    tester = MultiModelVideoE2ETester()
    
    try:
        success = await tester.run_all_tests()
        
        if success:
            print("ALL TESTS PASSED! System is fully functional.")
            sys.exit(0)
        else:
            print("SOME TESTS FAILED! Please check the results above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nTest suite interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error during testing: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
