"""
Initialize database with schema
Run once after PostgreSQL installation
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def init_database():
    """Load schema.sql into database"""
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment variables")
        print("Please create .env file with DATABASE_URL")
        return
    
    try:
        # Connect to database
        print(f"Connecting to database...")
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Read and execute schema
        print(f"Loading schema.sql...")
        with open('schema.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        cursor.execute(schema_sql)
        conn.commit()
        
        print("✅ Database schema created successfully")
        
        # Verify tables
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        tables = cursor.fetchall()
        print(f"✅ Tables created: {[t[0] for t in tables]}")
        
        # Verify config
        cursor.execute("SELECT COUNT(*) FROM user_config")
        config_count = cursor.fetchone()[0]
        print(f"✅ Default config entries: {config_count}")
        
        # Show table sizes
        cursor.execute("""
            SELECT 
                tablename, 
                pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        print("\n📊 Table Sizes:")
        for table, size in cursor.fetchall():
            print(f"  {table}: {size}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ Database initialization complete!")
        print("You can now run the Flask application with: python app.py")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        raise


if __name__ == '__main__':
    init_database()
