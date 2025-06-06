"""
Multimodal RAG System for Video Content Analysis
Handles query processing, context retrieval, and response generation
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
import logging
from pathlib import Path
import json
import re

# AI/ML imports
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    from langchain_core.prompts import PromptTemplate
    import openai
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logging.warning("LangChain/OpenAI not available for RAG system")

from ..embedding_engine.engine import get_embedding_engine
from ..database.models import Video, TranscriptChunk, VideoFrame, SessionLocal

class MultimodalRAG:
    """
    Retrieval-Augmented Generation system for multimodal video content
    """
    
    def __init__(self, openai_api_key: Optional[str] = None):
        self.openai_api_key = openai_api_key
        self.chat_model = None
        self.embedding_engine = None
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Initialize prompt templates
        self._setup_prompts()
    
    async def initialize(self):
        """Initialize RAG system components"""
        try:
            # Initialize embedding engine
            self.embedding_engine = await get_embedding_engine()
            
            # Initialize language model
            if LANGCHAIN_AVAILABLE and self.openai_api_key:
                self.chat_model = ChatOpenAI(
                    temperature=0.7,
                    model_name="gpt-3.5-turbo",
                    openai_api_key=self.openai_api_key
                )
                self.logger.info("RAG system initialized with OpenAI")
            else:
                self.logger.warning("RAG system initialized without language model")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG system: {e}")
            raise
    
    def _setup_prompts(self):
        """Setup prompt templates for different query types"""
        
        self.system_prompt = """You are an AI assistant that analyzes video content. You have access to video transcripts and frame information.

Your capabilities:
- Analyze video content based on transcripts and visual frames
- Answer questions about what happens in videos
- Provide timestamps for specific events
- Describe visual elements and scenes
- Make connections between audio and visual content

Guidelines:
- Always cite timestamps when referencing specific moments
- Be specific about visual details when describing frames
- If you're unsure about something, say so
- Provide frame numbers or timestamps for visual references
- Keep responses informative but concise"""

        self.query_prompt_template = PromptTemplate(
            input_variables=["query", "context", "video_info"],
            template="""Based on the following video content, answer the user's question.

Video Information:
{video_info}

Relevant Context:
{context}

User Question: {query}

Please provide a detailed answer based on the available context. Include specific timestamps and frame references where relevant.

Answer:"""
        )
        
        self.summarization_prompt = PromptTemplate(
            input_variables=["content", "video_title"],
            template="""Summarize the following video content:

Video: {video_title}

Content:
{content}

Provide a comprehensive summary covering:
- Main topics discussed
- Key events or scenes
- Important timestamps
- Visual highlights

