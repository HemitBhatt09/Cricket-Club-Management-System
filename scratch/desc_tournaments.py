import mysql.connector
import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_connection

def describe_tournaments():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("DESCRIBE tournaments")
    rows = cursor.fetchall()
    for r in rows:
        print(r)

    cursor.close()
    conn.close()

if __name__ == "__main__":
    describe_tournaments()
