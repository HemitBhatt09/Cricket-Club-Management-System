import mysql.connector
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_connection

def clear_db():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Disable foreign key checks to allow truncating
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        
        tables = [
            "ball_by_ball",
            "current_match_state",
            "match_players",
            "matches",
            "tournament_teams",
            "tournaments"
        ]
        
        for table in tables:
            print(f"Truncating {table}...")
            cursor.execute(f"TRUNCATE TABLE {table};")
            
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        conn.commit()
        print("Database successfully cleared of all matches, stats, and tournaments!")
        
    except Exception as e:
        print("Error clearing DB:", str(e))
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    clear_db()
