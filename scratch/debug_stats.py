import mysql.connector
import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import get_connection

def debug_query(tournament_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    print(f"DEBUG: Testing Tournament ID {tournament_id}")
    
    # Test 1: Top Batsmen
    cursor.execute("""
        SELECT u.name, t.team_name,
               SUM(CASE WHEN b.extra_type IN ('WIDE','BYE','LEG_BYE') THEN 0 ELSE b.runs_scored END) AS runs
        FROM ball_by_ball b
        JOIN users u ON b.striker_id = u.user_id
        JOIN matches m ON b.match_id = m.match_id
        LEFT JOIN match_players mp ON mp.match_id = m.match_id AND mp.user_id = u.user_id
        LEFT JOIN teams t ON t.team_id = mp.team_id
        WHERE m.tournament_id = %s
        GROUP BY u.user_id, u.name, t.team_name
    """, (tournament_id,))
    rows = cursor.fetchall()
    print(f"Top Batsmen Rows: {len(rows)}")
    for r in rows:
        print(f" - {r['name']} ({r['team_name']}): {r['runs']} runs")

    # Test 2: Subquery check
    cursor.execute("""
        SELECT b.striker_id, mp_inner.team_id, 
               SUM(CASE WHEN b.extra_type IN ('WIDE','BYE','LEG_BYE') THEN 0 ELSE b.runs_scored END) AS runs
        FROM ball_by_ball b 
        JOIN match_players mp_inner ON b.match_id = mp_inner.match_id AND b.striker_id = mp_inner.user_id
        JOIN matches m_inner ON b.match_id = m_inner.match_id
        WHERE m_inner.tournament_id = %s
        GROUP BY b.striker_id, mp_inner.team_id
    """, (tournament_id,))
    sub_rows = cursor.fetchall()
    print(f"Subquery bat Rows: {len(sub_rows)}")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    import sys
    tid = 8
    debug_query(tid)
