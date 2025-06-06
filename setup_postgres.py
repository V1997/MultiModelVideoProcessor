"""
PostgreSQL Database Setup Script for MultiModel Video Processor
"""

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import os
from dotenv import load_dotenv
import sys

def create_database():
    """Create the multimodal_video database if it doesn't exist"""
    
    # Default connection parameters
    DEFAULT_USER = "postgres"
    DEFAULT_PASSWORD = "password"  # Update this to match your PostgreSQL password
    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = "5432"
    DATABASE_NAME = "multimodal_video"
    
    print("🔧 Setting up PostgreSQL database for MultiModel Video Processor...")
    
    # Get user input for connection details
    user = input(f"PostgreSQL username (default: {DEFAULT_USER}): ").strip() or DEFAULT_USER
    password = input(f"PostgreSQL password (default: {DEFAULT_PASSWORD}): ").strip() or DEFAULT_PASSWORD
    host = input(f"PostgreSQL host (default: {DEFAULT_HOST}): ").strip() or DEFAULT_HOST
    port = input(f"PostgreSQL port (default: {DEFAULT_PORT}): ").strip() or DEFAULT_PORT
    
    try:
        # Connect to PostgreSQL server (not to a specific database)
        print(f"\n📡 Connecting to PostgreSQL server at {host}:{port}...")
        conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database="postgres"  # Connect to default postgres database
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname='{DATABASE_NAME}'")
        exists = cursor.fetchone()
        
        if exists:
            print(f"✅ Database '{DATABASE_NAME}' already exists!")
        else:
            # Create the database
            print(f"🔨 Creating database '{DATABASE_NAME}'...")
            cursor.execute(f"CREATE DATABASE {DATABASE_NAME}")
            print(f"✅ Database '{DATABASE_NAME}' created successfully!")
        
        cursor.close()
        conn.close()
        
        # Update .env file with correct connection string
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{DATABASE_NAME}"
        print(f"\n📝 Updating .env file with connection string...")
        
        # Read current .env file
        env_path = ".env"
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                lines = f.readlines()
            
            # Update DATABASE_URL line
            with open(env_path, 'w') as f:
                for line in lines:
                    if line.startswith('DATABASE_URL='):
                        f.write(f'DATABASE_URL={database_url}\n')
                    else:
                        f.write(line)
        
        print(f"✅ .env file updated with: DATABASE_URL={database_url}")
        
        # Test connection to the new database
        print(f"\n🧪 Testing connection to '{DATABASE_NAME}'...")
        test_conn = psycopg2.connect(database_url)
        test_conn.close()
        print(f"✅ Connection test successful!")
        
        print(f"\n🎉 PostgreSQL setup complete!")
        print(f"📋 Next steps:")
        print(f"   1. Install dependencies: pip install -r requirements.txt")
        print(f"   2. Start the API server: cd backend/api && python -m uvicorn main:app --reload")
        print(f"   3. Visit http://localhost:8000/docs for API documentation")
        
    except psycopg2.Error as e:
        print(f"❌ PostgreSQL Error: {e}")
        print(f"\n🔧 Troubleshooting tips:")
        print(f"   - Make sure PostgreSQL is running")
        print(f"   - Check your username and password")
        print(f"   - Verify PostgreSQL is accepting connections on {host}:{port}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_database()
