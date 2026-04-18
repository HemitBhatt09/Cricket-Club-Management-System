from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from db import get_connection

tournament_bp = Blueprint('tournament', __name__)

# ================= GET TOURNAMENTS =================
@tournament_bp.route("/tournaments", methods=["GET"])
def get_tournaments():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT tournament_id, tournament_name,
            host_name, host_mobile, logo,
            is_started, is_completed, hosted_by
        FROM tournaments
        ORDER BY tournament_id DESC
    """)

    data = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(data)


# ================= CREATE TOURNAMENT =================
@tournament_bp.route("/create-tournament", methods=["POST"])
def create_tournament():
    try:
        data = request.form

        name = data.get("name")
        date = data.get("date")
        t_type = data.get("type")
        overs = data.get("overs")
        match_type = data.get("match_type")
        ball_type = data.get("ball_type")
        location = data.get("location")

        # TEMP FIX (remove later)
        user_id = session.get("user_id") or 1

        if not user_id:
            return jsonify({"error": "User not logged in"}), 400

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Get user
        cursor.execute("SELECT name, mobile_no FROM users WHERE user_id=%s", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 400

        host_name = user["name"]
        host_mobile = user["mobile_no"]

        # Handle logo
        logo_file = request.files.get("logo")
        logo_filename = None

        if logo_file:
            import os
            os.makedirs("static/uploads", exist_ok=True)   # 🔥 FIX
            logo_filename = logo_file.filename
            logo_file.save(f"static/uploads/{logo_filename}")

        # Insert
        cursor.execute("""
            INSERT INTO tournaments
            (tournament_name, hosted_by, host_name, host_mobile,
             tournament_date, tournament_type, overs,
             match_type, ball_type, location, logo)

            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            name, user_id, host_name, host_mobile,
            date, t_type,
            overs if overs else None,
            match_type, ball_type, location, logo_filename
        ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Tournament Created"})

    except Exception as e:
        print("🔥 ERROR:", str(e))   # 👈 PRINT IN TERMINAL
        return jsonify({"error": str(e)}), 500
    

