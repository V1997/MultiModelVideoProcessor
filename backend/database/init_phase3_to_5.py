#!/usr/bin/env python3
"""
Database initialization script for Phase 3-5 features
Creates new tables for conversational interface, visual search, and navigation features
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.models import Base, ChatSession, ChatMessage, ConversationContext, ObjectDetection, SceneClassification, TopicSegment, ContentOutline, NavigationEvent

def get_db_url():
    """Get database URL from environment"""
    return os.getenv("DATABASE_URL", "sqlite:///./multimodal_video.db")

def init_phase3_to_5_tables():
    """Initialize Phase 3-5 database tables"""
    
    # Get database URL
    db_url = get_db_url()
    
    # Create engine
    engine = create_engine(db_url)
    
    # Create session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    try:
        print("Creating Phase 3-5 database tables...")
        
        # Create all tables (this will only create new ones, existing tables are ignored)
        Base.metadata.create_all(bind=engine)
        
        print("✅ Phase 3-5 tables created successfully!")
        
        # Verify table creation
        with SessionLocal() as session:
            # Check if new tables exist by trying to query them
            tables_to_check = [
                ('chat_sessions', ChatSession),
                ('chat_messages', ChatMessage),
                ('conversation_contexts', ConversationContext),
                ('object_detections', ObjectDetection),
                ('scene_classifications', SceneClassification),
                ('topic_segments', TopicSegment),
                ('content_outlines', ContentOutline),
                ('navigation_events', NavigationEvent)
            ]
            
            print("\nVerifying table creation:")
            for table_name, model_class in tables_to_check:
                try:
                    # Try to query the table
                    result = session.query(model_class).first()
                    print(f"  ✅ {table_name}: OK")
                except SQLAlchemyError as e:
                    print(f"  ❌ {table_name}: ERROR - {str(e)}")
                    
        print("\n🎉 Phase 3-5 database initialization completed!")
        
    except SQLAlchemyError as e:
        print(f"❌ Database error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False
    
    return True

def reset_phase3_to_5_tables():
    """Reset Phase 3-5 tables (DROP and recreate)"""
    
    db_url = get_db_url()
    engine = create_engine(db_url)
    
    try:
        print("⚠️  Resetting Phase 3-5 database tables...")
        
        # For SQLite, we'll recreate all tables
        if "sqlite" in db_url:
            print("SQLite detected - recreating all tables...")
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            print("✅ All tables recreated for SQLite")
        else:
            # For PostgreSQL, drop Phase 3-5 tables in reverse order
            tables_to_drop = [
                'navigation_events',
                'content_outlines', 
                'topic_segments',
                'scene_classifications',
                'object_detections',
                'conversation_contexts',
                'chat_messages',
                'chat_sessions'
            ]
            
            with engine.connect() as conn:
                for table_name in tables_to_drop:
                    try:
                        conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                        print(f"  🗑️  Dropped table: {table_name}")
                    except SQLAlchemyError as e:
                        print(f"  ⚠️  Could not drop {table_name}: {str(e)}")
                
                # Commit the drops
                conn.commit()
            
            # Recreate tables
            Base.metadata.create_all(bind=engine)
            print("✅ Phase 3-5 tables reset successfully!")
        
    except SQLAlchemyError as e:
        print(f"❌ Database error during reset: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error during reset: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize Phase 3-5 database tables")
    parser.add_argument(
        "--reset", 
        action="store_true", 
        help="Reset (drop and recreate) Phase 3-5 tables"
    )
    
    args = parser.parse_args()
    
    if args.reset:
        success = reset_phase3_to_5_tables()
    else:
        success = init_phase3_to_5_tables()
    
    sys.exit(0 if success else 1)
