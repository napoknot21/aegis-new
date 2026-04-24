#!/usr/bin/env python3
"""
Test reading quotes from the database
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import Settings

def read_quotes():
    """Read quotes from the database"""
    settings = Settings()
    
    print("=" * 60)
    print("READING QUOTES FROM DATABASE")
    print("=" * 60)
    print(f"Environment: {settings.environment}")
    print("Database URL: configured (redacted)" if settings.database_url else "No database URL")
    print()
    
    if not settings.database_url:
        print("❌ ERROR: No database URL configured")
        return False
    
    try:
        import psycopg
        
        print(f"✓ Connecting to database...")
        
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                print(f"✓ Connected!")
                
                # Check if quotes table exists
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'quotes'
                    );
                """)
                quotes_exists = cur.fetchone()[0]
                
                if not quotes_exists:
                    print(f"\n❌ 'quotes' table DOES NOT EXIST in database")
                    return False
                
                print(f"\n✓ 'quotes' table EXISTS")
                
                # Get quotes count
                cur.execute("SELECT COUNT(*) FROM quotes;")
                total_count = cur.fetchone()[0]
                print(f"  Total records: {total_count}")
                
                # Get all quotes
                cur.execute("""
                    SELECT id, domain, author, quote
                    FROM quotes 
                    ORDER BY id
                """)
                rows = cur.fetchall()
                
                if not rows:
                    print(f"\n❌ No quotes found in table")
                    return False
                
                print(f"\n✓ Found {len(rows)} quotes:\n")
                for id_q, domain, author, quote in rows:
                    print(f"[{id_q}] {quote}")
                    print(f"    Author: {author}")
                    print(f"    Domain: {domain}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = read_quotes()
    sys.exit(0 if success else 1)