@tournament_bp.route("/join-tournament", methods=["POST"])
def join_tournament():
    try:
        data = request.json

        tournament_id = data.get("tournament_id")
        team_id = data.get("team_id")

        user_id =  session.get("user_id") or 2  # temp
       

        conn = get_connection()
        cursor = conn.cursor()

        # ❌ prevent duplicate
        cursor.execute("""
            SELECT * FROM tournament_teams
            WHERE tournament_id=%s AND team_id=%s
        """, (tournament_id, team_id))

        if cursor.fetchone():
            return jsonify({"error": "Team already registered"}), 400

        cursor.execute("""
            INSERT INTO tournament_teams (tournament_id, team_id, joined_by, status)
            VALUES (%s,%s,%s,'PENDING')
        """, (tournament_id, team_id, user_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Registered Successfully"})

    except Exception as e:
        print("🔥 ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

@tournament_bp.route("/invite-team", methods=["POST"])
def invite_team():
    try:
        data = request.json
        tournament_id = data.get("tournament_id")
        team_id = data.get("team_id")
        user_id = session.get("user_id")
        if not user_id: return jsonify({"error": "Unauthorized"}), 401

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT hosted_by FROM tournaments WHERE tournament_id=%s", (tournament_id,))
        t = cursor.fetchone()
        if not t or t['hosted_by'] != user_id:
            return jsonify({"error": "Unauthorized"}), 403

        cursor.execute("SELECT * FROM tournament_teams WHERE tournament_id=%s AND team_id=%s", (tournament_id, team_id))
        if cursor.fetchone():
            return jsonify({"error": "Team already registered or invited"}), 400

        cursor.execute("""
            INSERT INTO tournament_teams (tournament_id, team_id, joined_by, status)
            VALUES (%s,%s,%s,'INVITED')
        """, (tournament_id, team_id, user_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Team Invited"})
    except Exception as e:
        print("🔥 ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

@tournament_bp.route("/team-invitations", methods=["GET"])
def team_invitations():
    try:
        user_id = session.get("user_id")
        if not user_id: return jsonify([])

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                tt.tournament_id,
                t.tournament_name,
                team.team_name,
                team.team_id
            FROM tournament_teams tt
            JOIN tournaments t ON tt.tournament_id = t.tournament_id
            JOIN teams team ON tt.team_id = team.team_id
            JOIN team_members tm ON team.team_id = tm.team_id
            WHERE tm.user_id = %s AND tm.is_captain = 1 AND tt.status = 'INVITED'
        """, (user_id,))

        data = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify(data)
    except Exception as e:
        print("🔥 ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

@tournament_bp.route("/my-teams", methods=["GET"])
def my_teams():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                t.team_id,
                t.team_name,
                u.name AS captain_name
            FROM teams t

            JOIN team_members tm 
                ON t.team_id = tm.team_id AND tm.is_captain = 1

            JOIN users u 
                ON tm.user_id = u.user_id
        """)

        data = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(data)

    except Exception as e:
        print("🔥 ERROR:", str(e))
        return jsonify({"error": str(e)}), 500
    
@tournament_bp.route("/my-registrations", methods=["GET"])
def my_registrations():
    try:
        user_id = session.get("user_id") or 2  # forced

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT tournament_id
            FROM tournament_teams
            WHERE joined_by = %s
        """, (user_id,))

        data = cursor.fetchall()

        print("USER:", user_id)
        print("REG DATA:", data)

        cursor.close()
        conn.close()

        return jsonify(data)

    except Exception as e:
        print("🔥 ERROR:", str(e))
        return jsonify({"error": str(e)}), 500
    
@tournament_bp.route("/my-tournaments", methods=["GET"])
def my_tournaments():
    try:
        user_id =session.get("user_id") or 1  # TEMP (later session)

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                t.tournament_id,
                t.tournament_name,
                t.is_started,
                t.is_completed,
                COUNT(tt.team_id) AS total_teams

            FROM tournaments t

            LEFT JOIN tournament_teams tt
                ON t.tournament_id = tt.tournament_id

            WHERE t.hosted_by = %s

            GROUP BY t.tournament_id
            ORDER BY t.tournament_id DESC
        """, (user_id,))

        data = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(data)

    except Exception as e:
        print("🔥 ERROR:", str(e))
        return jsonify({"error": str(e)}), 500
    
@tournament_bp.route("/tournament-teams/<int:tournament_id>", methods=["GET"])
def get_tournament_teams(tournament_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                t.team_id,
                t.team_name,
                u.name AS captain_name,
                tt.status

            FROM tournament_teams tt

            JOIN teams t ON tt.team_id = t.team_id

            JOIN team_members tm 
                ON t.team_id = tm.team_id AND tm.is_captain = 1

            JOIN users u 
                ON tm.user_id = u.user_id

            WHERE tt.tournament_id = %s
        """, (tournament_id,))

        data = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify(data)

    except Exception as e:
        print("🔥 ERROR:", str(e))
        return jsonify({"error": str(e)}), 500
    
@tournament_bp.route("/update-team-status", methods=["POST"])
def update_team_status():
    try:
        data = request.json

        tournament_id = data.get("tournament_id")
        team_id = data.get("team_id")
        status = data.get("status")  # ACCEPTED / REJECTED

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE tournament_teams
            SET status = %s
            WHERE tournament_id = %s AND team_id = %s
        """, (status, tournament_id, team_id))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Status Updated"})

    except Exception as e:
        print("🔥 ERROR:", str(e))
        return jsonify({"error": str(e)}), 500
    
import random

@tournament_bp.route("/generate-schedule/<int:tournament_id>", methods=["POST"])
def generate_schedule(tournament_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # GET HOST ID
        cursor.execute("SELECT hosted_by FROM tournaments WHERE tournament_id = %s", (tournament_id,))
        tournament = cursor.fetchone()
        if not tournament:
            return jsonify({"error": "Tournament not found"}), 404
        host_id = tournament["hosted_by"]

        # ENSURE NO PENDING OR INVITED TEAMS
        cursor.execute("SELECT * FROM tournament_teams WHERE tournament_id = %s AND status IN ('PENDING', 'INVITED')", (tournament_id,))
        if cursor.fetchone():
            return jsonify({"error": "Cannot generate schedule: There are pending team requests or invitations."}), 400

        # GET ACCEPTED TEAMS
        cursor.execute("SELECT team_id FROM tournament_teams WHERE tournament_id = %s AND status = 'ACCEPTED'", (tournament_id,))
        teams = cursor.fetchall()
        if len(teams) < 3:
            return jsonify({"error": f"Minimum 3 accepted teams required to generate schedule. Currently only {len(teams)} team(s) accepted."}), 400

        team_ids = [t["team_id"] for t in teams]
        random.shuffle(team_ids) # SHUFFLE ON REGENERATE
        
        def generate_round_robin(team_ids):
            teams = team_ids[:]
            if len(teams) % 2 != 0: teams.append(None)
            n = len(teams)
            rounds = n - 1
            schedule = []
            for _ in range(rounds):
                round_matches = []
                for i in range(n // 2):
                    t1 = teams[i]
                    t2 = teams[n - 1 - i]
                    if t1 is not None and t2 is not None:
                        round_matches.append((t1, t2))
                schedule.append(round_matches)
                teams = [teams[0]] + [teams[-1]] + teams[1:-1]
            return schedule

        schedule = generate_round_robin(team_ids)

        # CLEAR EXISTING MATCHES FOR THIS TOURNAMENT (drafts)
        cursor.execute("DELETE FROM matches WHERE tournament_id = %s AND is_completed = 0", (tournament_id,))

        cursor.execute("SELECT match_type FROM tournaments WHERE tournament_id = %s", (tournament_id,))
        t_type = cursor.fetchone()['match_type'] or 'T20'

        for round_matches in schedule:
            for t1, t2 in round_matches:
                cursor.execute("""
                    INSERT INTO matches 
                    (team1_id, team2_id, tournament_id, match_type, is_completed, created_by, stage)
                    VALUES (%s,%s,%s,%s,0,%s,'LEAGUE')
                """, (t1, t2, tournament_id, t_type, host_id))
        # NOTE: SEMI/FINAL matches are auto-generated later via /auto-generate-knockouts

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Draft schedule generated"})

    except Exception as e:
        print("🔥 ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

@tournament_bp.route("/draft-schedule/<int:tournament_id>", methods=["GET"])
def draft_schedule(tournament_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.match_id, m.match_date, m.stage,
                   IFNULL(t1.team_name, 'TBA') as team1_name, 
                   IFNULL(t2.team_name, 'TBA') as team2_name
            FROM matches m
            LEFT JOIN teams t1 ON m.team1_id = t1.team_id
            LEFT JOIN teams t2 ON m.team2_id = t2.team_id
            WHERE m.tournament_id = %s AND m.is_completed = 0
            ORDER BY FIELD(m.stage, 'LEAGUE', 'SEMI', 'FINAL'), m.match_id
        """, (tournament_id,))
        matches = cursor.fetchall()
        
        for m in matches:
            if m['match_date']:
                m['match_date'] = m['match_date'].strftime('%Y-%m-%dT%H:%M') if hasattr(m['match_date'], 'strftime') else str(m['match_date']).replace(' ', 'T')
        
        cursor.close()
        conn.close()
        return jsonify(matches)
    except Exception as e:
        print("🔥 ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

@tournament_bp.route("/update-draft-match/<int:match_id>", methods=["POST"])
def update_draft_match(match_id):
    try:
        data = request.json
        match_date = data.get("match_date")
        conn = get_connection()
        cursor = conn.cursor()
        
        if match_date:
            cursor.execute("UPDATE matches SET match_date = %s WHERE match_id = %s", (match_date, match_id))
        else:
            cursor.execute("UPDATE matches SET match_date = NULL WHERE match_id = %s", (match_id,))
            
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Match updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@tournament_bp.route("/delete-draft-match/<int:match_id>", methods=["POST"])
def delete_draft_match(match_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM matches WHERE match_id = %s", (match_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Match deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@tournament_bp.route("/finalize-tournament/<int:tournament_id>", methods=["POST"])
def finalize_tournament(tournament_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tournaments
            SET is_started = 1
            WHERE tournament_id = %s
        """, (tournament_id,))
        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "message": "Tournament finalized",
            "redirect": f"/tournament/{tournament_id}/matches"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
@tournament_bp.route("/tournament-upcoming/<int:tournament_id>")
def tournament_upcoming(tournament_id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch host to determine permissions
    cursor.execute("SELECT hosted_by FROM tournaments WHERE tournament_id=%s", (tournament_id,))
    t_data = cursor.fetchone()
    host_id = t_data["hosted_by"] if t_data else -1
    is_host = (session.get('user_id') == host_id)

    # Use LEFT JOIN so SEMI/FINAL placeholder rows (NULL teams) are included,
    # but filter out placeholders that still have no teams assigned yet.
    cursor.execute("""
        SELECT m.match_id,
               t1.team_name AS team1,
               t2.team_name AS team2,
               m.stage
        FROM matches m
        LEFT JOIN teams t1 ON m.team1_id = t1.team_id
        LEFT JOIN teams t2 ON m.team2_id = t2.team_id
        WHERE m.tournament_id=%s
          AND m.is_completed=0
          AND m.team1_id IS NOT NULL
          AND m.team2_id IS NOT NULL
        ORDER BY FIELD(m.stage,'LEAGUE','SEMI','FINAL'), m.match_id
    """, (tournament_id,))

    data = cursor.fetchall()
    
    for m in data:
        m['is_host'] = is_host

    cursor.close()
    conn.close()

    return jsonify(data)

@tournament_bp.route("/tournament-completed/<int:tournament_id>")
def tournament_completed(tournament_id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT m.*, 
               t1.team_name AS team1,
               t2.team_name AS team2
        FROM matches m
        JOIN teams t1 ON m.team1_id = t1.team_id
        JOIN teams t2 ON m.team2_id = t2.team_id
        WHERE m.tournament_id=%s AND m.is_completed=1
        ORDER BY m.match_id
    """, (tournament_id,))

    data = cursor.fetchall()
    cursor.close()
    conn.close()

    return jsonify(data)
    
@tournament_bp.route("/prepare-match/<int:match_id>", methods=["POST"])
def prepare_match(match_id):
    # Now that we let the host select playing 11 at Toss, we don't need to auto-insert them here.
    # Just return success so the frontend continues to redirect to /toss/<match_id>
    try:
        return jsonify({"message": "Ready for Toss"})
    except Exception as e:
        print("🔥 ERROR:", str(e))
        return jsonify({"error": str(e)}), 500
    
@tournament_bp.route("/points-table/<int:tournament_id>")
def get_points_table(tournament_id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # ================= GET ALL MATCHES =================
    cursor.execute("""
        SELECT 
            m.*,
            t1.team_name AS team1_name,
            t2.team_name AS team2_name

        FROM matches m
        JOIN teams t1 ON m.team1_id = t1.team_id
        JOIN teams t2 ON m.team2_id = t2.team_id

        WHERE m.tournament_id = %s
          AND m.is_completed = 1
          AND m.stage = 'LEAGUE'
    """, (tournament_id,))

    matches = cursor.fetchall()

    # ================= CALCULATE =================
    table = {}

    for m in matches:

        t1 = m["team1_id"]
        t2 = m["team2_id"]

        # init
        for t in [t1, t2]:
            if t not in table:
                table[t] = {
                    "team_name": m["team1_name"] if t == t1 else m["team2_name"],
                    "played": 0,
                    "wins": 0,
                    "losses": 0,
                    "points": 0,
                    "runs_scored": 0,
                    "overs_faced": 0,
                    "runs_conceded": 0,
                    "overs_bowled": 0
                }

        # increment played
        table[t1]["played"] += 1
        table[t2]["played"] += 1

        r1 = m["team1_score"]
        r2 = m["team2_score"]

        o1 = float(m["team1_overs"])
        o2 = float(m["team2_overs"])

        # runs + overs
        table[t1]["runs_scored"] += r1
        table[t1]["overs_faced"] += o1
        table[t1]["runs_conceded"] += r2
        table[t1]["overs_bowled"] += o2

        table[t2]["runs_scored"] += r2
        table[t2]["overs_faced"] += o2
        table[t2]["runs_conceded"] += r1
        table[t2]["overs_bowled"] += o1

        # result
        if r1 > r2:
            table[t1]["wins"] += 1
            table[t1]["points"] += 2
            table[t2]["losses"] += 1

        elif r2 > r1:
            table[t2]["wins"] += 1
            table[t2]["points"] += 2
            table[t1]["losses"] += 1

    # ================= CALCULATE NRR =================
    result = []

    for t_id, t in table.items():

        if t["overs_faced"] == 0 or t["overs_bowled"] == 0:
            nrr = 0
        else:
            nrr = (t["runs_scored"] / t["overs_faced"]) - \
                  (t["runs_conceded"] / t["overs_bowled"])

        result.append({
            "team_name": t["team_name"],
            "matches_played": t["played"],
            "wins": t["wins"],
            "losses": t["losses"],
            "points": t["points"],
            "nrr": round(nrr, 2)
        })

    # ================= SORT =================
    result.sort(key=lambda x: (-x["points"], -x["nrr"]))

    cursor.close()
    conn.close()

    return jsonify(result)

# ============================================================
# 🏆 SMART AUTO KNOCKOUT GENERATOR
# Handles both ≤3 teams (direct final) and ≥4 teams (semi+final)
# Call this after all league matches are done, and again after
# both semi-finals are done to auto-fill the final.
# ============================================================
@tournament_bp.route("/auto-generate-knockouts/<int:tournament_id>", methods=["POST"])
def auto_generate_knockouts(tournament_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Get tournament info
        cursor.execute("SELECT match_type, hosted_by FROM tournaments WHERE tournament_id=%s", (tournament_id,))
        t = cursor.fetchone()
        if not t:
            return jsonify({"error": "Tournament not found"}), 404
        t_type = t['match_type'] or 'T20'
        host_id = t['hosted_by']

        # Get existing knockout matches
        cursor.execute("""
            SELECT match_id, team1_id, team2_id,
                   team1_score, team2_score, is_completed
            FROM matches
            WHERE tournament_id=%s AND stage='SEMI'
            ORDER BY match_id ASC
        """, (tournament_id,))
        existing_semis = cursor.fetchall()

        cursor.execute("""
            SELECT match_id, team1_id, team2_id, is_completed
            FROM matches
            WHERE tournament_id=%s AND stage='FINAL'
            ORDER BY match_id ASC
        """, (tournament_id,))
        existing_finals = cursor.fetchall()

        semis_completed = [s for s in existing_semis if s['is_completed']]

        # ===================================================
        # PHASE 2: Both semi-finals done → generate FINAL
        # ===================================================
        if len(semis_completed) >= 2:
            winner_ids = []
            for semi in semis_completed[:2]:
                if semi['team1_score'] > semi['team2_score']:
                    winner_ids.append(semi['team1_id'])
                else:
                    winner_ids.append(semi['team2_id'])

            if len(winner_ids) < 2:
                return jsonify({"error": "Could not determine semi-final winners"}), 400

            if existing_finals:
                cursor.execute(
                    "UPDATE matches SET team1_id=%s, team2_id=%s WHERE match_id=%s",
                    (winner_ids[0], winner_ids[1], existing_finals[0]['match_id'])
                )
            else:
                cursor.execute("""
                    INSERT INTO matches
                    (team1_id, team2_id, tournament_id, match_type, is_completed, created_by, stage)
                    VALUES (%s,%s,%s,%s,0,%s,'FINAL')
                """, (winner_ids[0], winner_ids[1], tournament_id, t_type, host_id))

            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"message": "Final generated from semi-final winners", "stage": "FINAL"})

        # ===================================================
        # PHASE 1: All league matches done → generate SEMI/FINAL
        # ===================================================
        cursor.execute("""
            SELECT COUNT(*) AS pending FROM matches
            WHERE tournament_id=%s AND stage='LEAGUE' AND is_completed=0
        """, (tournament_id,))
        pending_league = cursor.fetchone()['pending']

        if pending_league > 0:
            return jsonify({"error": "League matches not yet completed"}), 400

        # Get top teams sorted by points then NRR
        cursor.execute("""
            SELECT
                t.team_id,
                t.team_name,
                SUM(
                    CASE
                        WHEN m.team1_id = t.team_id AND m.team1_score > m.team2_score THEN 2
                        WHEN m.team2_id = t.team_id AND m.team2_score > m.team1_score THEN 2
                        ELSE 0
                    END
                ) AS points,
                (
                    SUM(CASE WHEN m.team1_id = t.team_id THEN m.team1_score ELSE m.team2_score END)
                    / NULLIF(SUM(CASE WHEN m.team1_id = t.team_id THEN m.team1_overs ELSE m.team2_overs END), 0)
                    -
                    SUM(CASE WHEN m.team1_id = t.team_id THEN m.team2_score ELSE m.team1_score END)
                    / NULLIF(SUM(CASE WHEN m.team1_id = t.team_id THEN m.team2_overs ELSE m.team1_overs END), 0)
                ) AS nrr
            FROM teams t
            JOIN matches m ON t.team_id IN (m.team1_id, m.team2_id)
            WHERE m.tournament_id=%s AND m.is_completed=1 AND m.stage='LEAGUE'
            GROUP BY t.team_id, t.team_name
            ORDER BY points DESC, nrr DESC
        """, (tournament_id,))
        top_teams = cursor.fetchall()

        num_teams = len(top_teams)
        if num_teams < 2:
            return jsonify({"error": "Not enough teams to generate knockouts"}), 400

        # ── ≤ 3 teams: Direct Final between top 2 ──────────────────
        if num_teams <= 3:
            t1_id = top_teams[0]['team_id']
            t2_id = top_teams[1]['team_id']

            # Remove any stale SEMI/FINAL with NULL teams
            cursor.execute("""
                DELETE FROM matches
                WHERE tournament_id=%s AND stage IN ('SEMI','FINAL')
                  AND team1_id IS NULL AND is_completed=0
            """, (tournament_id,))

            if existing_finals:
                cursor.execute(
                    "UPDATE matches SET team1_id=%s, team2_id=%s WHERE match_id=%s",
                    (t1_id, t2_id, existing_finals[0]['match_id'])
                )
            else:
                cursor.execute("""
                    INSERT INTO matches
                    (team1_id, team2_id, tournament_id, match_type, is_completed, created_by, stage)
                    VALUES (%s,%s,%s,%s,0,%s,'FINAL')
                """, (t1_id, t2_id, tournament_id, t_type, host_id))

            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"message": "Final generated (direct — 3-team format)", "stage": "FINAL"})

        # ── ≥ 4 teams: Semi-Finals (1st vs 4th, 2nd vs 3rd) ────────
        t1_id = top_teams[0]['team_id']
        t2_id = top_teams[1]['team_id']
        t3_id = top_teams[2]['team_id']
        t4_id = top_teams[3]['team_id'] if num_teams >= 4 else top_teams[2]['team_id']

        pair1 = (t1_id, t4_id)  # 1st vs 4th
        pair2 = (t2_id, t3_id)  # 2nd vs 3rd

        # Remove any stale NULL-team SEMI placeholders
        cursor.execute("""
            DELETE FROM matches
            WHERE tournament_id=%s AND stage='SEMI'
              AND team1_id IS NULL AND is_completed=0
        """, (tournament_id,))

        # Re-fetch after delete
        cursor.execute("""
            SELECT match_id FROM matches
            WHERE tournament_id=%s AND stage='SEMI'
            ORDER BY match_id ASC
        """, (tournament_id,))
        live_semis = cursor.fetchall()

        if len(live_semis) >= 2:
            cursor.execute("UPDATE matches SET team1_id=%s, team2_id=%s WHERE match_id=%s",
                           (pair1[0], pair1[1], live_semis[0]['match_id']))
            cursor.execute("UPDATE matches SET team1_id=%s, team2_id=%s WHERE match_id=%s",
                           (pair2[0], pair2[1], live_semis[1]['match_id']))
        else:
            for tA, tB in [pair1, pair2]:
                cursor.execute("""
                    INSERT INTO matches
                    (team1_id, team2_id, tournament_id, match_type, is_completed, created_by, stage)
                    VALUES (%s,%s,%s,%s,0,%s,'SEMI')
                """, (tA, tB, tournament_id, t_type, host_id))

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Semi-Finals generated", "stage": "SEMI"})

    except Exception as e:
        print("🔥 ERROR auto_generate_knockouts:", str(e))
        return jsonify({"error": str(e)}), 500


# Keep these for backward compatibility (now just delegate)
@tournament_bp.route("/generate-semi-finals/<int:tournament_id>", methods=["POST"])
def generate_semi_finals(tournament_id):
    return auto_generate_knockouts(tournament_id)

@tournament_bp.route("/generate-final/<int:tournament_id>", methods=["POST"])
def generate_final(tournament_id):
    return auto_generate_knockouts(tournament_id)


# ================= TOURNAMENT STATS =================
@tournament_bp.route("/tournament-stats/<int:tournament_id>")
def tournament_stats(tournament_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT t.tournament_name, t.is_completed, t.man_of_tournament_id,
                   m.winner AS final_winner, u.name AS mott_name
            FROM tournaments t
            LEFT JOIN matches m
                ON m.tournament_id = t.tournament_id AND m.stage = 'FINAL' AND m.is_completed = 1
            LEFT JOIN users u
                ON t.man_of_tournament_id = u.user_id
            WHERE t.tournament_id = %s
        """, (tournament_id,))
        tourney = cursor.fetchone()

        if not tourney:
            return jsonify({"error": "Tournament not found"}), 404

        if tourney['is_completed'] == 1 and not tourney['final_winner']:
            cursor.execute("""
                SELECT t.team_name,
                    SUM(
                        CASE 
                            WHEN m.team1_id = t.team_id AND m.team1_score > m.team2_score THEN 2
                            WHEN m.team2_id = t.team_id AND m.team2_score > m.team1_score THEN 2
                            ELSE 0
                        END
                    ) AS points
                FROM teams t
                JOIN matches m ON t.team_id IN (m.team1_id, m.team2_id)
                WHERE m.tournament_id=%s AND m.is_completed=1
                GROUP BY t.team_id, t.team_name
                ORDER BY points DESC
                LIMIT 1
            """, (tournament_id,))
            top_team = cursor.fetchone()
            if top_team:
                tourney['final_winner'] = top_team['team_name']

        # ===== TOP SCORER =====
        cursor.execute("""
            SELECT u.name,
                   SUM(CASE WHEN b.extra_type IN ('WIDE','BYE','LEG_BYE') THEN 0 ELSE b.runs_scored END) AS total_runs,
                   COUNT(CASE WHEN b.extra_type = 'WIDE' THEN NULL ELSE 1 END) AS balls_faced
            FROM ball_by_ball b
            JOIN users u ON b.striker_id = u.user_id
            JOIN matches m ON b.match_id = m.match_id
            WHERE m.tournament_id = %s
            GROUP BY b.striker_id, u.name
            ORDER BY total_runs DESC
            LIMIT 1
        """, (tournament_id,))
        top_scorer = cursor.fetchone()

        # ===== TOP WICKET TAKER =====
        cursor.execute("""
            SELECT u.name,
                   COUNT(*) AS wickets
            FROM ball_by_ball b
            JOIN users u ON b.bowler_id = u.user_id
            JOIN matches m ON b.match_id = m.match_id
            WHERE m.tournament_id = %s
              AND b.is_wicket = 1
              AND b.wicket_type != 'RUNOUT'
            GROUP BY b.bowler_id, u.name
            ORDER BY wickets DESC
            LIMIT 1
        """, (tournament_id,))
        top_wicket = cursor.fetchone()

        cursor.close()
        conn.close()

        return jsonify({
            "tournament_name": tourney["tournament_name"],
            "is_completed": tourney["is_completed"],
            "final_winner": tourney["final_winner"],
            "man_of_tournament_name": tourney["mott_name"],
            "top_scorer": top_scorer,
            "top_wicket_taker": top_wicket
        })

    except Exception as e:
        print("🔥 ERROR:", str(e))
        return jsonify({"error": str(e)}), 500


# ================= MARK TOURNAMENT COMPLETE =================
@tournament_bp.route("/complete-tournament/<int:tournament_id>", methods=["POST"])
def complete_tournament(tournament_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE tournaments SET is_completed = 1
            WHERE tournament_id = %s
        """, (tournament_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": "Tournament marked complete"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================= TOURNAMENT LEADERBOARDS =================
@tournament_bp.route("/tournament-leaderboards/<int:tournament_id>")
def tournament_leaderboards(tournament_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT u.name, t.team_name,
                   SUM(CASE WHEN b.extra_type IN ('WIDE','BYE','LEG_BYE') THEN 0 ELSE b.runs_scored END) AS runs,
                   COUNT(CASE WHEN b.extra_type = 'WIDE' THEN NULL ELSE 1 END) AS balls,
                   (SUM(CASE WHEN b.extra_type IN ('WIDE','BYE','LEG_BYE') THEN 0 ELSE b.runs_scored END) / NULLIF(COUNT(CASE WHEN b.extra_type = 'WIDE' THEN NULL ELSE 1 END), 0) * 100) AS strike_rate
            FROM ball_by_ball b
            JOIN users u ON b.striker_id = u.user_id
            JOIN matches m ON b.match_id = m.match_id
            LEFT JOIN match_players mp ON mp.match_id = m.match_id AND mp.user_id = u.user_id
            LEFT JOIN teams t ON t.team_id = mp.team_id
            WHERE m.tournament_id = %s
            GROUP BY u.user_id, u.name, t.team_name
            HAVING runs > 0
            ORDER BY runs DESC, strike_rate DESC
            LIMIT 10
        """, (tournament_id,))
        top_batsmen = cursor.fetchall()

        cursor.execute("""
            SELECT u.name, t.team_name,
                   COUNT(CASE WHEN b.is_wicket = 1 AND b.wicket_type != 'RUNOUT' THEN 1 END) AS wickets,
                   COUNT(CASE WHEN b.extra_type IN ('WIDE', 'NO_BALL') THEN NULL ELSE 1 END) / 6.0 AS overs,
                   SUM(b.runs_scored + IFNULL(b.extra_runs, 0)) AS runs_conceded,
                   (SUM(b.runs_scored + IFNULL(b.extra_runs, 0)) / NULLIF(COUNT(CASE WHEN b.extra_type IN ('WIDE', 'NO_BALL') THEN NULL ELSE 1 END) / 6.0, 0)) AS economy
            FROM ball_by_ball b
            JOIN users u ON b.bowler_id = u.user_id
            JOIN matches m ON b.match_id = m.match_id
            LEFT JOIN match_players mp ON mp.match_id = m.match_id AND mp.user_id = u.user_id
            LEFT JOIN teams t ON t.team_id = mp.team_id
            WHERE m.tournament_id = %s
            GROUP BY u.user_id, u.name, t.team_name
            HAVING wickets > 0 OR overs > 0
            ORDER BY wickets DESC, economy ASC
            LIMIT 10
        """, (tournament_id,))
        top_bowlers = cursor.fetchall()
        
        cursor.execute("""
            SELECT u.user_id, u.name, t.team_name,
                   MAX(IFNULL(bat.runs, 0)) AS bat_runs,
                   MAX(IFNULL(bowl.wickets, 0)) AS bowl_wickets,
                   MAX(IFNULL(field.dismissals, 0)) AS field_dismissals,
                   (MAX(IFNULL(bat.runs, 0)) + MAX(IFNULL(bowl.wickets, 0)) * 20 + MAX(IFNULL(field.dismissals, 0)) * 10) AS points
            FROM users u
            JOIN match_players mp ON u.user_id = mp.user_id
            JOIN matches m ON mp.match_id = m.match_id
            LEFT JOIN teams t ON mp.team_id = t.team_id
            LEFT JOIN (
                SELECT b.striker_id, mp_inner.team_id, 
                       SUM(CASE WHEN b.extra_type IN ('WIDE','BYE','LEG_BYE') THEN 0 ELSE b.runs_scored END) AS runs
                FROM ball_by_ball b 
                JOIN match_players mp_inner ON b.match_id = mp_inner.match_id AND b.striker_id = mp_inner.user_id
                JOIN matches m_inner ON b.match_id = m_inner.match_id
                WHERE m_inner.tournament_id = %s
                GROUP BY b.striker_id, mp_inner.team_id
            ) bat ON bat.striker_id = u.user_id AND bat.team_id = mp.team_id
            LEFT JOIN (
                SELECT b.bowler_id, mp_inner.team_id, COUNT(*) AS wickets
                FROM ball_by_ball b 
                JOIN match_players mp_inner ON b.match_id = mp_inner.match_id AND b.bowler_id = mp_inner.user_id
                JOIN matches m_inner ON b.match_id = m_inner.match_id
                WHERE m_inner.tournament_id = %s AND b.is_wicket = 1 AND b.wicket_type != 'RUNOUT'
                GROUP BY b.bowler_id, mp_inner.team_id
            ) bowl ON bowl.bowler_id = u.user_id AND bowl.team_id = mp.team_id
            LEFT JOIN (
                SELECT b.fielder_id, mp_inner.team_id, COUNT(*) AS dismissals
                FROM ball_by_ball b 
                JOIN match_players mp_inner ON b.match_id = mp_inner.match_id AND b.fielder_id = mp_inner.user_id
                JOIN matches m_inner ON b.match_id = m_inner.match_id
                WHERE m_inner.tournament_id = %s AND b.is_wicket = 1 AND b.fielder_id IS NOT NULL
                GROUP BY b.fielder_id, mp_inner.team_id
            ) field ON field.fielder_id = u.user_id AND field.team_id = mp.team_id
            WHERE m.tournament_id = %s
            GROUP BY u.user_id, u.name, t.team_name
            HAVING points > 0
            ORDER BY points DESC
            LIMIT 10
        """, (tournament_id, tournament_id, tournament_id, tournament_id))
        top_mvps = cursor.fetchall()
        
        cursor.close()
        conn.close()

        # Convert Decimals to float/int to avoid JSON serialization errors
        for p in top_batsmen:
            p['runs'] = int(p['runs'] or 0)
            p['balls'] = int(p['balls'] or 0)
            p['strike_rate'] = float(p['strike_rate'] or 0)
            
        for p in top_bowlers:
            p['wickets'] = int(p['wickets'] or 0)
            p['overs'] = float(p['overs'] or 0)
            p['runs_conceded'] = int(p['runs_conceded'] or 0)
            p['economy'] = float(p['economy'] or 0)
            
        for p in top_mvps:
            p['bat_runs'] = int(p['bat_runs'] or 0)
            p['bowl_wickets'] = int(p['bowl_wickets'] or 0)
            p['field_dismissals'] = int(p['field_dismissals'] or 0)
            p['points'] = float(p['points'] or 0)

        return jsonify({
            "top_batsmen": top_batsmen,
            "top_bowlers": top_bowlers,
            "top_mvps": top_mvps
        })

    except Exception as e:
        print("🔥 ERROR:", str(e))
        return jsonify({"error": str(e)}), 500

# ================= SELECT MOTT (MAN OF THE TOURNAMENT) =================
@tournament_bp.route("/select-mott/<int:tournament_id>")
def select_mott(tournament_id):
    if 'user_id' not in session:
        return redirect(url_for('auth_bp.login'))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT u.user_id, u.name, t.team_name,
                   MAX(IFNULL(bat.runs, 0)) AS bat_runs,
                   MAX(IFNULL(bowl.wickets, 0)) AS bowl_wickets,
                   MAX(IFNULL(field.dismissals, 0)) AS field_dismissals,
                   (MAX(IFNULL(bat.runs, 0)) + MAX(IFNULL(bowl.wickets, 0)) * 20 + MAX(IFNULL(field.dismissals, 0)) * 10) AS points
            FROM users u
            JOIN match_players mp ON u.user_id = mp.user_id
            JOIN matches m ON mp.match_id = m.match_id
            LEFT JOIN teams t ON mp.team_id = t.team_id
            LEFT JOIN (
                SELECT b.striker_id, mp_inner.team_id, 
                       SUM(CASE WHEN b.extra_type IN ('WIDE','BYE','LEG_BYE') THEN 0 ELSE b.runs_scored END) AS runs
                FROM ball_by_ball b 
                JOIN match_players mp_inner ON b.match_id = mp_inner.match_id AND b.striker_id = mp_inner.user_id
                JOIN matches m_inner ON b.match_id = m_inner.match_id
                WHERE m_inner.tournament_id = %s
                GROUP BY b.striker_id, mp_inner.team_id
            ) bat ON bat.striker_id = u.user_id AND bat.team_id = mp.team_id
            LEFT JOIN (
                SELECT b.bowler_id, mp_inner.team_id, COUNT(*) AS wickets
                FROM ball_by_ball b 
                JOIN match_players mp_inner ON b.match_id = mp_inner.match_id AND b.bowler_id = mp_inner.user_id
                JOIN matches m_inner ON b.match_id = m_inner.match_id
                WHERE m_inner.tournament_id = %s AND b.is_wicket = 1 AND b.wicket_type != 'RUNOUT'
                GROUP BY b.bowler_id, mp_inner.team_id
            ) bowl ON bowl.bowler_id = u.user_id AND bowl.team_id = mp.team_id
            LEFT JOIN (
                SELECT b.fielder_id, mp_inner.team_id, COUNT(*) AS dismissals
                FROM ball_by_ball b 
                JOIN match_players mp_inner ON b.match_id = mp_inner.match_id AND b.fielder_id = mp_inner.user_id
                JOIN matches m_inner ON b.match_id = m_inner.match_id
                WHERE m_inner.tournament_id = %s AND b.is_wicket = 1 AND b.fielder_id IS NOT NULL
                GROUP BY b.fielder_id, mp_inner.team_id
            ) field ON field.fielder_id = u.user_id AND field.team_id = mp.team_id
            WHERE m.tournament_id = %s
            GROUP BY u.user_id, u.name, t.team_name
            HAVING points > 0
            ORDER BY points DESC
            LIMIT 10
        """, (tournament_id, tournament_id, tournament_id, tournament_id))
        top_mvps = cursor.fetchall()
        
        cursor.execute("SELECT tournament_name FROM tournaments WHERE tournament_id = %s", (tournament_id,))
        tid = cursor.fetchone()
        tname = tid['tournament_name'] if tid else f"Tournament #{tournament_id}"

        return render_template("select_mott.html", tournament_id=tournament_id, tournament_name=tname, players=top_mvps)
    except Exception as e:
        print("🔥 ERROR in MOTT:", str(e))
        return str(e), 500
    finally:
        cursor.close()
        conn.close()

@tournament_bp.route('/save-mott', methods=['POST'])
def save_mott():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    tournament_id = data.get("tournament_id")
    mott_id = data.get("mott_id")
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE tournaments 
            SET man_of_tournament_id = %s, is_completed = 1 
            WHERE tournament_id = %s
        """, (mott_id, tournament_id))
        conn.commit()
        return jsonify({"message": "Man of the Tournament saved successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()