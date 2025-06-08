#!/usr/bin/env python3
"""
User Acceptance Testing (UAT) for MultiModelVideo Application
Tests the system from an end-user perspective to validate usability and functionality
"""

import requests
import json
import time
import sys
from typing import Dict, List, Any
import asyncio
import aiohttp

class UserAcceptanceTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_results = {}
        self.user_scenarios = []
        self.current_video_id = None
        self.current_session_id = None

    def log_scenario(self, scenario: str, status: str, details: str = "", user_impact: str = ""):
        """Log user scenario test results"""
        self.test_results[scenario] = {
            "status": status,
            "details": details,
            "user_impact": user_impact,
            "timestamp": time.time()
        }
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {scenario}")
        if details:
            print(f"   Details: {details}")
        if user_impact:
            print(f"   User Impact: {user_impact}")

    def test_user_scenario_1_video_discovery(self):
        """Scenario 1: User wants to discover and explore available videos"""
        print("\n🎬 USER SCENARIO 1: Video Discovery & Exploration")
        
        try:
            # User visits the application and wants to see available videos
            response = requests.get(f"{self.base_url}/videos", timeout=10)
            
            if response.status_code == 200:
                videos = response.json().get("videos", [])
                if len(videos) > 0:
                    self.current_video_id = videos[0]["id"]
                    video_count = len(videos)
                    
                    # Check video metadata quality
                    sample_video = videos[0]
                    has_title = sample_video.get("original_filename") is not None
                    has_duration = sample_video.get("duration", 0) > 0
                    is_processed = sample_video.get("processed", False)
                    
                    if has_title and has_duration and is_processed:
                        self.log_scenario(
                            "Video Discovery",
                            "PASS",
                            f"Found {video_count} videos with complete metadata",
                            "Users can easily browse and select videos"
                        )
                    else:
                        self.log_scenario(
                            "Video Discovery",
                            "PARTIAL",
                            f"Found {video_count} videos but some missing metadata",
                            "Users may experience incomplete video information"
                        )
                else:
                    self.log_scenario(
                        "Video Discovery",
                        "FAIL",
                        "No videos available in system",
                        "Users cannot explore any content"
                    )
            else:
                self.log_scenario(
                    "Video Discovery",
                    "FAIL",
                    f"API returned status {response.status_code}",
                    "Users cannot access video library"
                )
                
        except Exception as e:
            self.log_scenario(
                "Video Discovery",
                "FAIL",
                f"System error: {str(e)}",
                "Users cannot access the application"
            )

    def test_user_scenario_2_youtube_integration(self):
        """Scenario 2: User wants to search and add YouTube videos"""
        print("\n🔍 USER SCENARIO 2: YouTube Video Integration")
        
        try:
            # Test YouTube search functionality
            search_data = {"query": "machine learning tutorial", "max_results": 3}
            response = requests.post(
                f"{self.base_url}/api/v1/youtube/search",
                json=search_data,
                timeout=15
            )
            
            if response.status_code == 200:
                results = response.json()
                if isinstance(results, list) and len(results) > 0:
                    # Check quality of search results
                    sample_result = results[0]
                    has_title = "title" in sample_result
                    has_thumbnail = "thumbnail" in sample_result
                    has_video_id = "video_id" in sample_result
                    
                    if has_title and has_thumbnail and has_video_id:
                        self.log_scenario(
                            "YouTube Search",
                            "PASS",
                            f"Retrieved {len(results)} high-quality search results",
                            "Users can easily find and preview YouTube content"
                        )
                    else:
                        self.log_scenario(
                            "YouTube Search",
                            "PARTIAL",
                            f"Retrieved {len(results)} results with incomplete metadata",
                            "Users may have difficulty evaluating search results"
                        )
                else:
                    self.log_scenario(
                        "YouTube Search",
                        "FAIL",
                        "No search results returned",
                        "Users cannot find YouTube content"
                    )
            else:
                self.log_scenario(
                    "YouTube Search",
                    "FAIL",
                    f"Search failed with status {response.status_code}",
                    "Users cannot search for YouTube videos"
                )
                
        except Exception as e:
            self.log_scenario(
                "YouTube Search",
                "FAIL",
                f"System error: {str(e)}",
                "YouTube integration not available to users"
            )

    def test_user_scenario_3_conversational_interface(self):
        """Scenario 3: User wants to have conversations about video content"""
        print("\n💬 USER SCENARIO 3: Conversational AI Interface")
        
        if not self.current_video_id:
            self.log_scenario(
                "Chat Interface",
                "FAIL",
                "No video available for testing",
                "Users cannot start conversations without videos"
            )
            return
        
        try:
            # Test conversation start
            response = requests.post(
                f"{self.base_url}/api/v1/conversation/start",
                params={"video_id": self.current_video_id},
                timeout=10
            )
            
            if response.status_code == 200:
                session_data = response.json()
                self.current_session_id = session_data.get("session_id")
                
                if self.current_session_id:
                    self.log_scenario(
                        "Chat Session Creation",
                        "PASS",
                        f"Created session {self.current_session_id}",
                        "Users can start conversations about videos"
                    )
                    
                    # Test sending a message
                    self.test_chat_messaging()
                else:
                    self.log_scenario(
                        "Chat Session Creation",
                        "FAIL",
                        "No session ID returned",
                        "Users cannot establish chat sessions"
                    )
            else:
                self.log_scenario(
                    "Chat Session Creation",
                    "FAIL",
                    f"Failed with status {response.status_code}",
                    "Users cannot access conversational features"
                )
                
        except Exception as e:
            self.log_scenario(
                "Chat Session Creation",
                "FAIL",
                f"System error: {str(e)}",
                "Conversational interface unavailable"
            )

    def test_chat_messaging(self):
        """Test actual chat messaging functionality"""
        if not self.current_session_id:
            return
            
        try:
            message_data = {
                "session_id": self.current_session_id,
                "message": "What is this video about?"
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/conversation/{self.current_session_id}/ask",
                json=message_data,
                timeout=20
            )
            
            if response.status_code == 200:
                chat_response = response.json()
                answer = chat_response.get("answer", "")
                
                if len(answer) > 10:  # Reasonable response length
                    self.log_scenario(
                        "Chat Messaging",
                        "PASS",
                        f"Received {len(answer)} character response",
                        "Users get meaningful AI responses about video content"
                    )
                else:
                    self.log_scenario(
                        "Chat Messaging",
                        "PARTIAL",
                        "Response too short or empty",
                        "Users may receive inadequate AI responses"
                    )
            else:
                self.log_scenario(
                    "Chat Messaging",
                    "FAIL",
                    f"Message failed with status {response.status_code}",
                    "Users cannot send messages in chat"
                )
                
        except Exception as e:
            self.log_scenario(
                "Chat Messaging",
                "FAIL",
                f"Messaging error: {str(e)}",
                "Chat functionality unavailable"
            )

    def test_user_scenario_4_content_analysis(self):
        """Scenario 4: User wants to analyze video content and get insights"""
        print("\n📊 USER SCENARIO 4: Content Analysis & Insights")
        
        if not self.current_video_id:
            self.log_scenario(
                "Content Analysis",
                "FAIL",
                "No video available for testing",
                "Users cannot analyze content without videos"
            )
            return
        
        try:
            # Test topic analysis
            response = requests.post(
                f"{self.base_url}/api/v1/content/analyze-topics",
                params={"video_id": self.current_video_id},
                timeout=15
            )
            
            if response.status_code == 200:
                analysis = response.json()
                topics = analysis.get("topics", [])
                
                if len(topics) > 0:
                    # Check quality of topic analysis
                    sample_topic = topics[0]
                    has_timeline = "start_time" in sample_topic and "end_time" in sample_topic
                    has_summary = "topic_summary" in sample_topic
                    has_keywords = "keywords" in sample_topic
                    
                    if has_timeline and has_summary:
                        self.log_scenario(
                            "Topic Analysis",
                            "PASS",
                            f"Generated {len(topics)} topic segments with timestamps",
                            "Users can understand video structure and key topics"
                        )
                    else:
                        self.log_scenario(
                            "Topic Analysis",
                            "PARTIAL",
                            f"Generated {len(topics)} topics with incomplete metadata",
                            "Users get basic topic analysis but may lack detail"
                        )
                else:
                    self.log_scenario(
                        "Topic Analysis",
                        "FAIL",
                        "No topics identified in video",
                        "Users cannot get content insights"
                    )
            else:
                self.log_scenario(
                    "Topic Analysis",
                    "FAIL",
                    f"Analysis failed with status {response.status_code}",
                    "Content analysis unavailable to users"
                )
                
        except Exception as e:
            self.log_scenario(
                "Topic Analysis",
                "FAIL",
                f"Analysis error: {str(e)}",
                "Content analysis features unavailable"
            )

    def test_user_scenario_5_navigation_experience(self):
        """Scenario 5: User wants to navigate through video content efficiently"""
        print("\n🧭 USER SCENARIO 5: Video Navigation Experience")
        
        if not self.current_video_id:
            self.log_scenario(
                "Video Navigation",
                "FAIL",
                "No video available for testing",
                "Users cannot test navigation without videos"
            )
            return
        
        try:
            # Test navigation data
            response = requests.get(
                f"{self.base_url}/api/v1/content/navigation/{self.current_video_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                nav_data = response.json()
                topic_segments = nav_data.get("topic_segments", [])
                navigation_events = nav_data.get("navigation_events", [])
                stats = nav_data.get("statistics", {})
                
                total_segments = stats.get("total_segments", 0)
                total_events = stats.get("total_events", 0)
                
                if total_segments > 0 or total_events > 0:
                    self.log_scenario(
                        "Video Navigation",
                        "PASS",
                        f"Navigation data: {total_segments} segments, {total_events} events",
                        "Users can navigate video content with structured guidance"
                    )
                else:
                    self.log_scenario(
                        "Video Navigation",
                        "PARTIAL",
                        "Navigation data available but minimal content",
                        "Users have basic navigation but limited guidance"
                    )
            else:
                self.log_scenario(
                    "Video Navigation",
                    "FAIL",
                    f"Navigation failed with status {response.status_code}",
                    "Video navigation features unavailable"
                )
                
        except Exception as e:
            self.log_scenario(
                "Video Navigation",
                "FAIL",
                f"Navigation error: {str(e)}",
                "Navigation features unavailable"
            )

    def test_system_responsiveness(self):
        """Test system responsiveness for good user experience"""
        print("\n⚡ SYSTEM RESPONSIVENESS TEST")
        
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/health", timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200 and response_time < 1000:
                self.log_scenario(
                    "System Responsiveness",
                    "PASS",
                    f"Health check: {response_time:.0f}ms",
                    "Users experience fast system responses"
                )
            elif response.status_code == 200:
                self.log_scenario(
                    "System Responsiveness",
                    "PARTIAL",
                    f"Health check: {response_time:.0f}ms (slow)",
                    "Users may experience some delays"
                )
            else:
                self.log_scenario(
                    "System Responsiveness",
                    "FAIL",
                    f"Health check failed: {response.status_code}",
                    "System may be unresponsive to users"
                )
                
        except Exception as e:
            self.log_scenario(
                "System Responsiveness",
                "FAIL",
                f"System error: {str(e)}",
                "System may be unavailable to users"
            )

    def generate_uat_report(self):
        """Generate comprehensive UAT report"""
        print("\n" + "=" * 80)
        print("🎯 USER ACCEPTANCE TESTING REPORT")
        print("=" * 80)
        
        passed_tests = [k for k, v in self.test_results.items() if v["status"] == "PASS"]
        partial_tests = [k for k, v in self.test_results.items() if v["status"] == "PARTIAL"]
        failed_tests = [k for k, v in self.test_results.items() if v["status"] == "FAIL"]
        
        total_tests = len(self.test_results)
        pass_rate = (len(passed_tests) / total_tests * 100) if total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS:")
        print(f"   Total Scenarios Tested: {total_tests}")
        print(f"   Passed: {len(passed_tests)} ({len(passed_tests)/total_tests*100:.1f}%)")
        print(f"   Partial: {len(partial_tests)} ({len(partial_tests)/total_tests*100:.1f}%)")
        print(f"   Failed: {len(failed_tests)} ({len(failed_tests)/total_tests*100:.1f}%)")
        
        print(f"\n🎖️ USER ACCEPTANCE RATING:")
        if pass_rate >= 90:
            print("   EXCELLENT - Ready for immediate user deployment")
        elif pass_rate >= 75:
            print("   GOOD - Ready for user testing with minor improvements")
        elif pass_rate >= 60:
            print("   ACCEPTABLE - Needs some improvements before user deployment")
        else:
            print("   NEEDS WORK - Significant improvements required")
        
        if failed_tests:
            print(f"\n❌ CRITICAL ISSUES FOR USERS:")
            for test in failed_tests:
                impact = self.test_results[test]["user_impact"]
                print(f"   • {test}: {impact}")
        
        if partial_tests:
            print(f"\n⚠️ AREAS FOR IMPROVEMENT:")
            for test in partial_tests:
                impact = self.test_results[test]["user_impact"]
                print(f"   • {test}: {impact}")
        
        print(f"\n✅ WORKING WELL FOR USERS:")
        for test in passed_tests:
            impact = self.test_results[test]["user_impact"]
            print(f"   • {test}: {impact}")
        
        return pass_rate >= 75

    def run_user_acceptance_tests(self):
        """Run all user acceptance tests"""
        print("🧑‍💻 MULTIMODELVIDEO USER ACCEPTANCE TESTING")
        print("Testing system from end-user perspective...")
        print("=" * 80)
        
        # Run all user scenarios
        self.test_user_scenario_1_video_discovery()
        self.test_user_scenario_2_youtube_integration()
        self.test_user_scenario_3_conversational_interface()
        self.test_user_scenario_4_content_analysis()
        self.test_user_scenario_5_navigation_experience()
        self.test_system_responsiveness()
        
        # Generate report
        return self.generate_uat_report()

def main():
    """Run User Acceptance Testing"""
    uat_tester = UserAcceptanceTest()
    
    try:
        success = uat_tester.run_user_acceptance_tests()
        
        if success:
            print("\n🎉 USER ACCEPTANCE TESTING PASSED!")
            print("The system is ready for user deployment.")
            sys.exit(0)
        else:
            print("\n⚠️ USER ACCEPTANCE TESTING NEEDS ATTENTION")
            print("Review the issues above before user deployment.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nUser Acceptance Testing interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error during UAT: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
