#!/usr/bin/env python3
"""
Create test data for Phase 3-5 endpoint testing
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.database.models import get_db, Video, TranscriptChunk, VideoFrame
from sqlalchemy.orm import Session

def create_test_video():
    """Create a test video record with transcript and frames"""
    
    db = next(get_db())
    
    try:
        # Create test video
        test_video = Video(
            filename="test_video_sample.mp4",
            original_filename="Sample Video for Testing.mp4",
            file_path="./test_videos/test_video_sample.mp4",
            video_url="https://www.youtube.com/watch?v=sample123",
            duration=300.0,  # 5 minutes
            width=1920,
            height=1080,
            fps=30.0,
            file_size=50000000,  # 50MB
            processed=True,
            transcript_generated=True,
            frames_extracted=True,
            created_at=datetime.utcnow()
        )
        
        db.add(test_video)
        db.commit()
        db.refresh(test_video)
        
        print(f"✅ Created test video with ID: {test_video.id}")
        
        # Create sample transcript chunks
        transcript_data = [
            {"start_time": 0.0, "end_time": 30.0, "text": "Welcome to this comprehensive tutorial on machine learning and artificial intelligence. Today we'll explore neural networks and their applications."},
            {"start_time": 30.0, "end_time": 60.0, "text": "Neural networks are computational models inspired by biological neural networks. They consist of interconnected nodes called neurons."},
            {"start_time": 60.0, "end_time": 90.0, "text": "Deep learning is a subset of machine learning that uses neural networks with multiple layers to learn complex patterns."},
            {"start_time": 90.0, "end_time": 120.0, "text": "Convolutional neural networks are particularly effective for image recognition and computer vision tasks."},
            {"start_time": 120.0, "end_time": 150.0, "text": "Natural language processing uses AI to understand and generate human language, enabling applications like chatbots and translation."},
            {"start_time": 150.0, "end_time": 180.0, "text": "Training neural networks requires large datasets and computational resources, often using GPUs for acceleration."},
            {"start_time": 180.0, "end_time": 210.0, "text": "Overfitting is a common problem where models perform well on training data but poorly on new data."},
            {"start_time": 210.0, "end_time": 240.0, "text": "Regularization techniques help prevent overfitting and improve model generalization."},
            {"start_time": 240.0, "end_time": 270.0, "text": "Transfer learning allows using pre-trained models as starting points for new tasks, saving time and resources."},
            {"start_time": 270.0, "end_time": 300.0, "text": "The future of AI includes developments in quantum computing, neuromorphic chips, and more efficient algorithms."}
        ]
        
        for i, chunk_data in enumerate(transcript_data):
            chunk = TranscriptChunk(
                video_id=test_video.id,
                text=chunk_data["text"],
                start_time=chunk_data["start_time"],
                end_time=chunk_data["end_time"],
                confidence=0.95,
                speaker=f"Speaker_{i % 2 + 1}",  # Alternate between Speaker_1 and Speaker_2
                created_at=datetime.utcnow()
            )
            db.add(chunk)
        
        print(f"✅ Created {len(transcript_data)} transcript chunks")
        
        # Create sample video frames
        for i in range(0, 301, 10):  # Every 10 seconds
            frame = VideoFrame(
                video_id=test_video.id,
                frame_path=f"./frames/test_video_sample/frame_{i:06d}.jpg",
                timestamp=float(i),
                frame_number=i * 30,  # 30 FPS
                width=1920,
                height=1080,
                created_at=datetime.utcnow()
            )
            db.add(frame)
        
        frame_count = len(range(0, 301, 10))
        print(f"✅ Created {frame_count} video frames")
        
        db.commit()
        
        print(f"\n🎉 Test data creation complete!")
        print(f"📊 Summary:")
        print(f"   Video ID: {test_video.id}")
        print(f"   Transcript chunks: {len(transcript_data)}")
        print(f"   Video frames: {frame_count}")
        print(f"   Duration: {test_video.duration} seconds")
        
        return test_video.id
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
        return None
    finally:
        db.close()

def create_additional_test_videos():
    """Create additional test videos for comprehensive testing"""
    
    db = next(get_db())
    
    try:
        # Video 2: Tech presentation
        video2 = Video(
            filename="tech_presentation.mp4",
            original_filename="Technology Presentation.mp4", 
            file_path="./test_videos/tech_presentation.mp4",
            duration=180.0,  # 3 minutes
            width=1280,
            height=720,
            fps=25.0,
            file_size=30000000,
            processed=True,
            transcript_generated=True,
            frames_extracted=True
        )
        
        # Video 3: Educational content
        video3 = Video(
            filename="educational_content.mp4",
            original_filename="Educational Content.mp4",
            file_path="./test_videos/educational_content.mp4", 
            duration=420.0,  # 7 minutes
            width=1920,
            height=1080,
            fps=30.0,
            file_size=75000000,
            processed=True,
            transcript_generated=True,
            frames_extracted=True
        )
        
        db.add_all([video2, video3])
        db.commit()
        
        print(f"✅ Created additional test videos")
        print(f"   Video 2 ID: {video2.id}")
        print(f"   Video 3 ID: {video3.id}")
        
        return [video2.id, video3.id]
        
    except Exception as e:
        print(f"❌ Error creating additional videos: {e}")
        db.rollback()
        return []
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 50)
    print("CREATING TEST DATA FOR PHASE 3-5")
    print("=" * 50)
    
    # Create main test video
    primary_video_id = create_test_video()
    
    if primary_video_id:
        # Create additional videos
        additional_ids = create_additional_test_videos()
        
        print(f"\n🎯 Test data ready for API testing!")
        print(f"Primary test video ID: {primary_video_id}")
        if additional_ids:
            print(f"Additional video IDs: {additional_ids}")
        
        print(f"\n📋 You can now test endpoints with:")
        print(f"   Video ID: {primary_video_id}")
        print(f"   Session creation, chat, visual search, content analysis")
    else:
        print("❌ Failed to create test data")
