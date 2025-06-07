# Content Segmentation Engine for Phase 5: Topic Analysis and Navigation

import re
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from backend.database.models import Video, TranscriptChunk, TopicSegment, ContentOutline, NavigationEvent
from collections import Counter
import json

class ContentSegmentationEngine:
    """
    Analyzes video content to identify topic segments, generate outlines,
    and create navigation events for enhanced user experience.
    """
    
    def __init__(self):
        self.min_segment_duration = 30.0  # Minimum segment duration in seconds
        self.max_segment_duration = 300.0  # Maximum segment duration in seconds
        self.topic_change_threshold = 0.7  # Threshold for detecting topic changes
        
    def analyze_transcript_topics(self, db: Session, video_id: int) -> List[Dict[str, Any]]:
        """
        Analyze transcript to identify topic segments.
        """
        # Get all transcript chunks for the video
        transcript_chunks = db.query(TranscriptChunk).filter(
            TranscriptChunk.video_id == video_id
        ).order_by(TranscriptChunk.start_time).all()
        
        if not transcript_chunks:
            return []
        
        # Extract text and timestamps
        texts = [chunk.text for chunk in transcript_chunks]
        timestamps = [(chunk.start_time, chunk.end_time) for chunk in transcript_chunks]
        
        # Perform topic segmentation
        topic_segments = self._segment_by_topics(texts, timestamps)
        
        return topic_segments
    
    def _segment_by_topics(self, texts: List[str], timestamps: List[Tuple[float, float]]) -> List[Dict[str, Any]]:
        """
        Segment text into topic-based segments using keyword analysis and semantic similarity.
        """
        segments = []
        current_segment = {
            'start_time': timestamps[0][0],
            'end_time': timestamps[0][1],
            'texts': [texts[0]],
            'keywords': set()
        }
        
        for i in range(1, len(texts)):
            # Extract keywords from current and previous text
            current_keywords = self._extract_keywords(texts[i])
            prev_keywords = self._extract_keywords(' '.join(current_segment['texts'][-3:]))  # Last 3 chunks
            
            # Calculate topic similarity
            similarity = self._calculate_topic_similarity(current_keywords, prev_keywords)
            
            # Check for topic change
            time_duration = timestamps[i][0] - current_segment['start_time']
            
            if (similarity < self.topic_change_threshold and 
                time_duration >= self.min_segment_duration) or \
               time_duration >= self.max_segment_duration:
                
                # Finalize current segment
                current_segment['end_time'] = timestamps[i-1][1]
                current_segment['topic_summary'] = self._generate_topic_summary(current_segment['texts'])
                current_segment['keywords'] = list(current_segment['keywords'])
                current_segment['importance_score'] = self._calculate_importance_score(current_segment)
                
                segments.append(current_segment)
                
                # Start new segment
                current_segment = {
                    'start_time': timestamps[i][0],
                    'end_time': timestamps[i][1],
                    'texts': [texts[i]],
                    'keywords': current_keywords
                }
            else:
                # Continue current segment
                current_segment['end_time'] = timestamps[i][1]
                current_segment['texts'].append(texts[i])
                current_segment['keywords'].update(current_keywords)
        
        # Add final segment
        if current_segment['texts']:
            current_segment['topic_summary'] = self._generate_topic_summary(current_segment['texts'])
            current_segment['keywords'] = list(current_segment['keywords'])
            current_segment['importance_score'] = self._calculate_importance_score(current_segment)
            segments.append(current_segment)
        
        return segments
    
    def _extract_keywords(self, text: str) -> set:
        """Extract keywords from text using simple frequency analysis."""
        # Simple keyword extraction (in production, use more sophisticated NLP)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        
        # Common stop words to remove
        stop_words = {
            'this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 'said', 
            'each', 'which', 'their', 'time', 'about', 'would', 'there', 'could', 
            'other', 'more', 'very', 'what', 'know', 'just', 'first', 'into', 'over', 
            'think', 'also', 'your', 'work', 'life', 'only', 'still', 'should', 
            'after', 'being', 'made', 'before', 'here', 'through', 'when', 'where', 
            'much', 'some', 'these', 'many', 'then', 'them', 'well', 'were'
        }
        
        meaningful_words = {word for word in words if word not in stop_words and len(word) > 3}
        return meaningful_words
    
    def _calculate_topic_similarity(self, keywords1: set, keywords2: set) -> float:
        """Calculate similarity between two sets of keywords."""
        if not keywords1 or not keywords2:
            return 0.0
        
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        return intersection / union if union > 0 else 0.0
    
    def _generate_topic_summary(self, texts: List[str]) -> str:
        """Generate a summary title for a topic segment."""
        # Combine all texts
        combined_text = ' '.join(texts)
        
        # Extract most frequent meaningful words
        keywords = self._extract_keywords(combined_text)
        word_counts = Counter(re.findall(r'\b[a-zA-Z]{4,}\b', combined_text.lower()))
        
        # Get top keywords that appear in our keyword set
        top_keywords = [word for word, count in word_counts.most_common(5) if word in keywords]
        
        if len(top_keywords) >= 2:
            return f"Discussion about {', '.join(top_keywords[:3])}"
        elif len(top_keywords) == 1:
            return f"Topic: {top_keywords[0].title()}"
        else:
            return "General Discussion"
    
    def _calculate_importance_score(self, segment: Dict[str, Any]) -> float:
        """Calculate importance score for a segment based on various factors."""
        # Factors: length, keyword density, uniqueness
        duration = segment['end_time'] - segment['start_time']
        text_length = sum(len(text) for text in segment['texts'])
        keyword_count = len(segment['keywords'])
        
        # Normalize factors
        duration_score = min(duration / 60.0, 1.0)  # Up to 1 minute gets full score
        length_score = min(text_length / 1000.0, 1.0)  # Up to 1000 chars gets full score
        keyword_score = min(keyword_count / 10.0, 1.0)  # Up to 10 keywords gets full score
        
        # Weighted combination
        importance = (duration_score * 0.3 + length_score * 0.4 + keyword_score * 0.3)
        return round(importance, 3)
    
    def create_topic_segments(self, db: Session, video_id: int) -> Dict[str, Any]:
        """
        Create and store topic segments for a video.
        """
        # Analyze transcript topics
        topic_analysis = self.analyze_transcript_topics(db, video_id)
        
        if not topic_analysis:
            return {'segments_created': 0, 'error': 'No transcript data found'}
        
        segments_created = 0
        
        # Store topic segments in database
        for i, segment_data in enumerate(topic_analysis):
            topic_segment = TopicSegment(
                video_id=video_id,
                start_time=segment_data['start_time'],
                end_time=segment_data['end_time'],
                topic_title=segment_data['topic_summary'],
                topic_summary=self._create_detailed_summary(segment_data['texts']),
                keywords=segment_data['keywords'],
                importance_score=segment_data['importance_score']
            )
            
            db.add(topic_segment)
            segments_created += 1
        
        db.commit()
        
        return {
            'segments_created': segments_created,
            'total_duration': topic_analysis[-1]['end_time'] - topic_analysis[0]['start_time'],
            'average_segment_duration': sum(s['end_time'] - s['start_time'] for s in topic_analysis) / len(topic_analysis),
            'segments': [
                {
                    'title': s['topic_summary'],
                    'start_time': s['start_time'],
                    'end_time': s['end_time'],
                    'duration': s['end_time'] - s['start_time'],
                    'importance': s['importance_score']
                }
                for s in topic_analysis
            ]
        }
    
    def _create_detailed_summary(self, texts: List[str]) -> str:
        """Create a more detailed summary of the segment content."""
        combined_text = ' '.join(texts)
        
        # Extract sentences
        sentences = re.split(r'[.!?]+', combined_text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # Return first 2-3 sentences as summary
        summary_sentences = sentences[:3] if len(sentences) >= 3 else sentences
        return '. '.join(summary_sentences) + '.' if summary_sentences else "Content segment"
    
    def generate_content_outline(self, db: Session, video_id: int) -> Dict[str, Any]:
        """
        Generate a hierarchical content outline for the video.
        """
        # Get topic segments
        segments = db.query(TopicSegment).filter(
            TopicSegment.video_id == video_id
        ).order_by(TopicSegment.start_time).all()
        
        if not segments:
            return {'outline_created': False, 'error': 'No topic segments found'}
        
        # Create hierarchical outline
        outline_structure = self._create_hierarchical_outline(segments)
        
        # Store outline in database
        content_outline = ContentOutline(
            video_id=video_id,
            outline_data=outline_structure,
            generated_method='topic_segmentation',
            confidence_score=self._calculate_outline_confidence(segments)
        )
        
        db.add(content_outline)
        db.commit()
        
        return {
            'outline_created': True,
            'outline_id': content_outline.id,
            'total_sections': len(outline_structure['sections']),
            'outline': outline_structure
        }
    
    def _create_hierarchical_outline(self, segments: List[TopicSegment]) -> Dict[str, Any]:
        """Create a hierarchical outline structure from topic segments."""
        outline = {
            'title': 'Video Content Outline',
            'total_duration': segments[-1].end_time - segments[0].start_time if segments else 0,
            'sections': []
        }
        
        # Group segments by importance and similarity
        high_importance_segments = [s for s in segments if s.importance_score >= 0.7]
        medium_importance_segments = [s for s in segments if 0.4 <= s.importance_score < 0.7]
        low_importance_segments = [s for s in segments if s.importance_score < 0.4]
        
        # Create main sections from high importance segments
        main_sections = []
        for segment in high_importance_segments:
            section = {
                'title': segment.topic_title,
                'start_time': segment.start_time,
                'end_time': segment.end_time,
                'duration': segment.end_time - segment.start_time,
                'importance': segment.importance_score,
                'summary': segment.topic_summary,
                'keywords': segment.keywords or [],
                'subsections': []
            }
            main_sections.append(section)
        
        # Add medium importance segments as subsections or standalone sections
        for segment in medium_importance_segments:
            # Try to attach to nearest main section
            attached = False
            for main_section in main_sections:
                time_gap = abs(segment.start_time - main_section['end_time'])
                if time_gap < 60:  # Within 60 seconds
                    main_section['subsections'].append({
                        'title': segment.topic_title,
                        'start_time': segment.start_time,
                        'end_time': segment.end_time,
                        'duration': segment.end_time - segment.start_time,
                        'summary': segment.topic_summary
                    })
                    main_section['end_time'] = max(main_section['end_time'], segment.end_time)
                    attached = True
                    break
            
            if not attached:
                # Create standalone section
                main_sections.append({
                    'title': segment.topic_title,
                    'start_time': segment.start_time,
                    'end_time': segment.end_time,
                    'duration': segment.end_time - segment.start_time,
                    'importance': segment.importance_score,
                    'summary': segment.topic_summary,
                    'keywords': segment.keywords or [],
                    'subsections': []
                })
        
        # Sort sections by start time
        main_sections.sort(key=lambda x: x['start_time'])
        outline['sections'] = main_sections
        
        return outline
    
    def _calculate_outline_confidence(self, segments: List[TopicSegment]) -> float:
        """Calculate confidence score for the generated outline."""
        if not segments:
            return 0.0
        
        # Factors: number of segments, average importance, coverage
        num_segments = len(segments)
        avg_importance = sum(s.importance_score for s in segments) / num_segments
        
        # Confidence based on segment quality and quantity
        segment_score = min(num_segments / 10.0, 1.0)  # Up to 10 segments
        importance_score = avg_importance
        
        confidence = (segment_score * 0.4 + importance_score * 0.6)
        return round(confidence, 3)
    
    def create_navigation_events(self, db: Session, video_id: int) -> Dict[str, Any]:
        """
        Create navigation events for topic changes, scene changes, etc.
        """
        events_created = 0
        
        # Create events from topic segments
        segments = db.query(TopicSegment).filter(
            TopicSegment.video_id == video_id
        ).order_by(TopicSegment.start_time).all()
        
        for segment in segments:
            # Topic change event
            nav_event = NavigationEvent(
                video_id=video_id,
                event_type='topic_change',
                timestamp=segment.start_time,
                description=f"New topic: {segment.topic_title}",
                metadata={
                    'topic_title': segment.topic_title,
                    'importance_score': segment.importance_score,
                    'keywords': segment.keywords or []
                }
            )
            db.add(nav_event)
            events_created += 1
        
        # Create events from transcript analysis (speaker changes, etc.)
        transcript_chunks = db.query(TranscriptChunk).filter(
            TranscriptChunk.video_id == video_id
        ).order_by(TranscriptChunk.start_time).all()
        
        current_speaker = None
        for chunk in transcript_chunks:
            if chunk.speaker and chunk.speaker != current_speaker:
                nav_event = NavigationEvent(
                    video_id=video_id,
                    event_type='speaker_change',
                    timestamp=chunk.start_time,
                    description=f"Speaker: {chunk.speaker}",
                    metadata={'speaker': chunk.speaker}
                )
                db.add(nav_event)
                current_speaker = chunk.speaker
                events_created += 1
        
        db.commit()
        
        return {
            'events_created': events_created,
            'topic_events': len(segments),
            'speaker_events': events_created - len(segments)
        }
    
    def get_video_navigation_data(self, db: Session, video_id: int) -> Dict[str, Any]:
        """
        Get comprehensive navigation data for a video.
        """
        # Get topic segments
        segments = db.query(TopicSegment).filter(
            TopicSegment.video_id == video_id
        ).order_by(TopicSegment.start_time).all()
        
        # Get content outline
        outline = db.query(ContentOutline).filter(
            ContentOutline.video_id == video_id
        ).order_by(ContentOutline.created_at.desc()).first()
        
        # Get navigation events
        events = db.query(NavigationEvent).filter(
            NavigationEvent.video_id == video_id
        ).order_by(NavigationEvent.timestamp).all()
        
        return {
            'video_id': video_id,
            'topic_segments': [
                {
                    'id': segment.id,
                    'title': segment.topic_title,
                    'start_time': segment.start_time,
                    'end_time': segment.end_time,
                    'duration': segment.end_time - segment.start_time,
                    'summary': segment.topic_summary,
                    'keywords': segment.keywords or [],
                    'importance_score': segment.importance_score
                }
                for segment in segments
            ],
            'content_outline': outline.outline_data if outline else None,
            'navigation_events': [
                {
                    'type': event.event_type,
                    'timestamp': event.timestamp,
                    'description': event.description,
                    'metadata': event.metadata
                }
                for event in events
            ],
            'statistics': {
                'total_segments': len(segments),
                'total_events': len(events),
                'outline_available': outline is not None,
                'average_segment_duration': sum(s.end_time - s.start_time for s in segments) / len(segments) if segments else 0
            }
        }
