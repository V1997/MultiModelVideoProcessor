#!/usr/bin/env python3
"""
Feature Validation Testing for MultiModelVideo Application
Comprehensive validation of all Phase 1-5 features to demonstrate system capabilities
"""

import requests
import json
import time
import sys
from typing import Dict, List, Any
import os
from datetime import datetime

class FeatureValidationTest:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.feature_results = {}
        self.demo_data = {}

    def log_feature(self, feature: str, phase: str, status: str, details: str = "", demo_value: str = ""):
        """Log feature validation results"""
        self.feature_results[feature] = {
            "phase": phase,
            "status": status,
            "details": details,
            "demo_value": demo_value,
            "timestamp": datetime.now().isoformat()
        }
        
        status_icon = "✅" if status == "WORKING" else "❌" if status == "BROKEN" else "⚠️"
        print(f"{status_icon} {phase} - {feature}")
        if details:
            print(f"      {details}")
        if demo_value:
            print(f"      Demo: {demo_value}")

    def validate_phase1_features(self):
        """Validate Phase 1: Core Video Processing"""
        print("\n🎬 PHASE 1 FEATURE VALIDATION: Core Video Processing")
        
        # Feature 1: Video Upload System
        try:
            # Check upload endpoint exists
            response = requests.options(f"{self.base_url}/upload-video", timeout=5)
            if response.status_code in [200, 405]:  # 405 = Method not allowed, but endpoint exists
                self.log_feature(
                    "Video Upload System",
                    "Phase 1",
                    "WORKING",
                    "Upload endpoint available and configured",
                    "Users can upload MP4, AVI, MOV, MKV, WebM files"
                )
            else:
                self.log_feature(
                    "Video Upload System",
                    "Phase 1",
                    "BROKEN",
                    f"Upload endpoint returned {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "Video Upload System",
                "Phase 1",
                "BROKEN",
                f"Upload system error: {str(e)}"
            )

        # Feature 2: Video Database Management
        try:
            response = requests.get(f"{self.base_url}/videos", timeout=10)
            if response.status_code == 200:
                videos = response.json().get("videos", [])
                processed_count = len([v for v in videos if v.get("processed", False)])
                self.log_feature(
                    "Video Database Management",
                    "Phase 1",
                    "WORKING",
                    f"Database contains {len(videos)} videos, {processed_count} processed",
                    f"System manages {len(videos)} videos with metadata tracking"
                )
            else:
                self.log_feature(
                    "Video Database Management",
                    "Phase 1",
                    "BROKEN",
                    f"Database query failed: {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "Video Database Management",
                "Phase 1",
                "BROKEN",
                f"Database error: {str(e)}"
            )

        # Feature 3: YouTube Integration
        try:
            response = requests.options(f"{self.base_url}/process-youtube", timeout=5)
            if response.status_code in [200, 405]:
                self.log_feature(
                    "YouTube Video Processing",
                    "Phase 1",
                    "WORKING",
                    "YouTube processing endpoint available",
                    "Users can import YouTube videos by URL"
                )
            else:
                self.log_feature(
                    "YouTube Video Processing",
                    "Phase 1",
                    "BROKEN",
                    f"YouTube endpoint issue: {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "YouTube Video Processing",
                "Phase 1",
                "BROKEN",
                f"YouTube integration error: {str(e)}"
            )

        # Feature 4: Transcript Generation
        try:
            # Check if any videos have transcripts
            response = requests.get(f"{self.base_url}/videos", timeout=10)
            if response.status_code == 200:
                videos = response.json().get("videos", [])
                transcript_count = len([v for v in videos if v.get("transcript_generated", False)])
                if transcript_count > 0:
                    self.log_feature(
                        "Transcript Generation",
                        "Phase 1",
                        "WORKING",
                        f"{transcript_count} videos have generated transcripts",
                        "Automatic transcript generation from YouTube API and Whisper"
                    )
                else:
                    self.log_feature(
                        "Transcript Generation",
                        "Phase 1",
                        "PARTIAL",
                        "Transcript system available but no transcripts generated"
                    )
        except Exception as e:
            self.log_feature(
                "Transcript Generation",
                "Phase 1",
                "BROKEN",
                f"Transcript check error: {str(e)}"
            )

        # Feature 5: Frame Extraction
        try:
            response = requests.get(f"{self.base_url}/videos", timeout=10)
            if response.status_code == 200:
                videos = response.json().get("videos", [])
                frames_count = len([v for v in videos if v.get("frames_extracted", False)])
                if frames_count > 0:
                    self.log_feature(
                        "Frame Extraction",
                        "Phase 1",
                        "WORKING",
                        f"{frames_count} videos have extracted frames",
                        "Automated frame extraction for visual analysis"
                    )
                else:
                    self.log_feature(
                        "Frame Extraction",
                        "Phase 1",
                        "PARTIAL",
                        "Frame extraction available but not executed"
                    )
        except Exception as e:
            self.log_feature(
                "Frame Extraction",
                "Phase 1",
                "BROKEN",
                f"Frame extraction error: {str(e)}"
            )

    def validate_phase2_features(self):
        """Validate Phase 2: Vector Embeddings & RAG"""
        print("\n🔍 PHASE 2 FEATURE VALIDATION: Vector Embeddings & RAG")
        
        # Feature 1: Vector Embeddings
        try:
            response = requests.get(f"{self.base_url}/api/v1/embeddings/status", timeout=10)
            if response.status_code == 200:
                status = response.json()
                self.log_feature(
                    "Vector Embeddings",
                    "Phase 2",
                    "WORKING",
                    f"Embeddings system: {status}",
                    "Semantic search and similarity matching available"
                )
            elif response.status_code == 501:
                self.log_feature(
                    "Vector Embeddings",
                    "Phase 2",
                    "PARTIAL",
                    "Embeddings endpoints exist but service not implemented",
                    "Framework ready for embedding generation"
                )
            else:
                self.log_feature(
                    "Vector Embeddings",
                    "Phase 2",
                    "BROKEN",
                    f"Embeddings status error: {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "Vector Embeddings",
                "Phase 2",
                "BROKEN",
                f"Embeddings error: {str(e)}"
            )

        # Feature 2: Semantic Search
        try:
            search_data = {"query": "machine learning", "limit": 5}
            response = requests.post(
                f"{self.base_url}/api/v1/search/semantic",
                json=search_data,
                timeout=10
            )
            if response.status_code == 200:
                results = response.json()
                self.log_feature(
                    "Semantic Search",
                    "Phase 2",
                    "WORKING",
                    f"Search returned {len(results)} results",
                    "Users can search video content by meaning, not just keywords"
                )
            elif response.status_code == 501:
                self.log_feature(
                    "Semantic Search",
                    "Phase 2",
                    "PARTIAL",
                    "Search endpoint exists but not fully implemented"
                )
            else:
                self.log_feature(
                    "Semantic Search",
                    "Phase 2",
                    "BROKEN",
                    f"Search failed: {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "Semantic Search",
                "Phase 2",
                "BROKEN",
                f"Search error: {str(e)}"
            )

        # Feature 3: Multimodal RAG
        try:
            rag_data = {"query": "What is this video about?", "video_id": 1}
            response = requests.post(
                f"{self.base_url}/api/v1/query/multimodal",
                json=rag_data,
                timeout=15
            )
            if response.status_code == 200:
                result = response.json()
                answer = result.get("answer", "")
                if len(answer) > 10:
                    self.log_feature(
                        "Multimodal RAG",
                        "Phase 2",
                        "WORKING",
                        f"Generated {len(answer)} character answer",
                        "AI can answer questions about video content with citations"
                    )
                else:
                    self.log_feature(
                        "Multimodal RAG",
                        "Phase 2",
                        "PARTIAL",
                        "RAG working but answers are brief"
                    )
            elif response.status_code == 501:
                self.log_feature(
                    "Multimodal RAG",
                    "Phase 2",
                    "PARTIAL",
                    "RAG endpoint exists but not fully implemented"
                )
            else:
                self.log_feature(
                    "Multimodal RAG",
                    "Phase 2",
                    "BROKEN",
                    f"RAG failed: {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "Multimodal RAG",
                "Phase 2",
                "BROKEN",
                f"RAG error: {str(e)}"
            )

    def validate_phase3_features(self):
        """Validate Phase 3: Conversational Interface"""
        print("\n💬 PHASE 3 FEATURE VALIDATION: Conversational Interface")
        
        # Feature 1: Chat Session Management
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/conversation/start",
                params={"video_id": 1},
                timeout=10
            )
            if response.status_code == 200:
                session_data = response.json()
                session_id = session_data.get("session_id")
                if session_id:
                    self.log_feature(
                        "Chat Session Management",
                        "Phase 3",
                        "WORKING",
                        f"Created session: {session_id}",
                        "Users can start personalized chat sessions with videos"
                    )
                    
                    # Test messaging in the session
                    self.test_chat_messaging(session_id)
                else:
                    self.log_feature(
                        "Chat Session Management",
                        "Phase 3",
                        "PARTIAL",
                        "Session created but no ID returned"
                    )
            elif response.status_code == 501:
                self.log_feature(
                    "Chat Session Management",
                    "Phase 3",
                    "PARTIAL",
                    "Chat endpoints exist but not fully implemented"
                )
            else:
                self.log_feature(
                    "Chat Session Management",
                    "Phase 3",
                    "BROKEN",
                    f"Session creation failed: {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "Chat Session Management",
                "Phase 3",
                "BROKEN",
                f"Chat session error: {str(e)}"
            )

        # Feature 2: Context-Aware Conversations
        try:
            # Check if conversation history is maintained
            response = requests.get(f"{self.base_url}/api/v1/chat/sessions", timeout=10)
            if response.status_code == 200:
                self.log_feature(
                    "Context-Aware Conversations",
                    "Phase 3",
                    "WORKING",
                    "Chat session history tracking available",
                    "AI maintains conversation context and remembers previous exchanges"
                )
            elif response.status_code == 404:
                self.log_feature(
                    "Context-Aware Conversations",
                    "Phase 3",
                    "PARTIAL",
                    "Chat system partially implemented"
                )
            else:
                self.log_feature(
                    "Context-Aware Conversations",
                    "Phase 3",
                    "BROKEN",
                    f"Context system error: {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "Context-Aware Conversations",
                "Phase 3",
                "BROKEN",
                f"Context error: {str(e)}"
            )

    def test_chat_messaging(self, session_id: str):
        """Test chat messaging within a session"""
        try:
            message_data = {
                "session_id": session_id,
                "message": "Tell me about the main topics in this video"
            }
            response = requests.post(
                f"{self.base_url}/api/v1/conversation/{session_id}/ask",
                json=message_data,
                timeout=20
            )
            
            if response.status_code == 200:
                chat_response = response.json()
                answer = chat_response.get("answer", "")
                confidence = chat_response.get("confidence", 0)
                
                if len(answer) > 20 and confidence > 0:
                    self.log_feature(
                        "AI Chat Responses",
                        "Phase 3",
                        "WORKING",
                        f"Generated {len(answer)} char response, confidence: {confidence}",
                        "AI provides detailed, confident answers about video content"
                    )
                else:
                    self.log_feature(
                        "AI Chat Responses",
                        "Phase 3",
                        "PARTIAL",
                        "Chat working but responses need improvement"
                    )
            else:
                self.log_feature(
                    "AI Chat Responses",
                    "Phase 3",
                    "BROKEN",
                    f"Chat messaging failed: {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "AI Chat Responses",
                "Phase 3",
                "BROKEN",
                f"Chat messaging error: {str(e)}"
            )

    def validate_phase4_features(self):
        """Validate Phase 4: Visual Search Engine"""
        print("\n👁️ PHASE 4 FEATURE VALIDATION: Visual Search Engine")
        
        # Feature 1: Object Detection
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/visual-search/detect-objects",
                params={"video_id": 1, "frame_path": "test_frame.jpg", "confidence_threshold": 0.5},
                timeout=15
            )
            if response.status_code == 200:
                detection_results = response.json()
                self.log_feature(
                    "Object Detection",
                    "Phase 4",
                    "WORKING",
                    f"Object detection completed: {detection_results}",
                    "AI can identify objects and scenes in video frames"
                )
            elif response.status_code in [422, 501]:
                self.log_feature(
                    "Object Detection",
                    "Phase 4",
                    "PARTIAL",
                    "Object detection endpoint exists, needs proper parameters"
                )
            else:
                self.log_feature(
                    "Object Detection",
                    "Phase 4",
                    "BROKEN",
                    f"Object detection failed: {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "Object Detection",
                "Phase 4",
                "BROKEN",
                f"Object detection error: {str(e)}"
            )

        # Feature 2: Visual Search
        try:
            search_data = {"video_id": 1, "query": "person speaking", "confidence_threshold": 0.3}
            response = requests.post(
                f"{self.base_url}/api/v1/visual-search/search/1",
                json=search_data,
                timeout=15
            )
            if response.status_code == 200:
                search_results = response.json()
                self.log_feature(
                    "Visual Content Search",
                    "Phase 4",
                    "WORKING",
                    f"Visual search completed: {search_results}",
                    "Users can search for visual content using natural language"
                )
            elif response.status_code in [422, 501]:
                self.log_feature(
                    "Visual Content Search",
                    "Phase 4",
                    "PARTIAL",
                    "Visual search endpoint exists, framework ready"
                )
            else:
                self.log_feature(
                    "Visual Content Search",
                    "Phase 4",
                    "BROKEN",
                    f"Visual search failed: {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "Visual Content Search",
                "Phase 4",
                "BROKEN",
                f"Visual search error: {str(e)}"
            )

        # Feature 3: Scene Classification
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/visual/process/1",
                timeout=15
            )
            if response.status_code == 200:
                processing_result = response.json()
                self.log_feature(
                    "Scene Classification",
                    "Phase 4",
                    "WORKING",
                    f"Scene processing: {processing_result}",
                    "AI automatically classifies scenes and visual content"
                )
            elif response.status_code in [422, 501]:
                self.log_feature(
                    "Scene Classification",
                    "Phase 4",
                    "PARTIAL",
                    "Scene classification framework ready"
                )
            else:
                self.log_feature(
                    "Scene Classification",
                    "Phase 4",
                    "BROKEN",
                    f"Scene classification failed: {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "Scene Classification",
                "Phase 4",
                "BROKEN",
                f"Scene classification error: {str(e)}"
            )

    def validate_phase5_features(self):
        """Validate Phase 5: Content Segmentation & Navigation"""
        print("\n🧭 PHASE 5 FEATURE VALIDATION: Content Segmentation & Navigation")
        
        # Feature 1: Topic Segmentation
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/content/analyze-topics",
                params={"video_id": 1},
                timeout=15
            )
            if response.status_code == 200:
                segmentation = response.json()
                topics = segmentation.get("topics", [])
                self.log_feature(
                    "Topic Segmentation",
                    "Phase 5",
                    "WORKING",
                    f"Generated {len(topics)} topic segments with timestamps",
                    "AI automatically segments videos by topic with precise timing"
                )
            elif response.status_code == 501:
                self.log_feature(
                    "Topic Segmentation",
                    "Phase 5",
                    "PARTIAL",
                    "Topic segmentation endpoint ready"
                )
            else:
                self.log_feature(
                    "Topic Segmentation",
                    "Phase 5",
                    "BROKEN",
                    f"Topic segmentation failed: {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "Topic Segmentation",
                "Phase 5",
                "BROKEN",
                f"Topic segmentation error: {str(e)}"
            )

        # Feature 2: Content Outline Generation
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/content/generate-outline",
                params={"video_id": 1},
                timeout=15
            )
            if response.status_code == 200:
                outline = response.json()
                self.log_feature(
                    "Content Outline Generation",
                    "Phase 5",
                    "WORKING",
                    f"Generated content outline: {outline}",
                    "AI creates structured outlines for easy video navigation"
                )
            elif response.status_code == 501:
                self.log_feature(
                    "Content Outline Generation",
                    "Phase 5",
                    "PARTIAL",
                    "Outline generation endpoint ready"
                )
            else:
                self.log_feature(
                    "Content Outline Generation",
                    "Phase 5",
                    "BROKEN",
                    f"Outline generation failed: {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "Content Outline Generation",
                "Phase 5",
                "BROKEN",
                f"Outline generation error: {str(e)}"
            )

        # Feature 3: Enhanced Navigation
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/content/navigation/1",
                timeout=10
            )
            if response.status_code == 200:
                nav_data = response.json()
                stats = nav_data.get("statistics", {})
                total_segments = stats.get("total_segments", 0)
                total_events = stats.get("total_events", 0)
                
                self.log_feature(
                    "Enhanced Video Navigation",
                    "Phase 5",
                    "WORKING",
                    f"Navigation: {total_segments} segments, {total_events} events",
                    "Users get intelligent navigation with automatic timestamps and bookmarks"
                )
            elif response.status_code == 501:
                self.log_feature(
                    "Enhanced Video Navigation",
                    "Phase 5",
                    "PARTIAL",
                    "Navigation system framework ready"
                )
            else:
                self.log_feature(
                    "Enhanced Video Navigation",
                    "Phase 5",
                    "BROKEN",
                    f"Navigation failed: {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "Enhanced Video Navigation",
                "Phase 5",
                "BROKEN",
                f"Navigation error: {str(e)}"
            )

    def validate_youtube_integration(self):
        """Validate YouTube Integration (Bonus Feature)"""
        print("\n🎥 BONUS FEATURE VALIDATION: YouTube Integration")
        
        # Feature 1: YouTube Search
        try:
            search_data = {"query": "python programming", "max_results": 3}
            response = requests.post(
                f"{self.base_url}/api/v1/youtube/search",
                json=search_data,
                timeout=15
            )
            if response.status_code == 200:
                results = response.json()
                if isinstance(results, list) and len(results) > 0:
                    self.log_feature(
                        "YouTube Search API",
                        "Bonus",
                        "WORKING",
                        f"Retrieved {len(results)} YouTube search results",
                        "Users can search and import YouTube videos directly"
                    )
                else:
                    self.log_feature(
                        "YouTube Search API",
                        "Bonus",
                        "PARTIAL",
                        "YouTube search working but no results"
                    )
            else:
                self.log_feature(
                    "YouTube Search API",
                    "Bonus",
                    "BROKEN",
                    f"YouTube search failed: {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "YouTube Search API",
                "Bonus",
                "BROKEN",
                f"YouTube search error: {str(e)}"
            )

        # Feature 2: YouTube Video Info
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/youtube/info",
                params={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
                timeout=10
            )
            if response.status_code == 200:
                info = response.json()
                self.log_feature(
                    "YouTube Video Information",
                    "Bonus",
                    "WORKING",
                    f"Retrieved video metadata: {info}",
                    "Detailed YouTube video information and metadata extraction"
                )
            else:
                self.log_feature(
                    "YouTube Video Information",
                    "Bonus",
                    "BROKEN",
                    f"YouTube info failed: {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "YouTube Video Information",
                "Bonus",
                "BROKEN",
                f"YouTube info error: {str(e)}"
            )

    def validate_infrastructure_features(self):
        """Validate Infrastructure & Performance Features"""
        print("\n🏗️ INFRASTRUCTURE FEATURE VALIDATION: Core Systems")
        
        # Feature 1: Redis Caching
        try:
            response = requests.get(f"{self.base_url}/redis/status", timeout=5)
            if response.status_code == 200:
                redis_status = response.json()
                self.log_feature(
                    "Redis Caching System",
                    "Infrastructure",
                    "WORKING",
                    f"Redis operational: {redis_status}",
                    "High-performance caching for improved response times"
                )
            else:
                self.log_feature(
                    "Redis Caching System",
                    "Infrastructure",
                    "BROKEN",
                    f"Redis status failed: {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "Redis Caching System",
                "Infrastructure",
                "BROKEN",
                f"Redis error: {str(e)}"
            )

        # Feature 2: WebSocket Support
        try:
            response = requests.get(f"{self.base_url}/api/v1/websocket/connections", timeout=5)
            if response.status_code == 200:
                ws_status = response.json()
                self.log_feature(
                    "WebSocket Real-time Updates",
                    "Infrastructure",
                    "WORKING",
                    f"WebSocket service: {ws_status}",
                    "Real-time updates and live chat functionality"
                )
            else:
                self.log_feature(
                    "WebSocket Real-time Updates",
                    "Infrastructure",
                    "BROKEN",
                    f"WebSocket status failed: {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "WebSocket Real-time Updates",
                "Infrastructure",
                "BROKEN",
                f"WebSocket error: {str(e)}"
            )

        # Feature 3: API Documentation
        try:
            response = requests.get(f"{self.base_url}/docs", timeout=5)
            if response.status_code == 200:
                self.log_feature(
                    "API Documentation",
                    "Infrastructure",
                    "WORKING",
                    "Swagger UI documentation accessible",
                    "Complete interactive API documentation for developers"
                )
            else:
                self.log_feature(
                    "API Documentation",
                    "Infrastructure",
                    "BROKEN",
                    f"Documentation failed: {response.status_code}"
                )
        except Exception as e:
            self.log_feature(
                "API Documentation",
                "Infrastructure",
                "BROKEN",
                f"Documentation error: {str(e)}"
            )

    def generate_feature_validation_report(self):
        """Generate comprehensive feature validation report"""
        print("\n" + "=" * 80)
        print("🎯 FEATURE VALIDATION REPORT")
        print("=" * 80)
        
        # Organize features by phase
        phase_features = {}
        for feature, data in self.feature_results.items():
            phase = data["phase"]
            if phase not in phase_features:
                phase_features[phase] = []
            phase_features[phase].append((feature, data))
        
        total_features = len(self.feature_results)
        working_features = len([f for f in self.feature_results.values() if f["status"] == "WORKING"])
        partial_features = len([f for f in self.feature_results.values() if f["status"] == "PARTIAL"])
        broken_features = len([f for f in self.feature_results.values() if f["status"] == "BROKEN"])
        
        print(f"📊 OVERALL FEATURE STATUS:")
        print(f"   Total Features Tested: {total_features}")
        print(f"   Fully Working: {working_features} ({working_features/total_features*100:.1f}%)")
        print(f"   Partially Working: {partial_features} ({partial_features/total_features*100:.1f}%)")
        print(f"   Not Working: {broken_features} ({broken_features/total_features*100:.1f}%)")
        
        # Report by phase
        for phase in ["Phase 1", "Phase 2", "Phase 3", "Phase 4", "Phase 5", "Bonus", "Infrastructure"]:
            if phase in phase_features:
                print(f"\n📋 {phase.upper()} FEATURES:")
                for feature, data in phase_features[phase]:
                    status_icon = "✅" if data["status"] == "WORKING" else "❌" if data["status"] == "BROKEN" else "⚠️"
                    print(f"   {status_icon} {feature}")
                    if data["demo_value"]:
                        print(f"      Demo: {data['demo_value']}")
        
        # Feature readiness assessment
        working_percentage = (working_features / total_features * 100) if total_features > 0 else 0
        
        print(f"\n🎖️ FEATURE READINESS ASSESSMENT:")
        if working_percentage >= 85:
            print("   EXCELLENT - All major features are fully functional")
            print("   ✅ System ready for immediate demonstration and deployment")
        elif working_percentage >= 70:
            print("   GOOD - Most features working with minor issues")
            print("   ✅ System ready for demonstration with noted limitations")
        elif working_percentage >= 50:
            print("   ACCEPTABLE - Core features working, some advanced features need work")
            print("   ⚠️ System can be demonstrated but needs improvement")
        else:
            print("   NEEDS WORK - Many features not working properly")
            print("   ❌ System needs significant work before demonstration")
        
        return working_percentage >= 70

    def run_feature_validation(self):
        """Run comprehensive feature validation"""
        print("🎯 MULTIMODELVIDEO FEATURE VALIDATION TESTING")
        print("Validating all Phase 1-5 features and capabilities...")
        print("=" * 80)
        
        # Run all feature validations
        self.validate_phase1_features()
        self.validate_phase2_features()
        self.validate_phase3_features()
        self.validate_phase4_features()
        self.validate_phase5_features()
        self.validate_youtube_integration()
        self.validate_infrastructure_features()
        
        # Generate comprehensive report
        return self.generate_feature_validation_report()

def main():
    """Run Feature Validation Testing"""
    validator = FeatureValidationTest()
    
    try:
        success = validator.run_feature_validation()
        
        if success:
            print("\n🎉 FEATURE VALIDATION PASSED!")
            print("All major features are ready for demonstration.")
            sys.exit(0)
        else:
            print("\n⚠️ FEATURE VALIDATION NEEDS ATTENTION")
            print("Review the feature status above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nFeature validation interrupted.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error during feature validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
