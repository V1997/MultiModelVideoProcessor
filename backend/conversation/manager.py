# Conversation Manager for Phase 3: Context-Aware Chat System

import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from sqlalchemy.orm import Session
from backend.database.models import ChatSession, ChatMessage, ConversationContext, Video, TranscriptChunk, VideoFrame
from backend.embedding_engine.rag import MultimodalRAG
import json
import re

class ConversationManager:
    """
    Manages context-aware conversations with video content.
    Maintains conversation history, references timestamps, and provides enriched responses.
    """
    
    def __init__(self, rag_system: MultimodalRAG):
        self.rag_system = rag_system
        self.max_context_messages = 10  # Keep last 10 messages for context
        
    def create_session(self, db: Session, video_id: int, title: str = None) -> ChatSession:
        """Create a new chat session for a video."""
        session_id = str(uuid.uuid4())
        
        chat_session = ChatSession(
            video_id=video_id,
            session_id=session_id,
            title=title or f"Chat Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}"
        )
        
        db.add(chat_session)
        db.commit()
        db.refresh(chat_session)
        
        # Initialize conversation context
        context = ConversationContext(
            session_id=chat_session.id,
            key_topics=[],
            referenced_segments=[]
        )
        db.add(context)
        db.commit()
        
        return chat_session
    
    def get_session(self, db: Session, session_id: str) -> Optional[ChatSession]:
        """Retrieve a chat session by session ID."""
        return db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    
    def get_conversation_context(self, db: Session, session_id: int) -> List[Dict]:
        """Get recent conversation history for context."""
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at.desc()).limit(self.max_context_messages).all()
        
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp_references": msg.timestamp_references,
                "frame_references": msg.frame_references,
                "created_at": msg.created_at.isoformat()
            }
            for msg in reversed(messages)
        ]

    def extract_timestamp_references(self, text: str) -> List[float]:
        """Extract timestamp references from text (e.g., "at 2:30", "around 1:45")."""
        # Pattern to match timestamps like "2:30", "1:45:30", "0:45"
        timestamp_pattern = r'(?:at\s+|around\s+)?(\d{1,2}):(\d{2})(?::(\d{2}))?'
        matches = re.findall(timestamp_pattern, text, re.IGNORECASE)
        timestamps = []
        for match in matches:
            minutes = int(match[0])
            seconds = int(match[1])
            hours = int(match[2]) if match[2] else 0
            total_seconds = hours * 3600 + minutes * 60 + seconds
            timestamps.append(float(total_seconds))
        return timestamps
    
    async def find_relevant_segments(self, db: Session, video_id: int, query: str, 
                                     context_messages: List[Dict]) -> List[Dict]:
        """Find relevant transcript segments and frames for the query."""
        # Use RAG system to find relevant content
        rag_results = await self.rag_system.process_query(query, video_ids=[video_id])
        
        # Extract timestamps from context messages
        context_timestamps = []
        for msg in context_messages:
            if msg.get('timestamp_references'):
                context_timestamps.extend(msg['timestamp_references'])
        
        # Combine RAG results with context
        relevant_segments = []
        for result in rag_results.get('transcript_results', []):
            segment_info = {
                'text': result['text'],
                'start_time': result['start_time'],
                'end_time': result['end_time'],
                'confidence': result.get('confidence', 0.0),
                'source': 'transcript'
            }
            relevant_segments.append(segment_info)
        
        # Add frame results
        for result in rag_results.get('frame_results', []):
            frame_info = {
                'frame_path': result['frame_path'],
                'timestamp': result['timestamp'],
                'confidence': result.get('confidence', 0.0),
                'source': 'frame'
            }
            relevant_segments.append(frame_info)
        
        return relevant_segments

    async def generate_enhanced_response(self, db: Session, session_id: str, user_query: str, 
                                         video_id: int) -> Dict[str, Any]:
        """Generate a context-aware response with multimedia enhancements."""
        session = self.get_session(db, session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Get conversation context
        context_messages = self.get_conversation_context(db, session.id)
        
        # Find relevant segments
        relevant_segments = await self.find_relevant_segments(db, video_id, user_query, context_messages)
        
        # Extract timestamp references from user query
        timestamp_refs = self.extract_timestamp_references(user_query)

        # Generate response using RAG system with context
        context_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context_messages[-5:]])
        enhanced_query = f"Context: {context_text}\n\nUser Query: {user_query}"
        
        # Use await for the async method
        rag_response = await self.rag_system.process_query(enhanced_query, video_ids=[video_id])
        
        # Format response with enhancements
        response_content = rag_response.get('response', '')
        
        # Add timestamp citations
        cited_timestamps = []
        frame_references = []
        
        for segment in relevant_segments:
            if segment['source'] == 'transcript':
                cited_timestamps.append({
                    'timestamp': segment['start_time'],
                    'text': segment['text'][:100] + "..." if len(segment['text']) > 100 else segment['text'],
                    'confidence': segment['confidence']
                })
            elif segment['source'] == 'frame':
                frame_references.append({
                    'timestamp': segment['timestamp'],
                    'frame_path': segment['frame_path'],
                    'confidence': segment['confidence']
                })
        
        # Calculate overall confidence
        confidence_scores = [seg['confidence'] for seg in relevant_segments]
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        
        # Save user message
        user_message = ChatMessage(
            session_id=session.id,
            role="user",
            content=user_query,
            timestamp_references=timestamp_refs,
            created_at=datetime.utcnow()
        )
        db.add(user_message)
        
        # Save assistant response
        assistant_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=response_content,
            timestamp_references=[ts['timestamp'] for ts in cited_timestamps],
            frame_references=[fr['frame_path'] for fr in frame_references],
            confidence_score=overall_confidence,
            created_at=datetime.utcnow()
        )
        db.add(assistant_message)
          # Update conversation context
        self.update_conversation_context(db, session.id, user_query, response_content, 
                                       cited_timestamps, frame_references)
        
        db.commit()
        
        return {
            'message_id': str(assistant_message.id),
            'response': response_content,
            'confidence': overall_confidence,
            'timestamp_citations': cited_timestamps
        }
    
    def update_conversation_context(self, db: Session, session_id: int, user_query: str, 
                                  response: str, timestamps: List[Dict], frames: List[Dict]):
        """Update conversation context with new information."""
        context = db.query(ConversationContext).filter(
            ConversationContext.session_id == session_id
        ).first()
        
        if not context:
            return
        
        # Extract topics from query and response
        topics = self.extract_topics(user_query + " " + response)
        
        # Update key topics
        current_topics = context.key_topics or []
        for topic in topics:
            if topic not in current_topics:
                current_topics.append(topic)
        
        # Update referenced segments
        current_segments = context.referenced_segments or []
        for ts in timestamps:
            segment_ref = {
                'timestamp': ts['timestamp'],
                'text': ts['text'],
                'referenced_at': datetime.utcnow().isoformat()
            }
            current_segments.append(segment_ref)
        
        # Keep only recent segments (last 20)
        current_segments = current_segments[-20:]
        
        context.key_topics = current_topics
        context.referenced_segments = current_segments
        context.last_updated = datetime.utcnow()
        
        db.commit()
    
    def extract_topics(self, text: str) -> List[str]:
        """Extract key topics from text (simple keyword extraction)."""
        # This is a simplified implementation
        # In production, you might use NLP libraries like spaCy or NLTK
        import re
        
        # Remove common words and extract meaningful terms
        words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower())
        common_words = {'this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 'said', 'each', 'which', 'their', 'time', 'about', 'would', 'there', 'could', 'other', 'more', 'very', 'what', 'know', 'just', 'first', 'into', 'over', 'think', 'also', 'your', 'work', 'life', 'only', 'can', 'still', 'should', 'after', 'being', 'now', 'made', 'before', 'here', 'through', 'when', 'where', 'much', 'some', 'these', 'many', 'then', 'them', 'well', 'were'}
        
        meaningful_words = [word for word in words if word not in common_words and len(word) > 3]
        
        # Return top 10 most frequent topics
        from collections import Counter
        topic_counts = Counter(meaningful_words)
        return [topic for topic, count in topic_counts.most_common(10)]
    
    def get_session_history(self, db: Session, session_id: str) -> Dict[str, Any]:
        """Get complete session history with messages and context."""
        session = self.get_session(db, session_id)
        if not session:
            return {}
        
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at.asc()).all()
        
        context = db.query(ConversationContext).filter(
            ConversationContext.session_id == session.id
        ).first()
        
        return {
            'session_info': {
                'session_id': session.session_id,
                'title': session.title,
                'video_id': session.video_id,
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat()
            },
            'messages': [
                {
                    'id': msg.id,
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp_references': msg.timestamp_references,
                    'frame_references': msg.frame_references,
                    'confidence_score': msg.confidence_score,
                    'created_at': msg.created_at.isoformat()
                }
                for msg in messages
            ],
            'context': {
                'key_topics': context.key_topics if context else [],
                'referenced_segments': context.referenced_segments if context else [],
                'last_updated': context.last_updated.isoformat() if context else None
            }
        }
    
    def close_session(self, db: Session, session_id: str):
        """Close a chat session."""
        session = self.get_session(db, session_id)
        if session:
            session.is_active = False
            session.updated_at = datetime.utcnow()
            db.commit()