import mysql.connector
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_connection

def add_col():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE tournaments ADD COLUMN man_of_tournament_id INT DEFAULT NULL;")
        conn.commit()
        print("Column added successfully.")
    except Exception as e:
        print("Error:", str(e))
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    add_col()
