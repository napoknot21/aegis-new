#!/usr/bin/env python3
"""
Test database connection script
"""
import sys
import os
from pathlib import Path

# Add the backend app to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import Settings

def test_connection():
    """Test database connection"""
    settings = Settings()
    
    print("=" * 60)
    print("DATABASE CONNECTION TEST")
    print("=" * 60)
    print(f"Environment: {settings.environment}")
    print(f"Persistence Backend: {settings.persistence_backend}")
    print("Database URL: configured (redacted)" if settings.database_url else "No database URL")
    print()
    
    if not settings.database_url:
        print("❌ ERROR: No database URL configured")
        return False
    
    try:
        import psycopg
        print(f"✓ psycopg3 version: {psycopg.__version__}")
        
        # Try to connect
        print("\nAttempting connection...")
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version();")
                db_version = cur.fetchone()[0]
                print(f"✓ Connection successful!")
                print(f"  PostgreSQL version: {db_version[:50]}...")
                
                # Check if quotes table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'quotes'
                    );
                """)
                quotes_exists = cur.fetchone()[0]
                
                if quotes_exists:
                    print(f"\n✓ 'quotes' table EXISTS")
                    cur.execute("SELECT COUNT(*) FROM quotes;")
                    count = cur.fetchone()[0]
                    print(f"  Record count: {count}")
                else:
                    print(f"\n✗ 'quotes' table DOES NOT EXIST - needs to be created")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
