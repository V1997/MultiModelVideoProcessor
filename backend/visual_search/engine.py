# Visual Search Engine for Phase 4: Object Detection and Scene Classification

import cv2
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from backend.database.models import Video, VideoFrame, ObjectDetection, SceneClassification
import json
import re
from pathlib import Path

class VisualSearchEngine:
    """
    Visual search engine that performs object detection and scene classification
    on video frames and enables natural language queries.
    """
    
    def __init__(self):
        self.object_detector = None
        self.scene_classifier = None
        self.setup_models()
    
    def setup_models(self):
        """Initialize object detection and scene classification models."""
        try:
            # For now, we'll use a simple approach
            # In production, you would load YOLO, detectron2, or similar models
            print("🤖 Initializing visual search models...")
            print("📦 Object Detection: OpenCV DNN (YOLO-like)")
            print("🎬 Scene Classification: Pre-trained CNN")
            
            # Placeholder for actual model loading
            self.object_detector = "opencv_dnn"  # Would be actual model
            self.scene_classifier = "resnet_scenes"  # Would be actual model
            
        except Exception as e:
            print(f"⚠️ Warning: Could not load all visual models: {e}")
    
    def detect_objects_in_frame(self, frame_path: str, confidence_threshold: float = 0.5) -> List[Dict]:
        """
        Detect objects in a single frame.
        Returns list of detected objects with bounding boxes and confidence scores.
        """
        try:
            # Load the frame
            frame = cv2.imread(frame_path)
            if frame is None:
                return []
            
            # For demonstration, we'll simulate object detection
            # In production, you would use actual models like YOLO, detectron2, etc.
            detected_objects = self._simulate_object_detection(frame, confidence_threshold)
            
            return detected_objects
            
        except Exception as e:
            print(f"Error detecting objects in frame {frame_path}: {e}")
            return []
    
    def _simulate_object_detection(self, frame: np.ndarray, confidence_threshold: float) -> List[Dict]:
        """
        Simulate object detection for demonstration purposes.
        In production, replace with actual model inference.
        """
        height, width = frame.shape[:2]
        
        # Simulate detection of common objects
        simulated_objects = [
            {
                'class': 'person',
                'confidence': 0.85,
                'bbox': [0.2 * width, 0.1 * height, 0.3 * width, 0.7 * height],
                'attributes': {'clothing_color': 'blue', 'pose': 'standing'}
            },
            {
                'class': 'car',
                'confidence': 0.72,
                'bbox': [0.6 * width, 0.4 * height, 0.35 * width, 0.3 * height],
                'attributes': {'color': 'red', 'type': 'sedan'}
            },
            {
                'class': 'text',
                'confidence': 0.68,
                'bbox': [0.1 * width, 0.8 * height, 0.8 * width, 0.1 * height],
                'attributes': {'text_type': 'title', 'readable': True}
            }
        ]
        
        # Filter by confidence threshold
        return [obj for obj in simulated_objects if obj['confidence'] >= confidence_threshold]
    
    def classify_scene(self, frame_path: str) -> Dict[str, Any]:
        """
        Classify the scene/setting of a frame.
        Returns scene type with confidence and description.
        """
        try:
            frame = cv2.imread(frame_path)
            if frame is None:
                return {}
            
            # Simulate scene classification
            # In production, use models like Places365, etc.
            scene_classification = self._simulate_scene_classification(frame)
            
            return scene_classification
            
        except Exception as e:
            print(f"Error classifying scene in frame {frame_path}: {e}")
            return {}
    
    def _simulate_scene_classification(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Simulate scene classification for demonstration.
        In production, replace with actual model inference.
        """
        # Analyze basic properties of the frame
        mean_brightness = np.mean(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        
        # Simulate different scene types based on simple heuristics
        if mean_brightness > 150:
            scene_type = "outdoor"
            confidence = 0.78
            description = "Bright outdoor scene, likely daytime"
        elif mean_brightness > 100:
            scene_type = "indoor"
            confidence = 0.82
            description = "Well-lit indoor environment"
        else:
            scene_type = "indoor_dim"
            confidence = 0.65
            description = "Dimly lit indoor scene or nighttime"
        
        return {
            'scene_type': scene_type,
            'confidence': confidence,
            'description': description,
            'features': {
                'brightness': float(mean_brightness),
                'lighting': 'natural' if mean_brightness > 120 else 'artificial'
            }
        }
    
    def process_video_frames(self, db: Session, video_id: int, 
                           confidence_threshold: float = 0.5) -> Dict[str, int]:
        """
        Process all frames of a video for object detection and scene classification.
        """
        video = db.query(Video).filter(Video.id == video_id).first()
        if not video:
            raise ValueError(f"Video {video_id} not found")
        
        frames = db.query(VideoFrame).filter(VideoFrame.video_id == video_id).all()
        
        processed_count = {
            'objects_detected': 0,
            'scenes_classified': 0,
            'frames_processed': 0
        }
        
        for frame in frames:
            try:
                # Detect objects in frame
                detected_objects = self.detect_objects_in_frame(
                    frame.frame_path, confidence_threshold
                )
                
                # Store object detections
                for obj in detected_objects:
                    object_detection = ObjectDetection(
                        video_id=video_id,
                        frame_id=frame.id,
                        object_class=obj['class'],
                        confidence=obj['confidence'],
                        bbox_x=obj['bbox'][0],
                        bbox_y=obj['bbox'][1],
                        bbox_width=obj['bbox'][2],
                        bbox_height=obj['bbox'][3],
                        attributes=obj.get('attributes', {})
                    )
                    db.add(object_detection)
                    processed_count['objects_detected'] += 1
                
                # Classify scene
                scene_info = self.classify_scene(frame.frame_path)
                if scene_info:
                    scene_classification = SceneClassification(
                        video_id=video_id,
                        start_time=frame.timestamp,
                        end_time=frame.timestamp + 1.0,  # Assume 1-second duration
                        scene_type=scene_info['scene_type'],
                        confidence=scene_info['confidence'],
                        description=scene_info.get('description'),
                        features=scene_info.get('features', {})
                    )
                    db.add(scene_classification)
                    processed_count['scenes_classified'] += 1
                
                processed_count['frames_processed'] += 1
                
            except Exception as e:
                print(f"Error processing frame {frame.id}: {e}")
                continue
        
        db.commit()
        return processed_count
    
    def parse_visual_query(self, query: str) -> Dict[str, Any]:
        """
        Parse natural language visual queries into structured search parameters.
        """
        query_lower = query.lower()
        
        # Extract colors
        colors = ['red', 'blue', 'green', 'yellow', 'black', 'white', 'brown', 'gray', 'orange', 'purple']
        found_colors = [color for color in colors if color in query_lower]
        
        # Extract objects
        objects = ['person', 'car', 'truck', 'bus', 'motorcycle', 'bicycle', 'dog', 'cat', 'bird', 
                  'chair', 'table', 'computer', 'phone', 'book', 'bottle', 'cup', 'bowl']
        found_objects = [obj for obj in objects if obj in query_lower]
        
        # Extract scenes
        scenes = ['outdoor', 'indoor', 'office', 'street', 'park', 'building', 'room', 'kitchen', 'bedroom']
        found_scenes = [scene for scene in scenes if scene in query_lower]
        
        # Extract attributes
        attributes = {
            'size': ['big', 'large', 'small', 'tiny', 'huge'],
            'position': ['left', 'right', 'center', 'top', 'bottom', 'corner'],
            'action': ['walking', 'running', 'sitting', 'standing', 'moving', 'still']        }
        
        found_attributes = {}
        for attr_type, attr_values in attributes.items():
            found = [val for val in attr_values if val in query_lower]
            if found:
                found_attributes[attr_type] = found
        
        return {
            'colors': found_colors,
            'objects': found_objects,
            'scenes': found_scenes,
            'attributes': found_attributes,
            'original_query': query
        }

    def search_visual_content(self, db: Session, video_id: int, query: str, 
                            confidence_threshold: float = 0.3) -> Dict[str, Any]:
        """
        Search for visual content based on natural language query.
        """
        parsed_query = self.parse_visual_query(query)
        
        # Build database query for objects
        object_results = []
        if parsed_query['objects'] or parsed_query['colors']:
            object_query = db.query(ObjectDetection).filter(
                ObjectDetection.video_id == video_id,
                ObjectDetection.confidence >= confidence_threshold
            )
            
            # Filter by object classes
            if parsed_query['objects']:
                object_query = object_query.filter(
                    ObjectDetection.object_class.in_(parsed_query['objects'])
                )
            
            objects = object_query.all()
            
            for obj in objects:
                # Check color attributes if specified
                if parsed_query['colors']:
                    obj_attributes = obj.attributes or {}
                    obj_colors = [obj_attributes.get('color', '').lower(), 
                                obj_attributes.get('clothing_color', '').lower()]
                    
                    if not any(color in obj_colors for color in parsed_query['colors']):
                        continue
                
                # Get frame info
                frame = db.query(VideoFrame).filter(VideoFrame.id == obj.frame_id).first()
                
                object_results.append({
                    'type': 'object',
                    'object_class': obj.object_class,
                    'confidence': obj.confidence,
                    'timestamp': frame.timestamp if frame else 0,
                    'frame_path': frame.frame_path if frame else '',
                    'bounding_box': {
                        'x': obj.bbox_x,
                        'y': obj.bbox_y,
                        'width': obj.bbox_width,
                        'height': obj.bbox_height
                    },
                    'attributes': obj.attributes
                })
        
        # Build database query for scenes
        scene_results = []
        if parsed_query['scenes']:
            scenes = db.query(SceneClassification).filter(
                SceneClassification.video_id == video_id,
                SceneClassification.scene_type.in_(parsed_query['scenes']),
                SceneClassification.confidence >= confidence_threshold
            ).all()
            
            for scene in scenes:
                scene_results.append({
                    'type': 'scene',
                    'scene_type': scene.scene_type,
                    'confidence': scene.confidence,
                    'start_time': scene.start_time,
                    'end_time': scene.end_time,
                    'description': scene.description,
                    'features': scene.features
                })
        
        # Combine and sort results by confidence and timestamp
        all_results = object_results + scene_results
        all_results.sort(key=lambda x: (-x['confidence'], x.get('timestamp', x.get('start_time', 0))))
        
        return {
            'query': query,
            'parsed_query': parsed_query,
            'results': all_results,
            'total_results': len(all_results),
            'object_matches': len(object_results),
            'scene_matches': len(scene_results)
        }
    
    def get_visual_timeline(self, db: Session, video_id: int) -> Dict[str, Any]:
        """
        Generate a visual timeline showing detected objects and scenes over time.
        """
        # Get all objects for the video
        objects = db.query(ObjectDetection).join(VideoFrame).filter(
            ObjectDetection.video_id == video_id
        ).order_by(VideoFrame.timestamp).all()
        
        # Get all scenes for the video
        scenes = db.query(SceneClassification).filter(
            SceneClassification.video_id == video_id
        ).order_by(SceneClassification.start_time).all()
        
        # Build timeline
        timeline_events = []
        
        # Add object detections
        for obj in objects:
            frame = db.query(VideoFrame).filter(VideoFrame.id == obj.frame_id).first()
            if frame:
                timeline_events.append({
                    'timestamp': frame.timestamp,
                    'type': 'object_detection',
                    'object_class': obj.object_class,
                    'confidence': obj.confidence,
                    'attributes': obj.attributes
                })
        
        # Add scene classifications
        for scene in scenes:
            timeline_events.append({
                'timestamp': scene.start_time,
                'type': 'scene_change',
                'scene_type': scene.scene_type,
                'confidence': scene.confidence,
                'description': scene.description,
                'duration': scene.end_time - scene.start_time
            })
        
        # Sort by timestamp
        timeline_events.sort(key=lambda x: x['timestamp'])
        
        return {
            'video_id': video_id,
            'timeline': timeline_events,
            'total_events': len(timeline_events),
            'unique_objects': len(set(obj.object_class for obj in objects)),
            'unique_scenes': len(set(scene.scene_type for scene in scenes))
        }
    
    def get_object_statistics(self, db: Session, video_id: int) -> Dict[str, Any]:
        """
        Get statistics about detected objects in the video.
        """
        objects = db.query(ObjectDetection).filter(
            ObjectDetection.video_id == video_id
        ).all()
        
        if not objects:
            return {'total_objects': 0}
        
        # Count by class
        class_counts = {}
        confidence_scores = []
        
        for obj in objects:
            class_counts[obj.object_class] = class_counts.get(obj.object_class, 0) + 1
            confidence_scores.append(obj.confidence)
        
        # Calculate statistics
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        return {
            'total_objects': len(objects),
            'unique_classes': len(class_counts),
            'class_counts': class_counts,
            'average_confidence': avg_confidence,
            'confidence_range': {
                'min': min(confidence_scores),
                'max': max(confidence_scores)
            },
            'most_common_object': max(class_counts.items(), key=lambda x: x[1])[0] if class_counts else None
        }
