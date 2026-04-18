from flask import Blueprint, jsonify, session
from db import get_connection

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route("/matches-data", methods=["GET"])
def matches_data():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # UPCOMING MATCHES
        cursor.execute("""
            SELECT team1_name AS team1, team2_name AS team2
            FROM matches
            WHERE status = 'upcoming'
        """)
        upcoming = cursor.fetchall()

        # RECENT MATCHES
        cursor.execute("""
            SELECT team1_name AS team1, team2_name AS team2, result
            FROM matches
            WHERE status = 'completed'
            ORDER BY match_id DESC
            LIMIT 5
        """)
        recent = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({
            "upcoming": upcoming,
            "recent": recent
        })

    except Exception as e:
        print("ERROR:", str(e))
        return jsonify({"error": str(e)})
    

@dashboard_bp.route("/dashboard-upcoming", methods=["GET"])
def dashboard_upcoming():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            m.match_id,
            m.match_date,
            m.match_type,
            m.tournament_id,
            m.stage,
            t1.team_name AS team1_name,
            t2.team_name AS team2_name
        FROM matches m
        JOIN teams t1 ON m.team1_id = t1.team_id
        JOIN teams t2 ON m.team2_id = t2.team_id
        WHERE m.is_completed = FALSE
        ORDER BY m.match_date ASC
    """)

    matches = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(matches)
    
@dashboard_bp.route("/dashboard-recent", methods=["GET"])
def dashboard_recent():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            m.match_id,
            m.match_date,
            m.match_type,
            m.tournament_id,
            m.stage,

            t1.team_name AS team1_name,
            t2.team_name AS team2_name,

            m.team1_score,
            m.team2_score,

            m.team1_wickets,
            m.team2_wickets,

            m.team1_overs,
            m.team2_overs,

            m.winner,
            m.is_completed

        FROM matches m
        JOIN teams t1 ON m.team1_id = t1.team_id
        JOIN teams t2 ON m.team2_id = t2.team_id

        WHERE m.is_completed = TRUE
        ORDER BY m.match_id DESC
        LIMIT 30
    """)

    matches = cursor.fetchall()

    # 🔥 FIX FLOAT ISSUE (same as yours)
    for m in matches:
        m['team1_overs'] = round(m['team1_overs'], 1) if m['team1_overs'] else 0
        m['team2_overs'] = round(m['team2_overs'], 1) if m['team2_overs'] else 0

    cursor.close()
    conn.close()

    return jsonify(matches)

import os
from werkzeug.utils import secure_filename
from flask import request

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads', 'profiles')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@dashboard_bp.route("/update-profile", methods=["POST"])
def update_profile():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    name = request.form.get("name")
    role = request.form.get("role")
    file = request.files.get("profile_pic")

    conn = get_connection()
    cursor = conn.cursor()

    try:
        update_fields = []
        params = []
        if name:
            update_fields.append("name = %s")
            params.append(name)
        if role:
            update_fields.append("role = %s")
            params.append(role)
        
        if file and file.filename != '':
            filename = secure_filename(f"user_{user_id}_{file.filename}")
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            update_fields.append("profile_pic = %s")
            params.append(filename)

        if update_fields:
            query = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = %s"
            params.append(user_id)
            cursor.execute(query, tuple(params))
            conn.commit()

        return jsonify({"message": "Profile updated successfully"})
    except Exception as e:
        print("UPDATE PROFILE ERROR:", str(e))
        return jsonify({"error": "Failed to update profile."}), 500
    finally:
        cursor.close()
        conn.close()

