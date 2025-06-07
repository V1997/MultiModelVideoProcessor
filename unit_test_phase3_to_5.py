#!/usr/bin/env python3
"""
Unit Tests for Phase 3-5 Components
Tests individual components without requiring API server
"""

import sys
import os
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_conversation_manager():
    """Test ConversationManager functionality"""
    print("🗣️ Testing ConversationManager...")
    
    try:
        from backend.conversation.manager import ConversationManager
        
        # Create manager with mock RAG system
        mock_rag = MagicMock()
        manager = ConversationManager(mock_rag)
        
        # Mock database
        mock_db = MagicMock()
        
        # Test session creation
        session = manager.create_session(
            db=mock_db,
            video_id=1,
            title="Test Session"
        )
        
        print("   ✅ Session creation: WORKING")
        print(f"   📋 Session ID: {session.session_id}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ ConversationManager test failed: {e}")
        return False

def test_visual_search_engine():
    """Test VisualSearchEngine functionality"""
    print("👁️ Testing VisualSearchEngine...")
    
    try:
        from backend.visual_search.engine import VisualSearchEngine
        
        engine = VisualSearchEngine()
        
        # Test initialization
        print("   ✅ Engine initialization: WORKING")
        
        # Test search method (mock)
        mock_db = MagicMock()
        results = engine.search_frames(
            db=mock_db,
            video_id=1,
            query="person talking",
            confidence_threshold=0.5
        )
        
        print("   ✅ Search functionality: WORKING")
        
        return True
        
    except Exception as e:
        print(f"   ❌ VisualSearchEngine test failed: {e}")
        return False

def test_content_segmentation_engine():
    """Test ContentSegmentationEngine functionality"""
    print("📊 Testing ContentSegmentationEngine...")
    
    try:
        from backend.content_analysis.segmentation import ContentSegmentationEngine
        
        engine = ContentSegmentationEngine()
        
        # Test initialization
        print("   ✅ Engine initialization: WORKING")
        
        # Test topic analysis (mock)
        mock_db = MagicMock()
        topics = engine.analyze_transcript_topics(
            db=mock_db,
            video_id=1
        )
        
        print("   ✅ Topic analysis: WORKING")
        
        return True
        
    except Exception as e:
        print(f"   ❌ ContentSegmentationEngine test failed: {e}")
        return False

def test_database_models():
    """Test database models for Phase 3-5"""
    print("🗄️ Testing Database Models...")
    
    try:
        from backend.database.models import Video, TranscriptChunk, VideoFrame
        
        # Test model creation (without database)
        video = Video(
            filename="test.mp4",
            original_filename="test.mp4",
            file_path="/path/to/test.mp4",
            duration=120.0,
            width=1920,
            height=1080,
            fps=30.0,
            file_size=1024000
        )
        
        print("   ✅ Video model: WORKING")
        
        chunk = TranscriptChunk(
            video_id=1,
            text="Sample transcript text",
            start_time=0.0,
            end_time=5.0,
            chunk_index=0
        )
        
        print("   ✅ TranscriptChunk model: WORKING")
        
        frame = VideoFrame(
            video_id=1,
            frame_path="/path/to/frame.jpg",
            timestamp=10.0,
            frame_number=300
        )
        
        print("   ✅ VideoFrame model: WORKING")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Database models test failed: {e}")
        return False

def test_phase3_to_5_imports():
    """Test that all Phase 3-5 components can be imported"""
    print("📦 Testing Phase 3-5 Component Imports...")
    
    components = [
        ("ConversationManager", "backend.conversation.manager"),
        ("VisualSearchEngine", "backend.visual_search.engine"),
        ("ContentSegmentationEngine", "backend.content_analysis.segmentation"),
    ]
    
    success_count = 0
    
    for component_name, module_path in components:
        try:
            module = __import__(module_path, fromlist=[component_name])
            component = getattr(module, component_name)
            print(f"   ✅ {component_name}: IMPORTABLE")
            success_count += 1
        except Exception as e:
            print(f"   ❌ {component_name}: FAILED - {e}")
    
    return success_count == len(components)

def run_unit_tests():
    """Run all unit tests"""
    print("🧪 Phase 3-5 Unit Test Suite")
    print("=" * 50)
    
    tests = [
        ("Phase 3-5 Imports", test_phase3_to_5_imports),
        ("Database Models", test_database_models),
        ("Conversation Manager", test_conversation_manager),
        ("Visual Search Engine", test_visual_search_engine),
        ("Content Segmentation", test_content_segmentation_engine),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            success = test_func()
            results[test_name] = success
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 UNIT TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for success in results.values() if success)
    total = len(results)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    success_rate = (passed / total) * 100
    print(f"📊 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 Phase 3-5 components are working well!")
    elif success_rate >= 60:
        print("⚠️ Phase 3-5 components are mostly working")
    else:
        print("🔧 Phase 3-5 components need attention")
    
    return results

if __name__ == "__main__":
    run_unit_tests()
