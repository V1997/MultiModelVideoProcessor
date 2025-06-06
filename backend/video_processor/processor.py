import cv2
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import ffmpeg
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self, upload_dir: str = "./uploads", processed_dir: str = "./processed", frames_dir: str = "./frames"):
        self.upload_dir = Path(upload_dir)
        self.processed_dir = Path(processed_dir)
        self.frames_dir = Path(frames_dir)
        
        # Create directories if they don't exist
        for dir_path in [self.upload_dir, self.processed_dir, self.frames_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_video_metadata(self, video_path: str) -> Dict:
        """Extract video metadata using OpenCV and ffmpeg"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise ValueError(f"Could not open video file: {video_path}")
            
            # Get basic properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            # Get file size
            file_size = os.path.getsize(video_path)
            
            metadata = {
                "duration": duration,
                "fps": fps,
                "width": width,
                "height": height,
                "frame_count": frame_count,
                "file_size": file_size
            }
            
            logger.info(f"Extracted metadata for {video_path}: {metadata}")
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata from {video_path}: {str(e)}")
            raise
    
    def extract_frames(self, video_path: str, video_id: int, fps: float = 1.0) -> List[Dict]:
        """Extract frames from video at specified fps"""
        try:
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise ValueError(f"Could not open video file: {video_path}")
            
            video_fps = cap.get(cv2.CAP_PROP_FPS)
            frame_interval = int(video_fps / fps) if fps > 0 else 30
            
            frames_data = []
            frame_number = 0
            extracted_count = 0
            
            # Create video-specific frames directory
            video_frames_dir = self.frames_dir / str(video_id)
            video_frames_dir.mkdir(parents=True, exist_ok=True)
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                if frame_number % frame_interval == 0:
                    # Calculate timestamp
                    timestamp = frame_number / video_fps
                    
                    # Save frame
                    frame_filename = f"frame_{extracted_count:06d}_{timestamp:.2f}s.jpg"
                    frame_path = video_frames_dir / frame_filename
                    
                    # Convert BGR to RGB for saving
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_image = Image.fromarray(frame_rgb)
                    pil_image.save(frame_path, "JPEG", quality=85)
                    
                    frames_data.append({
                        "frame_path": str(frame_path),
                        "timestamp": timestamp,
                        "frame_number": frame_number,
                        "width": frame.shape[1],
                        "height": frame.shape[0]
                    })
                    
                    extracted_count += 1
                
                frame_number += 1
            
            cap.release()
            
            logger.info(f"Extracted {extracted_count} frames from video {video_id}")
            return frames_data
            
        except Exception as e:
            logger.error(f"Error extracting frames from {video_path}: {str(e)}")
            raise
    
    def process_uploaded_file(self, file_path: str, original_filename: str) -> Tuple[str, Dict]:
        """Process uploaded video file"""
        try:
            # Generate unique filename
            file_extension = Path(original_filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            processed_path = self.processed_dir / unique_filename
            
            # Copy file to processed directory (in production, you might want to move or link)
            import shutil
            shutil.copy2(file_path, processed_path)
            
            # Extract metadata
            metadata = self.get_video_metadata(str(processed_path))
            
            return str(processed_path), metadata
            
        except Exception as e:
            logger.error(f"Error processing uploaded file {original_filename}: {str(e)}")
            raise
    
    def validate_video_file(self, file_path: str, max_size_mb: int = 500) -> bool:
        """Validate video file format and size"""
        try:
            # Check file size
            file_size = os.path.getsize(file_path)
            max_size_bytes = max_size_mb * 1024 * 1024
            
            if file_size > max_size_bytes:
                logger.warning(f"File too large: {file_size} bytes > {max_size_bytes} bytes")
                return False
            
            # Try to open with OpenCV
            cap = cv2.VideoCapture(file_path)
            is_valid = cap.isOpened()
            cap.release()
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating video file {file_path}: {str(e)}")
            return False
    
    def cleanup_temp_files(self, file_paths: List[str]):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up temporary file: {file_path}")
            except Exception as e:
                logger.warning(f"Could not clean up file {file_path}: {str(e)}")

# Utility functions
def get_supported_formats() -> List[str]:
    """Get list of supported video formats"""
    return ['mp4', 'avi', 'mov', 'mkv', 'webm', 'flv', 'm4v']

def is_supported_format(filename: str) -> bool:
    """Check if file format is supported"""
    extension = Path(filename).suffix.lower().lstrip('.')
    return extension in get_supported_formats()