@dashboard_bp.route("/player-matches", methods=["GET"])
def player_matches():
    from flask import request
    user_id = request.args.get('user_id') or session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                m.match_id,
                m.match_date,
                m.match_type,
                m.stage,
                m.tournament_id,
                t1.team_name AS team1_name,
                t2.team_name AS team2_name,
                m.team1_score,
                m.team2_score,
                m.team1_wickets,
                m.team2_wickets,
                m.team1_overs,
                m.team2_overs,
                m.winner,
                m.team1_id,
                m.team2_id,
                mp.team_id AS user_team_id
            FROM match_players mp
            JOIN matches m ON mp.match_id = m.match_id
            JOIN teams t1 ON m.team1_id = t1.team_id
            JOIN teams t2 ON m.team2_id = t2.team_id
            WHERE mp.user_id = %s AND m.is_completed = TRUE
            GROUP BY
                m.match_id, m.match_date, m.match_type, m.stage, m.tournament_id,
                t1.team_name, t2.team_name,
                m.team1_score, m.team2_score,
                m.team1_wickets, m.team2_wickets,
                m.team1_overs, m.team2_overs,
                m.winner, m.team1_id, m.team2_id, mp.team_id
            ORDER BY m.match_id DESC
        """, (user_id,))


        matches = cursor.fetchall()

        for m in matches:
            m['team1_overs'] = round(float(m['team1_overs'] or 0), 1)
            m['team2_overs'] = round(float(m['team2_overs'] or 0), 1)
            m['match_date'] = str(m['match_date']) if m['match_date'] else None

        return jsonify(matches)

    except Exception as e:
        print("PLAYER MATCHES ERROR:", str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@dashboard_bp.route("/player-profile/<int:user_id>", methods=["GET"])
def player_profile(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Personal info
        cursor.execute("SELECT user_id, name, mobile_no, role, profile_pic FROM users WHERE user_id = %s", (user_id,))
        personal = cursor.fetchone()
        
        if not personal:
            return jsonify({"error": "Player not found"}), 404

        # Matches Played
        cursor.execute("SELECT COUNT(DISTINCT match_id) as matches_played FROM match_players WHERE user_id = %s", (user_id,))
        matches_played = cursor.fetchone()['matches_played']

        cursor.execute("""
            SELECT 
                SUM(CASE WHEN extra_type IN ('WIDE', 'BYE', 'LEG_BYE') THEN 0 ELSE runs_scored END) as total_runs, 
                SUM(CASE WHEN extra_type = 'WIDE' THEN 0 ELSE 1 END) as balls_faced
            FROM ball_by_ball
            WHERE striker_id = %s
        """, (user_id,))
        batting_agg = cursor.fetchone()
        
        total_runs = float(batting_agg['total_runs'] or 0)
        balls_faced = float(batting_agg['balls_faced'] or 0)
        strike_rate = round((total_runs / balls_faced * 100), 2) if balls_faced > 0 else 0

        # Batting average (runs / dismissals)
        cursor.execute("""
            SELECT SUM(CASE WHEN is_wicket = 1 THEN 1 ELSE 0 END) as dismissals
            FROM ball_by_ball
            WHERE striker_id = %s
        """, (user_id,))
        dismissals_row = cursor.fetchone()
        dismissals = float(dismissals_row['dismissals'] or 0)
        batting_average = round(total_runs / dismissals, 2) if dismissals > 0 else (total_runs if total_runs > 0 else 0)
        
        # Highest Score
        cursor.execute("""
            SELECT SUM(runs_scored) as match_runs
            FROM ball_by_ball
            WHERE striker_id = %s
            GROUP BY match_id
            ORDER BY match_runs DESC
            LIMIT 1
        """, (user_id,))
        hs_row = cursor.fetchone()
        highest_score = hs_row['match_runs'] if hs_row else 0

        # Bowling Stats - Total Wickets
        cursor.execute("""
            SELECT COUNT(*) as total_wickets
            FROM ball_by_ball
            WHERE bowler_id = %s AND is_wicket = 1 AND wicket_type != 'RUNOUT'
        """, (user_id,))
        total_wickets = cursor.fetchone()['total_wickets'] or 0
        
        # Best Bowling
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN is_wicket = 1 AND wicket_type != 'RUNOUT' THEN 1 ELSE 0 END) as match_wickets,
                SUM(runs_scored + COALESCE(extra_runs, 0)) as match_runs_conceded
            FROM ball_by_ball
            WHERE bowler_id = %s
            GROUP BY match_id
            ORDER BY match_wickets DESC, match_runs_conceded ASC
            LIMIT 1
        """, (user_id,))
        best_bowl_row = cursor.fetchone()
        best_bowling_wickets = best_bowl_row['match_wickets'] if best_bowl_row else 0
        best_bowling_runs = best_bowl_row['match_runs_conceded'] if best_bowl_row else 0
        best_bowling = f"{best_bowling_wickets}/{best_bowling_runs}" if best_bowl_row else "0/0"
        
        # Economy Rate and Bowling Strike Rate
        cursor.execute("""
            SELECT SUM(runs_scored + COALESCE(extra_runs, 0)) as total_runs_conceded,
                   SUM(CASE WHEN extra_type IS NULL OR extra_type NOT IN ('WIDE', 'NO_BALL') THEN 1 ELSE 0 END) as legal_balls_bowled
            FROM ball_by_ball
            WHERE bowler_id = %s
        """, (user_id,))
        bowl_agg = cursor.fetchone()
        total_runs_conceded = float(bowl_agg['total_runs_conceded'] or 0)
        legal_balls_bowled = float(bowl_agg['legal_balls_bowled'] or 0)
        overs_bowled = legal_balls_bowled / 6.0
        economy = round((total_runs_conceded / overs_bowled), 2) if overs_bowled > 0 else 0
        
        bowling_sr = round(legal_balls_bowled / total_wickets, 2) if total_wickets > 0 else 0

        return jsonify({
            "personal": personal,
            "stats": {
                "matches_played": matches_played,
                "total_runs": total_runs,
                "highest_score": highest_score,
                "batting_average": batting_average,
                "strike_rate": strike_rate,
                "total_wickets": total_wickets,
                "best_bowling": best_bowling,
                "economy": economy,
                "bowling_sr": bowling_sr
            }
        })
    except Exception as e:
        print("PLAYER PROFILE ERROR:", str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()