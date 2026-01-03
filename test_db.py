import psycopg2
# Import the connection logic we centralizing
from database import get_db_connection

def test_connection():
    """Tests if the app can successfully reach the database (Local or Cloud)."""
    conn = None
    try:
        # This will automatically use DATABASE_URL on Render or localhost on your Mac
        conn = get_db_connection()
        
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT version();")
            db_version = cur.fetchone()
            print(f"✅ Successfully connected to PostgreSQL!")
            print(f"📊 Database Version: {db_version[0]}")
            cur.close()
            conn.close()
        else:
            print("❌ Failed to connect: get_db_connection() returned None")
            
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")

if __name__ == "__main__":
    test_connection()