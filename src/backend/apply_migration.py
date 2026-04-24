#!/usr/bin/env python3
"""
Apply the quotes migration to the database
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import Settings

def apply_migration():
    """Apply the quotes migration"""
    settings = Settings()
    
    print("=" * 60)
    print("APPLYING QUOTES MIGRATION")
    print("=" * 60)
    print(f"Environment: {settings.environment}")
    print("Database URL: configured (redacted)" if settings.database_url else "No database URL")
    print()
    
    if not settings.database_url:
        print("❌ ERROR: No database URL configured")
        return False
    
    try:
        import psycopg
        
        # Read the migration file
        migration_path = Path(__file__).parent.parent / "supabase" / "migrations" / "20260420000100_add_login_quotes.sql"
        
        if not migration_path.exists():
            print(f"❌ ERROR: Migration file not found at {migration_path}")
            return False
        
        migration_sql = migration_path.read_text()
        
        print(f"✓ Migration file loaded")
        print(f"✓ Connecting to database...")
        
        with psycopg.connect(settings.database_url) as conn:
            with conn.cursor() as cur:
                print(f"✓ Connected!")
                print(f"\nExecuting migration...\n")
                
                # Execute the migration
                cur.execute(migration_sql)
                conn.commit()
                
                print(f"✓ Migration executed successfully!")
                
                # Verify the table and data
                cur.execute("SELECT COUNT(*) FROM quotes WHERE is_active = TRUE;")
                count = cur.fetchone()[0]
                print(f"✓ Active quotes in database: {count}")
                
                # Show the quotes
                cur.execute("SELECT id_quote, quote, author FROM quotes ORDER BY sort_order;")
                rows = cur.fetchall()
                print(f"\nQuotes:")
                for row in rows:
                    print(f"  [{row[0]}] {row[1]}")
                    print(f"       - {row[2]}\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
