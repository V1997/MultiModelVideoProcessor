"""
YouTube Search Service for MultiModelVideo
Provides YouTube video search functionality using YouTube Data API v3
"""

import os
import logging
from typing import List, Optional, Dict, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import isodate
from datetime import datetime

logger = logging.getLogger(__name__)

class YouTubeSearchService:
    """Service for searching YouTube videos"""
    
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        self.service = None
        
        if self.api_key:
            try:
                self.service = build('youtube', 'v3', developerKey=self.api_key)
                logger.info("YouTube Data API service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize YouTube service: {e}")
        else:
            logger.warning("YouTube API key not found. Search functionality will be limited.")
    
    def search_videos(
        self, 
        query: str, 
        max_results: int = 10,
        duration: Optional[str] = None,
        order: str = "relevance"
    ) -> List[Dict[str, Any]]:
        """
        Search for YouTube videos
        
        Args:
            query: Search query
            max_results: Maximum number of results (1-50)
            duration: Video duration filter ('short', 'medium', 'long')
            order: Sort order ('relevance', 'date', 'rating', 'viewCount')
        
        Returns:
            List of video information dictionaries
        """
        if not self.service:
            return self._get_mock_results(query, max_results)
        
        try:
            # Search parameters
            search_params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'maxResults': min(max_results, 50),
                'order': order,
                'videoCategoryId': '27',  # Education category
                'relevanceLanguage': 'en'
            }
            
            # Add duration filter if specified
            if duration in ['short', 'medium', 'long']:
                search_params['videoDuration'] = duration
            
            # Perform search
            search_response = self.service.search().list(**search_params).execute()
            
            # Extract video IDs for detailed info
            video_ids = [item['id']['videoId'] for item in search_response['items']]
            
            # Get detailed video information
            videos_response = self.service.videos().list(
                part='snippet,contentDetails,statistics',
                id=','.join(video_ids)
            ).execute()
            
            # Format results
            results = []
            for video in videos_response['items']:
                video_info = self._format_video_info(video)
                if video_info:
                    results.append(video_info)
            
            logger.info(f"Found {len(results)} videos for query: {query}")
            return results
            
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return self._get_mock_results(query, max_results)
        except Exception as e:
            logger.error(f"Error searching YouTube: {e}")
            return self._get_mock_results(query, max_results)
    
    def get_video_info(self, video_url: str) -> Optional[Dict[str, Any]]:
        """
        Get information for a specific YouTube video
        
        Args:
            video_url: YouTube video URL
            
        Returns:
            Video information dictionary or None
        """
        from backend.transcript_handler.handler import TranscriptHandler
        
        handler = TranscriptHandler()
        video_id = handler.extract_youtube_video_id(video_url)
        
        if not video_id or not self.service:
            return None
        
        try:
            videos_response = self.service.videos().list(
                part='snippet,contentDetails,statistics',
                id=video_id
            ).execute()
            
            if videos_response['items']:
                return self._format_video_info(videos_response['items'][0])
                
        except Exception as e:
            logger.error(f"Error getting video info: {e}")
            
        return None
    
    def _format_video_info(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format video data from YouTube API response"""
        try:
            snippet = video_data['snippet']
            content_details = video_data['contentDetails']
            statistics = video_data.get('statistics', {})
            
            # Parse duration
            duration_iso = content_details['duration']
            duration = isodate.parse_duration(duration_iso)
            duration_str = str(duration)
            
            # Format published date
            published_at = datetime.fromisoformat(
                snippet['publishedAt'].replace('Z', '+00:00')
            )
            
            return {
                'video_id': video_data['id'],
                'title': snippet['title'],
                'description': snippet['description'][:500] + '...' if len(snippet['description']) > 500 else snippet['description'],
                'thumbnail_url': snippet['thumbnails'].get('medium', {}).get('url', ''),
                'duration': duration_str,
                'view_count': int(statistics.get('viewCount', 0)),
                'published_at': published_at.isoformat(),
                'channel_title': snippet['channelTitle'],
                'url': f"https://www.youtube.com/watch?v={video_data['id']}"
            }
            
        except Exception as e:
            logger.error(f"Error formatting video info: {e}")
            return None
    
    def _get_mock_results(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Return mock results when API is not available"""
        mock_videos = [
            {
                'video_id': 'dQw4w9WgXcQ',
                'title': f'Sample Educational Video about {query}',
                'description': f'This is a sample educational video that covers topics related to {query}. It includes comprehensive explanations and examples.',
                'thumbnail_url': 'https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg',
                'duration': '0:04:33',
                'view_count': 1000000,
                'published_at': '2023-01-01T00:00:00+00:00',
                'channel_title': 'Educational Channel',
                'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
            },
            {
                'video_id': 'jNQXAC9IVRw',
                'title': f'Advanced {query} Tutorial',
                'description': f'Deep dive into {query} concepts with practical examples and real-world applications.',
                'thumbnail_url': 'https://img.youtube.com/vi/jNQXAC9IVRw/mqdefault.jpg',
                'duration': '0:12:15',
                'view_count': 500000,
                'published_at': '2023-06-15T00:00:00+00:00',
                'channel_title': 'Tech Education Hub',
                'url': 'https://www.youtube.com/watch?v=jNQXAC9IVRw'
            },
            {
                'video_id': 'kJQP7kiw5Fk',
                'title': f'{query} Fundamentals Explained',
                'description': f'Learn the fundamentals of {query} in this comprehensive beginner-friendly tutorial.',
                'thumbnail_url': 'https://img.youtube.com/vi/kJQP7kiw5Fk/mqdefault.jpg',
                'duration': '0:08:42',
                'view_count': 750000,
                'published_at': '2023-03-20T00:00:00+00:00',
                'channel_title': 'Learning Academy',
                'url': 'https://www.youtube.com/watch?v=kJQP7kiw5Fk'
            }
        ]
        
        logger.info(f"Returning {min(max_results, len(mock_videos))} mock results for: {query}")
        return mock_videos[:max_results]
