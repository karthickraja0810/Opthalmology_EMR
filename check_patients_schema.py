
import psycopg2
from database import get_db_connection

def check_schema():
    conn = get_db_connection()
    if not conn:
        print("Failed to connect")
        return
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='patients';")
        columns = [row[0] for row in cursor.fetchall()]
        print(f"Columns in 'patients': {columns}")
        
        if 'updated_at' in columns and 'created_at' in columns:
            print("✅ created_at and updated_at columns exist.")
        else:
            print("❌ Missing columns!")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_schema()