Summary:"""
        )
    
    async def process_query(self, 
                          query: str, 
                          video_ids: Optional[List[int]] = None,
                          search_type: str = "both",
                          max_results: int = 10) -> Dict[str, Any]:
        """
        Process a user query and generate a response
        
        Args:
            query: User's question
            video_ids: Specific videos to search (None for all)
            search_type: "text", "visual", or "both"
            max_results: Maximum context items to retrieve
        """
        try:
            # Step 1: Generate query embedding
            query_embedding = await self.embedding_engine.generate_text_embeddings([query])
            
            # Step 2: Retrieve relevant context
            context_items = await self._retrieve_context(
                query_embedding[0], 
                video_ids, 
                search_type, 
                max_results
            )
            
            # Step 3: Generate response
            response = await self._generate_response(query, context_items)
            
            return {
                "query": query,
                "response": response,
                "context": context_items,
                "video_ids": video_ids or [],
                "search_type": search_type
            }
            
        except Exception as e:
            self.logger.error(f"Error processing query: {e}")
            return {
                "query": query,
                "response": f"Sorry, I encountered an error processing your query: {str(e)}",
                "context": [],
                "video_ids": video_ids or [],
                "search_type": search_type
            }
    
    async def _retrieve_context(self, 
                              query_embedding, 
                              video_ids: Optional[List[int]], 
                              search_type: str, 
                              max_results: int) -> List[Dict]:
        """Retrieve relevant context from video content"""
        
        all_context = []
        
        # Search across all videos or specific ones
        if video_ids:
            for video_id in video_ids:
                context = await self.embedding_engine.search_similar_content(
                    query_embedding, 
                    content_type=search_type,
                    limit=max_results // len(video_ids),
                    video_id=video_id
                )
                all_context.extend(context)
        else:
            all_context = await self.embedding_engine.search_similar_content(
                query_embedding,
                content_type=search_type,
                limit=max_results
            )
        
        # Enrich context with database information
        enriched_context = await self._enrich_context(all_context)
        
        # Sort by relevance
        enriched_context.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        
        return enriched_context[:max_results]
    
    async def _enrich_context(self, context_items: List[Dict]) -> List[Dict]:
        """Enrich context items with additional database information"""
        
        db = SessionLocal()
        try:
            enriched = []
            
            for item in context_items:
                enriched_item = item.copy()
                
                # Get video information
                video_id = item.get("video_id")
                if video_id:
                    video = db.query(Video).filter(Video.id == video_id).first()
                    if video:
                        enriched_item["video_filename"] = video.filename
                        enriched_item["video_duration"] = video.duration
                        enriched_item["video_created"] = str(video.created_at)
                
                # Add context type
                if "text" in item:
                    enriched_item["context_type"] = "transcript"
                    enriched_item["content"] = item["text"]
                elif "frame_path" in item:
                    enriched_item["context_type"] = "frame"
                    enriched_item["content"] = f"Frame at {item.get('timestamp', 0):.2f}s"
                
                enriched.append(enriched_item)
            
            return enriched
            
        finally:
            db.close()
    
    async def _generate_response(self, query: str, context_items: List[Dict]) -> str:
        """Generate response using retrieved context"""
        
        if not self.chat_model:
            return self._generate_fallback_response(query, context_items)
        
        try:
            # Prepare context string
            context_str = self._format_context(context_items)
            
            # Prepare video information
            video_info = self._extract_video_info(context_items)
            
            # Generate response using language model
            prompt = self.query_prompt_template.format(
                query=query,
                context=context_str,
                video_info=video_info
            )
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = await self.chat_model.agenerate([messages])
            
            return response.generations[0][0].text.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return self._generate_fallback_response(query, context_items)
    
    def _format_context(self, context_items: List[Dict]) -> str:
        """Format context items for prompt"""
        
        formatted_items = []
        
        for i, item in enumerate(context_items, 1):
            context_type = item.get("context_type", "unknown")
            video_filename = item.get("video_filename", "Unknown video")
            similarity = item.get("similarity", 0)
            
            if context_type == "transcript":
                timestamp = item.get("start_time", 0)
                text = item.get("text", "")
                formatted_items.append(
                    f"{i}. [TRANSCRIPT] {video_filename} at {timestamp:.2f}s (relevance: {similarity:.3f})\n"
                    f"   \"{text}\""
                )
                
            elif context_type == "frame":
                timestamp = item.get("timestamp", 0)
                frame_number = item.get("frame_number", 0)
                formatted_items.append(
                    f"{i}. [FRAME] {video_filename} at {timestamp:.2f}s, frame #{frame_number} (relevance: {similarity:.3f})\n"
                    f"   Visual content at this timestamp"
                )
        
        return "\n\n".join(formatted_items)
    
    def _extract_video_info(self, context_items: List[Dict]) -> str:
        """Extract video metadata from context"""
        
        videos = {}
        for item in context_items:
            video_id = item.get("video_id")
            if video_id and video_id not in videos:
                videos[video_id] = {
                    "filename": item.get("video_filename", "Unknown"),
                    "duration": item.get("video_duration", 0),
                    "created": item.get("video_created", "Unknown")
                }
        
        video_info_parts = []
        for video_id, info in videos.items():
            video_info_parts.append(
                f"- {info['filename']} (Duration: {info['duration']:.2f}s, Created: {info['created']})"
            )
        
        return "\n".join(video_info_parts) if video_info_parts else "No video information available"
    
    def _generate_fallback_response(self, query: str, context_items: List[Dict]) -> str:
        """Generate a simple response without language model"""
        
        if not context_items:
            return "I couldn't find any relevant content for your query."
        
        response_parts = [
            f"Based on the video content, I found {len(context_items)} relevant items:",
            ""
        ]
        
        for i, item in enumerate(context_items[:5], 1):  # Limit to top 5
            context_type = item.get("context_type", "unknown")
            video_filename = item.get("video_filename", "Unknown video")
            
            if context_type == "transcript":
                timestamp = item.get("start_time", 0)
                text = item.get("text", "")[:100] + "..." if len(item.get("text", "")) > 100 else item.get("text", "")
                response_parts.append(f"{i}. At {timestamp:.2f}s in {video_filename}: \"{text}\"")
                
            elif context_type == "frame":
                timestamp = item.get("timestamp", 0)
                response_parts.append(f"{i}. Frame at {timestamp:.2f}s in {video_filename}")
        
        response_parts.append("")
        response_parts.append("For more detailed analysis, please ensure the language model is properly configured.")
        
        return "\n".join(response_parts)
    
    async def summarize_video(self, video_id: int) -> Dict[str, Any]:
        """Generate a comprehensive summary of a video"""
        
        try:
            db = SessionLocal()
            
            # Get video information
            video = db.query(Video).filter(Video.id == video_id).first()
            if not video:
                raise ValueError(f"Video {video_id} not found")
            
            # Get all transcript content
            transcripts = db.query(TranscriptChunk).filter(
                TranscriptChunk.video_id == video_id
            ).order_by(TranscriptChunk.start_time).all()
            
            # Get frame information
            frames = db.query(VideoFrame).filter(
                VideoFrame.video_id == video_id
            ).order_by(VideoFrame.timestamp).all()
            
            # Prepare content for summarization
            content_parts = []
            
            # Add transcript content
            if transcripts:
                content_parts.append("TRANSCRIPTS:")
                for transcript in transcripts:
                    content_parts.append(f"[{transcript.start_time:.2f}s] {transcript.text}")
            
            # Add frame information
            if frames:
                content_parts.append("\nFRAMES:")
                content_parts.append(f"Total frames extracted: {len(frames)}")
                content_parts.append(f"Frame timestamps: {frames[0].timestamp:.2f}s to {frames[-1].timestamp:.2f}s")
            
            content_str = "\n".join(content_parts)
            
            # Generate summary
            if self.chat_model:
                summary = await self._generate_ai_summary(video.filename, content_str)
            else:
                summary = self._generate_basic_summary(video, transcripts, frames)
            
            return {
                "video_id": video_id,
                "video_filename": video.filename,
                "duration": video.duration,
                "summary": summary,
                "transcript_chunks": len(transcripts),
                "frames_extracted": len(frames)
            }
            
        except Exception as e:
            self.logger.error(f"Error summarizing video {video_id}: {e}")
            raise
        finally:
            db.close()
    
    async def _generate_ai_summary(self, video_title: str, content: str) -> str:
        """Generate AI-powered summary"""
        
        try:
            prompt = self.summarization_prompt.format(
                video_title=video_title,
                content=content[:4000]  # Limit content length
            )
            
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=prompt)
            ]
            
            response = await self.chat_model.agenerate([messages])
            return response.generations[0][0].text.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating AI summary: {e}")
            return f"AI summary generation failed: {str(e)}"
    
    def _generate_basic_summary(self, video: Video, transcripts: List, frames: List) -> str:
        """Generate basic summary without AI"""
        
        summary_parts = [
            f"Video: {video.filename}",
            f"Duration: {video.duration:.2f} seconds",
            f"Dimensions: {video.width}x{video.height}",
            f"FPS: {video.fps:.2f}",
            "",
            f"Content Analysis:",
            f"- {len(transcripts)} transcript segments",
            f"- {len(frames)} frames extracted",
        ]
        
        if transcripts:
            total_text = " ".join([t.text for t in transcripts])
            word_count = len(total_text.split())
            summary_parts.append(f"- ~{word_count} words transcribed")
            
            # Simple keyword extraction
            common_words = self._extract_keywords(total_text)
            if common_words:
                summary_parts.append(f"- Key terms: {', '.join(common_words[:10])}")
        
        return "\n".join(summary_parts)
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Simple keyword extraction"""
        
        # Remove common stop words and extract meaningful terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'this', 'that', 'these', 'those'}
        
        # Simple tokenization and filtering
        words = re.findall(r'\b\w+\b', text.lower())
        filtered_words = [w for w in words if len(w) > 3 and w not in stop_words]
        
        # Count frequency
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return top words
        return sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)

# Global RAG instance
rag_system = None

async def get_rag_system(openai_api_key: Optional[str] = None):
    """Get or create the global RAG system instance"""
    global rag_system
    
    if rag_system is None:
        rag_system = MultimodalRAG(openai_api_key)
        await rag_system.initialize()
    
    return rag_system
