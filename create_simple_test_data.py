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

def main():
    try:
        from backend.database.models import get_db, Video, TranscriptChunk, VideoFrame
        from sqlalchemy.orm import Session
        
        print("Creating test data for Phase 3-5...")
        
        db = next(get_db())
        
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
        
        print(f"Created test video with ID: {test_video.id}")
        
        # Create sample transcript chunks
        transcript_data = [
            {"start_time": 0.0, "end_time": 30.0, "text": "Welcome to this comprehensive tutorial on machine learning and artificial intelligence. Today we'll explore neural networks and their applications."},
            {"start_time": 30.0, "end_time": 60.0, "text": "Neural networks are computational models inspired by biological neural networks. They consist of interconnected nodes called neurons."},
            {"start_time": 60.0, "end_time": 90.0, "text": "Deep learning is a subset of machine learning that uses neural networks with multiple layers to learn complex patterns."},
            {"start_time": 90.0, "end_time": 120.0, "text": "Convolutional neural networks are particularly effective for image recognition and computer vision tasks."},
            {"start_time": 120.0, "end_time": 150.0, "text": "Natural language processing uses AI to understand and generate human language, enabling chatbots and translation."}
        ]
        
        for i, chunk_data in enumerate(transcript_data):
            chunk = TranscriptChunk(
                video_id=test_video.id,
                text=chunk_data["text"],
                start_time=chunk_data["start_time"],
                end_time=chunk_data["end_time"],
                confidence=0.95,
                speaker=f"Speaker_{i % 2 + 1}",
                created_at=datetime.utcnow()
            )
            db.add(chunk)
        
        print(f"Created {len(transcript_data)} transcript chunks")
        
        # Create sample video frames
        frame_count = 0
        for i in range(0, 301, 30):  # Every 30 seconds
            frame = VideoFrame(
                video_id=test_video.id,
                frame_path=f"./frames/test_video_sample/frame_{i:06d}.jpg",
                timestamp=float(i),
                frame_number=i * 30,
                width=1920,
                height=1080,
                created_at=datetime.utcnow()
            )
            db.add(frame)
            frame_count += 1
        
        print(f"Created {frame_count} video frames")
        
        db.commit()
        
        print("Test data creation complete!")
        print(f"Video ID: {test_video.id}")
        print(f"Transcript chunks: {len(transcript_data)}")
        print(f"Video frames: {frame_count}")
        
        db.close()
        return test_video.id
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    main()
