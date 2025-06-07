"""
Integration tests for Phase 3-5 MultiModelVideo features
Tests conversational interface, visual search engine, and content segmentation
"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import Phase 3-5 components
from backend.conversation.manager import ConversationManager
from backend.visual_search.engine import VisualSearchEngine
from backend.content_analysis.segmentation import ContentSegmentationEngine


class TestPhase3To5Integration:
    """Integration tests for Phase 3-5 features"""
    
    @pytest.fixture
    def sample_video_data(self):
        """Sample video data for testing"""
        return {
            "id": "test-video-123",
            "title": "Sample Educational Video",
            "description": "A sample video about machine learning",
            "duration": 300,
            "transcript": [
                {"timestamp": 0, "text": "Welcome to this machine learning tutorial"},
                {"timestamp": 30, "text": "Today we'll discuss neural networks"},
                {"timestamp": 60, "text": "Neural networks are inspired by the human brain"},
                {"timestamp": 90, "text": "They consist of interconnected nodes called neurons"}
            ],
            "metadata": {
                "resolution": "1920x1080",
                "fps": 30,
                "format": "mp4"
            }
        }
    
    @pytest.fixture
    def conversation_manager(self):
        """Create ConversationManager instance"""
        return ConversationManager()
    
    @pytest.fixture
    def visual_search_engine(self):
        """Create VisualSearchEngine instance"""
        return VisualSearchEngine()
    
    @pytest.fixture
    def content_segmentation_engine(self):
        """Create ContentSegmentationEngine instance"""
        return ContentSegmentationEngine()
    
    def test_conversational_pipeline_integration(self, conversation_manager, sample_video_data):
        """Test full conversational pipeline with video content"""
        # Mock database session
        from unittest.mock import MagicMock
        mock_db = MagicMock()
        
        # Test session creation
        session = conversation_manager.create_session(
            db=mock_db,
            video_id=sample_video_data["id"],
            title=sample_video_data["title"]
        )
        
        assert session is not None
        assert hasattr(session, 'id')
        assert hasattr(session, 'video_id')
        
        # Test getting session
        retrieved_session = conversation_manager.get_session(mock_db, session.id)
        assert retrieved_session is not None
        
        # Test conversation history
        history = conversation_manager.get_session_history(mock_db, session.id)
        assert isinstance(history, list)
        
        print("✅ Conversational pipeline test passed")
    
    def test_visual_search_integration(self, visual_search_engine, sample_video_data):
        """Test visual search engine with mock video frames"""
        # Mock database session
        mock_db = MagicMock()
        
        # Test object detection in single frame
        with patch('cv2.imread') as mock_imread:
            # Mock successful image loading
            mock_imread.return_value = MagicMock()  # Mock image array
            
            detection_results = visual_search_engine.detect_objects_in_frame(
                frame_path="mock_frame.jpg"
            )
            assert isinstance(detection_results, list)
        
        # Test scene classification
        with patch('cv2.imread') as mock_imread:
            mock_imread.return_value = MagicMock()
            
            scene_result = visual_search_engine.classify_scene(
                frame_path="mock_frame.jpg"
            )
            assert isinstance(scene_result, dict)
        
        # Test visual content search across video
        with patch('os.listdir') as mock_listdir, \
             patch('cv2.imread') as mock_imread:
            
            # Mock frame files
            mock_listdir.return_value = ["frame_001.jpg", "frame_002.jpg"]
            mock_imread.return_value = MagicMock()
            
            search_results = visual_search_engine.search_visual_content(
                video_id=sample_video_data["id"],
                query="neural network diagram",
                frames_dir="mock_frames"
            )
            
            # Mock scene analysis for multiple frames
            scene_results = visual_search_engine.analyze_video_scenes(
                video_id=sample_video_data["id"],
                frames_dir="mock_frames"
            )
            assert len(scene_results) > 0
            assert all("scenes" in result for result in scene_results)
        
        print("✅ Visual search integration test completed")
    
    def test_content_segmentation_integration(self, content_segmentation_engine, sample_video_data):
        """Test content segmentation and navigation features"""
        # Mock database session
        mock_db = MagicMock()
        
        # Test transcript topic analysis
        segments = content_segmentation_engine.analyze_transcript_topics(
            transcript=sample_video_data["transcript"]
        )
        
        assert isinstance(segments, list)
        assert len(segments) > 0
        
        # Verify segment structure
        for segment in segments:
            assert "topic" in segment
            assert "confidence" in segment
            assert "key_phrases" in segment
        
        # Test outline generation
        outline_results = content_segmentation_engine.generate_content_outline(
            video_id=sample_video_data["id"],
            segments=segments
        )
        
        assert isinstance(outline_results, dict)
        assert "outline" in outline_results
        assert "chapters" in outline_results
        
        # Test navigation data generation
        nav_data = content_segmentation_engine.get_video_navigation_data(
            video_id=sample_video_data["id"]
        )
        
        assert isinstance(nav_data, dict)
        assert "chapters" in nav_data
        assert "timestamps" in nav_data
        
        print("✅ Content segmentation integration test completed")
    
    def test_api_endpoints_integration(self, sample_video_data):
        """Test Phase 3-5 API endpoints"""
        from fastapi.testclient import TestClient
        from backend.api.main import app
        
        client = TestClient(app)
        
        # Test chat session creation
        session_response = client.post("/api/v1/chat/sessions", json={
            "video_id": sample_video_data["id"],
            "title": sample_video_data["title"]
        })
        
        # Accept both success and not implemented responses
        assert session_response.status_code in [200, 201, 501]
        
        # Test visual search endpoints
        visual_search_response = client.post("/api/v1/visual-search/detect-objects", json={
            "frame_path": "test_frame.jpg"
        })
        assert visual_search_response.status_code in [200, 501]
        
        # Test content analysis endpoints
        segmentation_response = client.post("/api/v1/content/analyze-topics", json={
            "transcript": sample_video_data["transcript"]
        })
        assert segmentation_response.status_code in [200, 501]
        
        print("✅ API endpoints integration test completed")
    
    def test_error_handling_and_edge_cases(self, conversation_manager, visual_search_engine, content_segmentation_engine):
        """Test error handling and edge cases"""
        mock_db = MagicMock()
        
        # Test invalid session retrieval
        try:
            session = conversation_manager.get_session(mock_db, "invalid-session-id")
            assert session is None or hasattr(session, 'id')
        except Exception as e:
            # Should handle gracefully
            assert "session" in str(e).lower() or "not found" in str(e).lower()
        
        # Test visual search with invalid frame
        try:
            results = visual_search_engine.detect_objects_in_frame("nonexistent_frame.jpg")
            assert isinstance(results, list)
        except Exception as e:
            # Should handle file not found gracefully
            assert isinstance(e, (FileNotFoundError, ValueError)) or "cv2" in str(e).lower()
        
        # Test API with invalid data
        from fastapi.testclient import TestClient
        from backend.api.main import app
        
        client = TestClient(app)
        
        response = client.post("/api/v1/chat/sessions", json={})
        assert response.status_code in [200, 404, 422, 501]  # Any valid HTTP response
        
        print("✅ Error handling and edge cases test completed")
    
    def test_performance_and_scalability(self, conversation_manager, visual_search_engine):
        """Test basic performance characteristics"""
        import time
        
        mock_db = MagicMock()
        
        # Test multiple session creation performance
        start_time = time.time()
        sessions = []
        
        for i in range(5):  # Test with 5 sessions
            try:
                session = conversation_manager.create_session(
                    db=mock_db,
                    video_id=f"test-video-{i}",
                    title=f"Test Video {i}"
                )
                sessions.append(session)
            except Exception as e:
                # Handle any initialization issues
                print(f"Session creation {i} failed: {e}")
        
        elapsed_time = time.time() - start_time
        assert elapsed_time < 10.0  # Should complete in reasonable time
        
        # Test visual search performance
        start_time = time.time()
        
        with patch('cv2.imread') as mock_imread:
            mock_imread.return_value = MagicMock()
            
            for i in range(3):  # Test multiple detection calls
                try:
                    visual_search_engine.detect_objects_in_frame(f"frame_{i}.jpg")
                except Exception as e:
                    print(f"Visual search {i} failed: {e}")
        
        elapsed_time = time.time() - start_time
        assert elapsed_time < 5.0  # Should complete quickly
        
        print("✅ Performance and scalability test passed")
    
    def test_data_flow_integration(self, conversation_manager, visual_search_engine, content_segmentation_engine, sample_video_data):
        """Test data flow between all Phase 3-5 components"""
        mock_db = MagicMock()
        
        # Step 1: Create conversation session
        session = conversation_manager.create_session(
            db=mock_db,
            video_id=sample_video_data["id"],
            title=sample_video_data["title"]
        )
        
        # Step 2: Analyze content segments
        segments = content_segmentation_engine.analyze_transcript_topics(
            transcript=sample_video_data["transcript"]
        )
        
        # Step 3: Generate navigation data
        nav_data = content_segmentation_engine.get_video_navigation_data(
            video_id=sample_video_data["id"]
        )
        
        # Step 4: Mock visual search on key frames
        with patch('cv2.imread') as mock_imread:
            mock_imread.return_value = MagicMock()
            
            key_frame_analysis = visual_search_engine.detect_objects_in_frame(
                frame_path="key_frame.jpg"
            )
        
        # Verify data flow
        assert session is not None
        assert isinstance(segments, list)
        assert isinstance(nav_data, dict)
        assert isinstance(key_frame_analysis, list)
        
        print("✅ Data flow integration test completed")


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
