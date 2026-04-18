from flask import Blueprint, request, jsonify, render_template, session
from sqlalchemy import over
from db import get_connection
from flask import redirect

match_bp = Blueprint('match', __name__)


# ==========================
# 🧠 HELPER FUNCTION (NEW)
# ==========================
def is_valid_overs(overs):
    decimal = round(overs - int(overs), 1)
    return decimal in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]


# ==========================
# 🏏 GET ALL TEAMS
# ==========================
@match_bp.route('/teams', methods=['GET'])
def get_teams():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT team_id, team_name FROM teams")
    teams = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(teams)


# ==========================
# 🏏 SCHEDULE MATCH
# ==========================
@match_bp.route('/schedule-match', methods=['POST'])
def schedule_match():

    data = request.get_json()

    team1_id = data.get('team1_id')
    team2_id = data.get('team2_id')
    match_date = data.get('match_date')
    match_type = data.get('match_type')

    created_by = session.get('user_id')
    if not created_by:
        return jsonify({"error": "Unauthorized"}), 401

    if not team1_id or not team2_id or not match_date or not match_type:
        return jsonify({"error": "Missing data"}), 400

    if team1_id == team2_id:
        return jsonify({"error": "Both teams cannot be same"}), 400

    if match_type not in ["T20", "ODI", "TEST"]:
        return jsonify({"error": "Invalid match type"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT team_id FROM teams WHERE team_id = %s", (team1_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Team 1 not found"}), 404

        cursor.execute("SELECT team_id FROM teams WHERE team_id = %s", (team2_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Team 2 not found"}), 404

        cursor.execute("""
            SELECT tm1.user_id
            FROM team_members tm1
            JOIN team_members tm2 
            ON tm1.user_id = tm2.user_id
            WHERE tm1.team_id = %s AND tm2.team_id = %s
        """, (team1_id, team2_id))

        if cursor.fetchall():
            return jsonify({
                "error": "Both teams have common players"
            }), 400

        cursor.execute("""
            INSERT INTO matches (team1_id, team2_id, match_date, match_type, created_by)
            VALUES (%s, %s, %s, %s, %s)
        """, (team1_id, team2_id, match_date, match_type, created_by))

        conn.commit()

        return jsonify({
            "message": "Match scheduled",
            "match_id": cursor.lastrowid
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

    finally:
        cursor.close()
        conn.close()


# ==========================
# 🏏 ADD PLAYING 11
# ==========================
@match_bp.route('/add-playing11', methods=['POST'])
def add_playing11():

    data = request.get_json()

    match_id = data.get('match_id')
    team_id = data.get('team_id')
    players = data.get('players')

    current_user = session.get('user_id')
    if not current_user:
        return jsonify({"error": "Unauthorized"}), 401

    if not match_id or not team_id or not players:
        return jsonify({"error": "Missing data"}), 400

    if len(players) != 11:
        return jsonify({"error": "Select exactly 11 players"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT is_finalized FROM matches WHERE match_id = %s", (match_id,))
        match = cursor.fetchone()

        if match[0] == 1:
            return jsonify({"error": "Match already finalized"}), 400

        cursor.execute("SELECT created_by FROM matches WHERE match_id = %s", (match_id,))
        creator = cursor.fetchone()

        if creator[0] != current_user:
            return jsonify({"error": "Not allowed"}), 403

        cursor.execute("""
            SELECT * FROM match_players
            WHERE match_id = %s AND team_id = %s
        """, (match_id, team_id))

        if cursor.fetchone():
            return jsonify({"error": "Playing 11 already added for this team"}), 400

        for user_id in players:
            cursor.execute("""
                SELECT * FROM team_members
                WHERE team_id = %s AND user_id = %s
            """, (team_id, user_id))

            if not cursor.fetchone():
                return jsonify({"error": "Invalid player"}), 400

        for user_id in players:
            cursor.execute("""
                INSERT INTO match_players (match_id, team_id, user_id)
                VALUES (%s, %s, %s)
            """, (match_id, team_id, user_id))

        cursor.execute("""
            SELECT COUNT(DISTINCT team_id)
            FROM match_players
            WHERE match_id = %s
        """, (match_id,))

        team_count = cursor.fetchone()[0]

        if team_count == 2:
            cursor.execute("""
                UPDATE matches SET is_finalized = 1
                WHERE match_id = %s
            """, (match_id,))

            conn.commit()

            return jsonify({"message": "Match finalized successfully"}), 200

        conn.commit()

        return jsonify({"message": "Playing 11 added for team"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

    finally:
        cursor.close()
        conn.close()




@match_bp.route('/my-upcoming-matches', methods=['GET'])
def my_upcoming_matches():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT m.*, 
               t1.team_name AS team1_name,
               t2.team_name AS team2_name
        FROM matches m
        JOIN teams t1 ON m.team1_id = t1.team_id
        JOIN teams t2 ON m.team2_id = t2.team_id
        WHERE m.created_by = %s AND m.is_completed = FALSE AND m.tournament_id IS NULL
        ORDER BY m.match_id DESC
        LIMIT 30
    """, (user_id,))

    matches = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(matches)

@match_bp.route('/my-completed-matches', methods=['GET'])
def my_completed_matches():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            m.match_id,
            m.match_date,
            m.match_type,

            t1.team_name AS team1_name,
            t2.team_name AS team2_name,

            m.team1_score,
            m.team2_score,

            m.team1_wickets,
            m.team2_wickets,

            m.team1_overs,
            m.team2_overs,

            m.winner,            -- ✅ ADD THIS
            m.is_completed       -- ✅ ADD THIS

        FROM matches m
        JOIN teams t1 ON m.team1_id = t1.team_id
        JOIN teams t2 ON m.team2_id = t2.team_id

        WHERE m.created_by = %s AND m.is_completed = TRUE AND m.tournament_id IS NULL
        ORDER BY m.match_id DESC, m.match_date DESC
        LIMIT 30
    """, (user_id,))

    matches = cursor.fetchall()

    # 🔥 FIX FLOAT ISSUE
    for m in matches:
        m['team1_overs'] = round(m['team1_overs'], 1)
        m['team2_overs'] = round(m['team2_overs'], 1)

    cursor.close()
    conn.close()

    return jsonify(matches)


@match_bp.route('/toss/<int:match_id>')
def toss_page(match_id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            m.match_id,
            m.tournament_id,
            m.total_overs,
            t1.team_name AS team1_name,
            t2.team_name AS team2_name,
            m.team1_id,
            m.team2_id
        FROM matches m
        JOIN teams t1 ON m.team1_id = t1.team_id
        JOIN teams t2 ON m.team2_id = t2.team_id
        WHERE m.match_id = %s
    """, (match_id,))

    match = cursor.fetchone()

    # If it's a tournament match, fetch overs from tournament table
    if match and match['tournament_id']:
        cursor.execute("SELECT overs FROM tournaments WHERE tournament_id=%s", (match['tournament_id'],))
        tour = cursor.fetchone()
        if tour and tour['overs']:
            match['total_overs'] = tour['overs']

    # Fetch full squads for Playing 11 selection
    cursor.execute("""
        SELECT m.user_id, u.name, u.role
        FROM team_members m
        JOIN users u ON m.user_id = u.user_id
        WHERE m.team_id = %s
    """, (match['team1_id'],))
    team1_squad = cursor.fetchall()

    cursor.execute("""
        SELECT m.user_id, u.name, u.role
        FROM team_members m
        JOIN users u ON m.user_id = u.user_id
        WHERE m.team_id = %s
    """, (match['team2_id'],))
    team2_squad = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("toss.html", match=match, team1_squad=team1_squad, team2_squad=team2_squad)

@match_bp.route('/save-toss', methods=['POST'])
def save_toss():

    data = request.get_json()

    match_id = data.get("match_id")
    toss_winner_id = data.get("toss_winner_id")
    decision = data.get("decision")   # BAT / BOWL
    total_overs = data.get("total_overs")
    team1_11 = data.get("team1_11") # List of user IDs for Team 1
    team2_11 = data.get("team2_11") # List of user IDs for Team 2

    if not match_id or not toss_winner_id or not decision or not total_overs:
        return jsonify({"error": "Missing fundamental toss data"}), 400

    if not team1_11 or not team2_11 or len(team1_11) != 11 or len(team2_11) != 11:
        return jsonify({"error": "You must select exactly 11 players for both teams."}), 400

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 1. Update Match Details
        cursor.execute("""
            UPDATE matches
            SET toss_winner_id = %s,
                toss_decision = %s,
                total_overs = %s,
                is_started = TRUE,
                is_finalized = 1
            WHERE match_id = %s
        """, (toss_winner_id, decision, total_overs, match_id))

        # 2. Get teams for match
        cursor.execute("SELECT team1_id, team2_id FROM matches WHERE match_id=%s", (match_id,))
        m = cursor.fetchone()

        # 3. Fresh Start for match_players (clear any previous attempts)
        cursor.execute("DELETE FROM match_players WHERE match_id = %s", (match_id,))

        # 4. Insert Playing 11 for Team 1
        for uid in team1_11:
            cursor.execute("INSERT INTO match_players (match_id, team_id, user_id) VALUES (%s,%s,%s)", (match_id, m['team1_id'], uid))

        # 5. Insert Playing 11 for Team 2
        for uid in team2_11:
            cursor.execute("INSERT INTO match_players (match_id, team_id, user_id) VALUES (%s,%s,%s)", (match_id, m['team2_id'], uid))

        conn.commit()

        return jsonify({"message": "Toss and Playing 11 saved successfully!"}), 200

    except Exception as e:
        print("save_toss error:", e)
        return jsonify({"error": str(e)}), 400

    finally:
        cursor.close()
        conn.close()

@match_bp.route('/select-players/<int:match_id>')
def select_players(match_id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # 🔍 Get match + toss info
    cursor.execute("""
        SELECT * FROM matches WHERE match_id = %s
    """, (match_id,))
    match = cursor.fetchone()

    team1_id = match['team1_id']
    team2_id = match['team2_id']
    toss_winner = match['toss_winner_id']
    decision = match['toss_decision']

    # 🧠 Decide batting team
    if decision == "BAT":
        batting_team = toss_winner
    else:
        batting_team = team2_id if toss_winner == team1_id else team1_id

    bowling_team = team2_id if batting_team == team1_id else team1_id

    # 🔍 Get players
    cursor.execute("""
        SELECT 
            user_id,
            (SELECT name FROM users WHERE users.user_id = match_players.user_id) AS name
        FROM match_players
        WHERE match_id = %s AND team_id = %s
    """, (match_id, batting_team))
    batting_players = cursor.fetchall()

    cursor.execute("""
        SELECT 
            user_id,
            (SELECT name FROM users WHERE users.user_id = match_players.user_id) AS name
        FROM match_players
        WHERE match_id = %s AND team_id = %s
    """, (match_id, bowling_team))
    bowling_players = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("select_players.html",
                           match=match,
                           batting_players=batting_players,
                           bowling_players=bowling_players,
                           batting_team=batting_team,
                           bowling_team=bowling_team)


@match_bp.route('/start-innings', methods=['POST'])
def start_innings():

    data = request.get_json()

    match_id = data['match_id']
    striker = data['striker']
    non_striker = data['non_striker']
    bowler = data['bowler']

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO current_match_state
            (match_id, innings, striker_id, non_striker_id, bowler_id, last_bowler_id)
            VALUES (%s, 1, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            striker_id = VALUES(striker_id),
            non_striker_id = VALUES(non_striker_id),
            bowler_id = VALUES(bowler_id),
            last_bowler_id = VALUES(last_bowler_id)
        """, (match_id, striker, non_striker, bowler, bowler))

        conn.commit()

        return jsonify({"message": "Innings started"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

    finally:
        cursor.close()
        conn.close()

@match_bp.route('/live-score/<int:match_id>')
def live_score(match_id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # 🔥 GET tournament_id ALSO
    cursor.execute("""
        SELECT tournament_id 
        FROM matches
        WHERE match_id = %s
    """, (match_id,))

    match = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "live_score.html",
        match_id=match_id,
        tournament_id=match["tournament_id"]
    )

@match_bp.route('/add-ball', methods=['POST'])
def add_ball():

    data = request.get_json()

    match_id = int(data['match_id'])
    runs = int(data.get('runs', 0))
    extra_type = data.get('type')
    extra_runs = int(data.get('extra_runs', 0))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT * FROM current_match_state
            WHERE match_id = %s
        """, (match_id,))
        state = cursor.fetchone()

        over = state['current_over']
        ball = state['current_ball']
        striker = state['striker_id']
        non_striker = state['non_striker_id']
        bowler = state['bowler_id']
        innings = state['innings']

        # store current values FIRST
        store_over = over
        store_ball = ball
        store_striker = striker
        store_non_striker = non_striker

        legal_ball = True
        new_over = False

        if extra_type in ("WIDE", "NO_BALL"):
            legal_ball = False

        if legal_ball:
            

            # AFTER storing → increment
            ball += 1

            new_over = False

            if ball >= 6:
                ball = 0
                over += 1
                new_over = True
                striker, non_striker = non_striker, striker

        total_runs = runs + extra_runs

        # ===== STRIKE LOGIC =====
        if extra_type is None:
            if runs % 2 == 1:
                striker, non_striker = non_striker, striker

        elif extra_type in ("BYE", "LEG_BYE"):
            if extra_runs % 2 == 1:
                striker, non_striker = non_striker, striker

        elif extra_type == "NO_BALL":
            if runs % 2 == 1:
                striker, non_striker = non_striker, striker

        # =======================

        cursor.execute("""
        INSERT INTO ball_by_ball
        (match_id, innings, over_number, ball_number,
        striker_id, non_striker_id, bowler_id,
        runs_scored, extra_type, extra_runs)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            match_id, innings, store_over, store_ball,   # ✅ USE STORED VALUES
            store_striker, store_non_striker, bowler,    # ✅ USE STORED STRIKER VALUES
            runs, extra_type, extra_runs
        ))

        cursor.execute("""
            UPDATE current_match_state
            SET total_runs = total_runs + %s,
                current_over = %s,
                current_ball = %s,
                striker_id = %s,
                non_striker_id = %s
            WHERE match_id = %s
        """, (total_runs, over, ball, striker, non_striker, match_id))

        # ===== GET MATCH =====
        cursor.execute("""
            SELECT total_overs, team1_id, team2_id,
                   team1_score, team2_score
            FROM matches WHERE match_id = %s
        """, (match_id,))
        match = cursor.fetchone()

        max_overs = match['total_overs']

        # ===== LIVE SCORE =====
        cursor.execute("""
            SELECT total_runs, total_wickets, current_over, current_ball
            FROM current_match_state
            WHERE match_id = %s
        """, (match_id,))
        live = cursor.fetchone()

        runs_live = live['total_runs']
        wickets_live = live['total_wickets']

        if live['current_ball'] == 0:
            overs_live = live['current_over']
        else:
            overs_live = float(f"{live['current_over']}.{live['current_ball']}")

        if over >= max_overs:
            overs_live = float(max_overs)

        # batting team
        cursor.execute("""
            SELECT team_id FROM match_players
            WHERE match_id = %s AND user_id = %s
        """, (match_id, striker))
        batting_team = cursor.fetchone()['team_id']

        # update score
        if batting_team == match['team1_id']:
            cursor.execute("""
                UPDATE matches
                SET team1_score = %s,
                    team1_wickets = %s,
                    team1_overs = %s
                WHERE match_id = %s
            """, (runs_live, wickets_live, overs_live, match_id))
        else:
            cursor.execute("""
                UPDATE matches
                SET team2_score = %s,
                    team2_wickets = %s,
                    team2_overs = %s
                WHERE match_id = %s
            """, (runs_live, wickets_live, overs_live, match_id))

        # ===== TEAM NAMES =====
        cursor.execute("""
            SELECT t1.team_name AS team1_name, t2.team_name AS team2_name
            FROM matches m, teams t1, teams t2
            WHERE m.match_id = %s
            AND m.team1_id = t1.team_id
            AND m.team2_id = t2.team_id
        """, (match_id,))
        teams = cursor.fetchone()

        team1_name = teams['team1_name']
        team2_name = teams['team2_name']

        # ===== TARGET CHECK =====
        if innings == 2:

            if batting_team == match['team1_id']:
                team1_score = runs_live
                target = match['team2_score'] + 1
            else:
                team2_score = runs_live
                target = match['team1_score'] + 1

            if (batting_team == match['team1_id'] and team1_score >= target) or \
               (batting_team == match['team2_id'] and team2_score >= target):

                winner = team1_name if batting_team == match['team1_id'] else team2_name

                cursor.execute("SELECT stage, tournament_id FROM matches WHERE match_id = %s", (match_id,))
                match_info = cursor.fetchone()

                cursor.execute("""
                    UPDATE matches
                    SET is_completed = TRUE,
                        winner = %s
                    WHERE match_id = %s
                """, (winner, match_id))

                # If ALL matches in the tournament are completed, we now handle tournament completion via MOTT selection.
                if match_info and match_info['tournament_id']:
                    pass

                conn.commit()

                return jsonify({"match_end": True, "winner": winner}), 200

        # ===== WICKET CHECK =====
        cursor.execute("""
            SELECT total_wickets FROM current_match_state
            WHERE match_id = %s
        """, (match_id,))
        updated = cursor.fetchone()

        # ===== INNINGS / MATCH =====
        if over >= max_overs or updated['total_wickets'] >= 10:

            if innings == 1:

                new_team = match['team2_id'] if batting_team == match['team1_id'] else match['team1_id']

                # Reset state to innings 2 but leave player selection to the user
                cursor.execute("""
                    UPDATE current_match_state
                    SET innings = 2,
                        total_runs = 0,
                        total_wickets = 0,
                        current_over = 0,
                        current_ball = 0,
                        striker_id = NULL,
                        non_striker_id = NULL,
                        bowler_id = NULL,
                        last_bowler_id = NULL
                    WHERE match_id = %s
                """, (match_id,))

                conn.commit()

                return jsonify({
                    "innings_break": True,
                    "new_batting_team_id": new_team,
                    "new_bowling_team_id": batting_team
                }), 200

            else:
                # final result
                if match['team1_score'] > match['team2_score']:
                    winner = team1_name
                elif match['team2_score'] > match['team1_score']:
                    winner = team2_name
                else:
                    winner = "DRAW"

                cursor.execute("""
                    SELECT stage, tournament_id FROM matches WHERE match_id = %s
                """, (match_id,))
                match_info = cursor.fetchone()

                cursor.execute("""
                    UPDATE matches
                    SET is_completed = TRUE,
                        winner = %s
                    WHERE match_id = %s
                """, (winner, match_id))

                # If ALL matches in the tournament are completed, we now handle tournament completion via MOTT selection.
                if match_info and match_info['tournament_id']:
                    pass

                conn.commit()

                return jsonify({"match_end": True, "winner": winner}), 200

        conn.commit()

        return jsonify({"new_over": new_over}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

    finally:
        cursor.close()
        conn.close()

@match_bp.route('/get-live/<int:match_id>')
def get_live(match_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM current_match_state WHERE match_id = %s", (match_id,))
        state = cursor.fetchone()
        if not state:
            return jsonify({"error": "Match state not found"}), 404

        innings = state['innings']

        def get_player_stats(uid):
            if not uid:
                return {"name": "—", "runs": 0, "balls": 0}
            cursor.execute("SELECT name FROM users WHERE user_id = %s", (uid,))
            name = cursor.fetchone()['name']
            
            cursor.execute("""
                SELECT IFNULL(SUM(CASE WHEN extra_type IN ('BYE', 'LEG_BYE', 'WIDE') THEN 0 ELSE runs_scored END), 0) as runs,
                       COUNT(CASE WHEN extra_type = 'WIDE' THEN NULL ELSE 1 END) as balls
                FROM ball_by_ball
                WHERE match_id = %s AND innings = %s AND striker_id = %s
            """, (match_id, innings, uid))
            stats = cursor.fetchone()
            return {"name": name, "runs": stats['runs'], "balls": stats['balls']}

        striker_data = get_player_stats(state['striker_id'])
        ns_data = get_player_stats(state['non_striker_id'])

        # Bowler Stats
        bowler_data = {"name": "—", "runs": 0, "wickets": 0, "balls": 0}
        if state['bowler_id']:
            cursor.execute("SELECT name FROM users WHERE user_id = %s", (state['bowler_id'],))
            bowler_data['name'] = cursor.fetchone()['name']
            
            cursor.execute("""
                SELECT SUM(runs_scored + IFNULL(extra_runs, 0)) as runs,
                       COUNT(CASE WHEN extra_type IN ('WIDE', 'NO_BALL') THEN NULL ELSE 1 END) as balls,
                       COUNT(CASE WHEN is_wicket = 1 AND wicket_type != 'RUNOUT' THEN 1 END) as wickets
                FROM ball_by_ball
                WHERE match_id = %s AND innings = %s AND bowler_id = %s
            """, (match_id, innings, state['bowler_id']))
            b_stats = cursor.fetchone()
            bowler_data['runs'] = b_stats['runs'] or 0
            bowler_data['balls'] = b_stats['balls'] or 0
            bowler_data['wickets'] = b_stats['wickets'] or 0

        # Recent Balls
        cursor.execute("""
            SELECT runs_scored, extra_type, extra_runs, is_wicket, wicket_type
            FROM ball_by_ball
            WHERE match_id = %s AND innings = %s
            ORDER BY ball_id DESC LIMIT 12
        """, (match_id, innings))
        recent_balls = cursor.fetchall()

        # 2nd innings target info
        target = None
        balls_remaining = None
        if innings == 2:
            cursor.execute("""
                SELECT team1_score, team2_score, total_overs,
                       team1_id, team2_id, toss_winner_id, toss_decision
                FROM matches WHERE match_id = %s
            """, (match_id,))
            m = cursor.fetchone()
            if m:
                if m['toss_decision'] == 'BAT':
                    first_innings_score = m['team1_score'] if m['toss_winner_id'] == m['team1_id'] else m['team2_score']
                else:
                    first_innings_score = m['team2_score'] if m['toss_winner_id'] == m['team1_id'] else m['team1_score']

                if first_innings_score is not None:
                    target = int(first_innings_score) + 1
                    balls_used = int(state['current_over']) * 6 + int(state['current_ball'])
                    balls_remaining = (int(m['total_overs']) * 6) - balls_used

        return jsonify({
            "total_runs": state['total_runs'],
            "total_wickets": state['total_wickets'],
            "current_over": state['current_over'],
            "current_ball": state['current_ball'],
            "innings": innings,
            "target": target,
            "balls_remaining": balls_remaining,
            "striker": striker_data,
            "non_striker": ns_data,
            "bowler": bowler_data,
            "recent_balls": recent_balls[::-1]  # Return in chronological order
        })
    finally:
        cursor.close()
        conn.close()

@match_bp.route('/add-wicket', methods=['POST'])
def add_wicket():
    data = request.get_json()

    match_id = int(data['match_id'])
    wicket_type = data['type']
    new_batsman = data.get('new_batsman')
    fielder_id = data.get('fielder_id')
    out_batter = data.get('out_batter')
    runout_runs = int(data.get('runout_runs', 0))

    if new_batsman:
        new_batsman = int(new_batsman)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM current_match_state WHERE match_id = %s", (match_id,))
        state = cursor.fetchone()

        striker = state['striker_id']
        non_striker = state['non_striker_id']
        bowler = state['bowler_id']
        over = state['current_over']
        ball = state['current_ball']
        innings = state['innings']

        # 🟢 next ball logic
        store_over = over
        store_ball = ball
        new_over = False

        ball += 1
        if ball >= 6:
            ball = 0
            over += 1
            new_over = True

        # 🟢 Determine who got dismissed
        if wicket_type == 'RUNOUT' and out_batter == 'NON_STRIKER':
            dismissed_player = non_striker
        else:
            dismissed_player = striker
            
        # 🟢 Runs scored before runout
        run_score = runout_runs if wicket_type == 'RUNOUT' else 0

        # 🟢 insert wicket ball
        cursor.execute("""
            INSERT INTO ball_by_ball
            (match_id, innings, over_number, ball_number,
             striker_id, non_striker_id, bowler_id,
             runs_scored, is_wicket, wicket_type, fielder_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s)
        """, (match_id, innings, store_over, store_ball, striker, non_striker, bowler, run_score, wicket_type, fielder_id))

        if run_score > 0:
            cursor.execute("""
                UPDATE current_match_state
                SET total_runs = total_runs + %s
                WHERE match_id = %s
            """, (run_score, match_id))

        # ✅ store dismissed player
        cursor.execute("INSERT INTO dismissed_players (match_id, player_id) VALUES (%s, %s)", (match_id, dismissed_player))

        # 🔥 HANDLE STRIKE CHANGE
        pos_striker_end = striker
        pos_non_striker_end = non_striker

        # Reverse the logic as per user request (even runs = swap, odd runs = no swap)
        if wicket_type == 'RUNOUT' and runout_runs % 2 == 0 and runout_runs > 0:
            pos_striker_end, pos_non_striker_end = pos_non_striker_end, pos_striker_end

        # Replace dismissed player with new batsman at their end
        if pos_striker_end == dismissed_player:
            pos_striker_end = new_batsman if new_batsman else None
        else:
            pos_non_striker_end = new_batsman if new_batsman else None

        # End of over: swap strike again
        if new_over and pos_striker_end and pos_non_striker_end:
            pos_striker_end, pos_non_striker_end = pos_non_striker_end, pos_striker_end

        new_striker = pos_striker_end
        new_non_striker = pos_non_striker_end

        # 🔥 UPDATE STATE
        if new_striker or new_non_striker:
            cursor.execute("""
                UPDATE current_match_state
                SET striker_id = %s, non_striker_id = %s, total_wickets = total_wickets + 1, current_over = %s, current_ball = %s
                WHERE match_id = %s
            """, (new_striker, new_non_striker, over, ball, match_id))
        else:
            cursor.execute("""
                UPDATE current_match_state
                SET total_wickets = total_wickets + 1, current_over = %s, current_ball = %s
                WHERE match_id = %s
            """, (over, ball, match_id))

        # ===== GET MATCH FOR UPDATES =====
        cursor.execute("SELECT total_overs, team1_id, team2_id, team1_score, team2_score FROM matches WHERE match_id = %s", (match_id,))
        match = cursor.fetchone()
        max_overs = match['total_overs']

        # ===== LIVE SCORE & MATCH UPDATES =====
        cursor.execute("SELECT total_runs, total_wickets, current_over, current_ball FROM current_match_state WHERE match_id = %s", (match_id,))
        live = cursor.fetchone()
        runs_live = live['total_runs']
        wickets_live = live['total_wickets']
        overs_live = live['current_over'] if live['current_ball'] == 0 else float(f"{live['current_over']}.{live['current_ball']}")
        if over >= max_overs: overs_live = float(max_overs)

        cursor.execute("SELECT team_id FROM match_players WHERE match_id = %s AND user_id = %s", (match_id, non_striker))
        batting_team = cursor.fetchone()['team_id']

        if batting_team == match['team1_id']:
            cursor.execute("UPDATE matches SET team1_score = %s, team1_wickets = %s, team1_overs = %s WHERE match_id = %s", (runs_live, wickets_live, overs_live, match_id))
        else:
            cursor.execute("UPDATE matches SET team2_score = %s, team2_wickets = %s, team2_overs = %s WHERE match_id = %s", (runs_live, wickets_live, overs_live, match_id))

        cursor.execute("SELECT t1.team_name AS team1_name, t2.team_name AS team2_name FROM matches m, teams t1, teams t2 WHERE m.match_id = %s AND m.team1_id = t1.team_id AND m.team2_id = t2.team_id", (match_id,))
        teams = cursor.fetchone()

        # ===== INNINGS / MATCH LOGIC =====
        if over >= max_overs or live['total_wickets'] >= 10:
            if innings == 1:
                new_team = match['team2_id'] if batting_team == match['team1_id'] else match['team1_id']
                # Reset to innings 2 but let user pick batsmen and bowler
                cursor.execute("""
                    UPDATE current_match_state SET innings = 2, total_runs = 0, total_wickets = 0, current_over = 0, current_ball = 0,
                    striker_id = NULL, non_striker_id = NULL, bowler_id = NULL, last_bowler_id = NULL WHERE match_id = %s
                """, (match_id,))
                conn.commit()
                return jsonify({
                    "innings_break": True,
                    "new_batting_team_id": new_team,
                    "new_bowling_team_id": batting_team
                }), 200
            else:
                if match['team1_score'] > match['team2_score']: winner = teams['team1_name']
                elif match['team2_score'] > match['team1_score']: winner = teams['team2_name']
                else: winner = "DRAW"
                cursor.execute("SELECT stage, tournament_id FROM matches WHERE match_id = %s", (match_id,))
                match_info = cursor.fetchone()
                cursor.execute("UPDATE matches SET is_completed = TRUE, winner = %s WHERE match_id = %s", (winner, match_id))
                # If FINAL, tournament completion is now handled via MOTT selection
                if match_info and match_info['stage'] == 'FINAL' and match_info['tournament_id']:
                    pass
                conn.commit()
                return jsonify({"match_end": True, "winner": winner}), 200

        conn.commit()
        return jsonify({"message": "Wicket added", "new_over": new_over}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400

    finally:
        cursor.close()
        conn.close()

# ==========================
# 🏏 START SECOND INNINGS (user picks batsmen + bowler)
# ==========================
@match_bp.route('/start-second-innings', methods=['POST'])
def start_second_innings():
    data = request.get_json()
    match_id = data['match_id']
    striker = data['striker']
    non_striker = data['non_striker']
    bowler = data['bowler']

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            UPDATE current_match_state
            SET striker_id = %s,
                non_striker_id = %s,
                bowler_id = %s,
                last_bowler_id = %s
            WHERE match_id = %s
        """, (striker, non_striker, bowler, bowler, match_id))
        conn.commit()
        return jsonify({"message": "Second innings started"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


# ==========================
# 🏏 GET BATTING PLAYERS BY TEAM (for 2nd innings selection)
# ==========================
@match_bp.route('/innings-batting-players/<int:match_id>/<int:team_id>')
def innings_batting_players(match_id, team_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT mp.user_id,
                   u.name
            FROM match_players mp
            JOIN users u ON mp.user_id = u.user_id
            WHERE mp.match_id = %s AND mp.team_id = %s
        """, (match_id, team_id))
        players = cursor.fetchall()
        return jsonify(players)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()


@match_bp.route('/available-batsmen/<int:match_id>')

def available_batsmen(match_id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # current state
    cursor.execute("""
        SELECT * FROM current_match_state
        WHERE match_id = %s
    """, (match_id,))
    state = cursor.fetchone()

    # 🧠 Determine batting team strictly
    cursor.execute("SELECT team1_id, team2_id, toss_winner_id, toss_decision FROM matches WHERE match_id = %s", (match_id,))
    m = cursor.fetchone()
    
    innings = state['innings']
    if innings == 1:
        if m['toss_decision'] == 'BAT':
            batting_team = m['toss_winner_id']
        else:
            batting_team = m['team2_id'] if m['toss_winner_id'] == m['team1_id'] else m['team1_id']
    else:
        if m['toss_decision'] == 'BAT':
            batting_team = m['team2_id'] if m['toss_winner_id'] == m['team1_id'] else m['team1_id']
        else:
            batting_team = m['toss_winner_id']

    # all batting players
    cursor.execute("""
        SELECT mp.user_id,
               u.name
        FROM match_players mp
        JOIN users u ON mp.user_id = u.user_id
        WHERE mp.match_id = %s AND mp.team_id = %s
    """, (match_id, batting_team))

    players = cursor.fetchall()

    # dismissed players
    cursor.execute("""
        SELECT player_id FROM dismissed_players
        WHERE match_id = %s
    """, (match_id,))
    dismissed = [d['player_id'] for d in cursor.fetchall()]

    available = [
        p for p in players
        if p['user_id'] not in (
            state['striker_id'],
            state['non_striker_id'],
            *dismissed
        )
    ]

    cursor.close()
    conn.close()

    return jsonify(available)

@match_bp.route('/bowling-players/<int:match_id>')
def bowling_players(match_id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # 🔍 get current state
    cursor.execute("SELECT bowler_id, striker_id, non_striker_id, innings FROM current_match_state WHERE match_id = %s", (match_id,))
    state = cursor.fetchone()

    # 🧠 Determine bowling team strictly
    cursor.execute("SELECT team1_id, team2_id, toss_winner_id, toss_decision FROM matches WHERE match_id = %s", (match_id,))
    m = cursor.fetchone()
    
    innings = state['innings']
    if innings == 1:
        if m['toss_decision'] == 'BAT':
            batting_team = m['toss_winner_id']
        else:
            batting_team = m['team2_id'] if m['toss_winner_id'] == m['team1_id'] else m['team1_id']
    else:
        if m['toss_decision'] == 'BAT':
            batting_team = m['team2_id'] if m['toss_winner_id'] == m['team1_id'] else m['team1_id']
        else:
            batting_team = m['toss_winner_id']
            
    bowling_team = m['team2_id'] if batting_team == m['team1_id'] else m['team1_id']

    # 🔍 get players
    cursor.execute("""
        SELECT user_id,
               (SELECT name FROM users WHERE users.user_id = match_players.user_id) AS name
        FROM match_players
        WHERE match_id = %s AND team_id = %s
    """, (match_id, bowling_team))

    players = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(players)

@match_bp.route('/change-bowler', methods=['POST'])
def change_bowler():

    data = request.get_json()

    match_id = data['match_id']
    new_bowler = data['bowler']

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT bowler_id FROM current_match_state
        WHERE match_id = %s
    """, (match_id,))
    state = cursor.fetchone()

    last_bowler = state['bowler_id']

    if last_bowler is None:
        last_bowler = -1

    if new_bowler == last_bowler:
        return jsonify({"error": "Same bowler cannot bowl consecutive overs"}), 400

    cursor.execute("""
        UPDATE current_match_state
        SET bowler_id = %s
        WHERE match_id = %s
    """, (new_bowler, match_id))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "Bowler updated"})

@match_bp.route('/scorecard')
def scorecard():

    match_id = request.args.get('match_id')

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # ✅ FIXED MATCH QUERY (team_name instead of name)
    cursor.execute("""
        SELECT m.*, 
               t1.team_name AS team1_name, 
               t2.team_name AS team2_name,
               trn.is_completed AS tournament_completed,
               trn.man_of_tournament_id
        FROM matches m
        JOIN teams t1 ON m.team1_id = t1.team_id
        JOIN teams t2 ON m.team2_id = t2.team_id
        LEFT JOIN tournaments trn ON m.tournament_id = trn.tournament_id
        WHERE m.match_id = %s
    """, (match_id,))
    match = cursor.fetchone()

    # ================= TEAM 1 BATTING =================
    cursor.execute("""
        SELECT 
            u.name,

            SUM(
                CASE 
                    WHEN b.extra_type IN ('BYE','LEG_BYE') THEN 0 
                    ELSE b.runs_scored 
                END
            ) AS runs,

            SUM(CASE WHEN b.runs_scored = 4 THEN 1 ELSE 0 END) AS fours,
            SUM(CASE WHEN b.runs_scored = 6 THEN 1 ELSE 0 END) AS sixes,

            COUNT(CASE WHEN b.extra_type = 'WIDE' THEN NULL ELSE 1 END) AS balls,

            ROUND(
                SUM(
                    CASE 
                        WHEN b.extra_type IN ('BYE','LEG_BYE','WIDE') THEN 0 
                        ELSE b.runs_scored 
                    END
                ) * 100.0 / NULLIF(COUNT(CASE WHEN b.extra_type = 'WIDE' THEN NULL ELSE 1 END), 0), 2
            ) AS strike_rate,

            -- 🔥 dismissal info
            MAX(b.is_wicket) AS is_out,
            MAX(b.wicket_type) AS wicket_type,
            MAX(f.name) AS fielder_name,
            MAX(bowler.name) AS bowler_name

        FROM ball_by_ball b
        JOIN users u ON b.striker_id = u.user_id
        LEFT JOIN users f ON b.fielder_id = f.user_id
        LEFT JOIN users bowler ON b.bowler_id = bowler.user_id

        WHERE b.match_id = %s
        AND u.user_id IN (
            SELECT user_id FROM match_players
            WHERE match_id = %s AND team_id = %s
        )

        GROUP BY u.user_id, u.name
    """, (match_id, match_id, match['team1_id']))

    team1_batting = cursor.fetchall()

    # ================= TEAM 2 BATTING =================
    cursor.execute("""
        SELECT 
            u.name,

            SUM(
                CASE 
                    WHEN b.extra_type IN ('BYE','LEG_BYE') THEN 0 
                    ELSE b.runs_scored 
                END
            ) AS runs,

            SUM(CASE WHEN b.runs_scored = 4 THEN 1 ELSE 0 END) AS fours,
            SUM(CASE WHEN b.runs_scored = 6 THEN 1 ELSE 0 END) AS sixes,

            COUNT(CASE WHEN b.extra_type = 'WIDE' THEN NULL ELSE 1 END) AS balls,

            ROUND(
                SUM(
                    CASE 
                        WHEN b.extra_type IN ('BYE','LEG_BYE','WIDE') THEN 0 
                        ELSE b.runs_scored 
                    END
                ) * 100.0 / NULLIF(COUNT(CASE WHEN b.extra_type = 'WIDE' THEN NULL ELSE 1 END), 0), 2
            ) AS strike_rate,

            -- 🔥 dismissal info
            MAX(b.is_wicket) AS is_out,
            MAX(b.wicket_type) AS wicket_type,
            MAX(f.name) AS fielder_name,
            MAX(bowler.name) AS bowler_name

        FROM ball_by_ball b
        JOIN users u ON b.striker_id = u.user_id
        LEFT JOIN users f ON b.fielder_id = f.user_id
        LEFT JOIN users bowler ON b.bowler_id = bowler.user_id

        WHERE b.match_id = %s
        AND u.user_id IN (
            SELECT user_id FROM match_players
            WHERE match_id = %s AND team_id = %s
        )

        GROUP BY u.user_id, u.name
    """, (match_id, match_id, match['team2_id']))

    team2_batting = cursor.fetchall()

    def format_dismissal(p):
        if not p['is_out']:
            return "not out"

        wt = p['wicket_type']
        f = p['fielder_name']
        b = p['bowler_name']

        if wt == "CAUGHT":
            return f"c {f} b {b}"
        elif wt == "BOWLED":
            return f"b {b}"
        elif wt == "STUMPED":
            return f"st {f} b {b}"
        elif wt == "RUNOUT":
            return f"run out ({f})"
        else:
            return wt.lower()


    # apply to both teams
    for p in team1_batting:
        p['dismissal'] = format_dismissal(p)

    for p in team2_batting:
        p['dismissal'] = format_dismissal(p)

    # ================= TEAM 1 BOWLING =================
    cursor.execute("""
        SELECT 
            u.name,

            CONCAT(
                FLOOR(SUM(CASE 
                    WHEN b.extra_type IN ('WIDE','NO_BALL') THEN 0 
                    ELSE 1 
                END)/6),
                '.',
                MOD(SUM(CASE 
                    WHEN b.extra_type IN ('WIDE','NO_BALL') THEN 0 
                    ELSE 1 
                END),6)
            ) AS overs,

            SUM(b.runs_scored + IFNULL(b.extra_runs,0)) AS runs,

            SUM(CASE WHEN b.is_wicket = TRUE AND b.wicket_type != 'RUNOUT' THEN 1 ELSE 0 END) AS wickets,

            ROUND(
                SUM(b.runs_scored + IFNULL(b.extra_runs,0)) /
                (SUM(CASE 
                    WHEN b.extra_type IN ('WIDE','NO_BALL') THEN 0 
                    ELSE 1 
                END)/6), 2
            ) AS economy

        FROM ball_by_ball b
        JOIN users u ON b.bowler_id = u.user_id

        WHERE b.match_id = %s
        AND u.user_id IN (
            SELECT user_id FROM match_players
            WHERE match_id = %s AND team_id = %s
        )

        GROUP BY u.user_id, u.name
    """, (match_id, match_id, match['team2_id']))
    team1_bowling = cursor.fetchall()

    # ================= TEAM 2 BOWLING =================
    cursor.execute("""
        SELECT 
            u.name,

            CONCAT(
                FLOOR(SUM(CASE 
                    WHEN b.extra_type IN ('WIDE','NO_BALL') THEN 0 
                    ELSE 1 
                END)/6),
                '.',
                MOD(SUM(CASE 
                    WHEN b.extra_type IN ('WIDE','NO_BALL') THEN 0 
                    ELSE 1 
                END),6)
            ) AS overs,

            SUM(b.runs_scored + IFNULL(b.extra_runs,0)) AS runs,

            SUM(CASE WHEN b.is_wicket = TRUE AND b.wicket_type != 'RUNOUT' THEN 1 ELSE 0 END) AS wickets,

            ROUND(
                SUM(b.runs_scored + IFNULL(b.extra_runs,0)) /
                (SUM(CASE 
                    WHEN b.extra_type IN ('WIDE','NO_BALL') THEN 0 
                    ELSE 1 
                END)/6), 2
            ) AS economy

        FROM ball_by_ball b
        JOIN users u ON b.bowler_id = u.user_id

        WHERE b.match_id = %s
        AND u.user_id IN (
            SELECT user_id FROM match_players
            WHERE match_id = %s AND team_id = %s
        )

        GROUP BY u.user_id, u.name
    """, (match_id, match_id, match['team1_id']))
    team2_bowling = cursor.fetchall()

    # ================= TEAM 1 EXTRAS =================
    cursor.execute("""
        SELECT SUM(IFNULL(extra_runs,0)) AS extras
        FROM ball_by_ball
        WHERE match_id = %s
        AND striker_id IN (
            SELECT user_id FROM match_players
            WHERE match_id = %s AND team_id = %s
        )
    """, (match_id, match_id, match['team1_id']))
    team1_extras = cursor.fetchone()['extras'] or 0


    # ================= TEAM 2 EXTRAS =================
    cursor.execute("""
        SELECT SUM(IFNULL(extra_runs,0)) AS extras
        FROM ball_by_ball
        WHERE match_id = %s
        AND striker_id IN (
            SELECT user_id FROM match_players
            WHERE match_id = %s AND team_id = %s
        )
    """, (match_id, match_id, match['team2_id']))
    team2_extras = cursor.fetchone()['extras'] or 0

    # ================= TOP 5 MVPs AND MOTM =================
    cursor.execute("SELECT man_of_the_match FROM matches WHERE match_id = %s", (match_id,))
    motm_row = cursor.fetchone()
    motm_id = motm_row['man_of_the_match'] if motm_row else None

    # Calculate points for all match players
    cursor.execute("""
        SELECT 
            u.user_id,
            u.name,
            IFNULL(bat.runs, 0) AS runs,
            IFNULL(bowl.wickets, 0) AS wickets,
            IFNULL(field.dismissals, 0) AS dismissals,
            (IFNULL(bat.runs, 0) * 1 + IFNULL(bowl.wickets, 0) * 20 + IFNULL(field.dismissals, 0) * 10) AS points
        FROM users u
        JOIN match_players mp ON u.user_id = mp.user_id
        LEFT JOIN (
            SELECT striker_id, 
                   SUM(CASE WHEN extra_type IN ('WIDE','BYE','LEG_BYE') THEN 0 ELSE runs_scored END) AS runs
            FROM ball_by_ball
            WHERE match_id = %s
            GROUP BY striker_id
        ) bat ON bat.striker_id = u.user_id
        LEFT JOIN (
            SELECT bowler_id, COUNT(*) AS wickets
            FROM ball_by_ball
            WHERE match_id = %s AND is_wicket = 1 AND wicket_type != 'RUNOUT'
            GROUP BY bowler_id
        ) bowl ON bowl.bowler_id = u.user_id
        LEFT JOIN (
            SELECT fielder_id, COUNT(*) AS dismissals
            FROM ball_by_ball
            WHERE match_id = %s AND is_wicket = 1 AND fielder_id IS NOT NULL
            GROUP BY fielder_id
        ) field ON field.fielder_id = u.user_id
        WHERE mp.match_id = %s
        ORDER BY points DESC
    """, (match_id, match_id, match_id, match_id))
    
    all_players = cursor.fetchall()
    top_mvps = all_players[:5]
    
    motm_player = None
    if motm_id:
        for p in all_players:
            if p['user_id'] == motm_id:
                motm_player = p
                break

    return render_template(
        "scorecard.html",
        match=match,
        team1_batting=team1_batting,
        team2_batting=team2_batting,
        team1_bowling=team1_bowling,
        team2_bowling=team2_bowling,
        team1_extras=team1_extras,
        team2_extras=team2_extras,
        top_mvps=top_mvps,
        motm_player=motm_player
    )

@match_bp.route('/select-motm/<int:match_id>')
def select_motm(match_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM matches WHERE match_id = %s", (match_id,))
    match = cursor.fetchone()
    
    cursor.execute("""
        SELECT 
            u.user_id,
            u.name,
            IFNULL(bat.runs, 0) AS runs,
            IFNULL(bowl.wickets, 0) AS wickets,
            IFNULL(field.dismissals, 0) AS dismissals,
            (IFNULL(bat.runs, 0) * 1 + IFNULL(bowl.wickets, 0) * 20 + IFNULL(field.dismissals, 0) * 10) AS points
        FROM users u
        JOIN match_players mp ON u.user_id = mp.user_id
        LEFT JOIN (
            SELECT striker_id, 
                   SUM(CASE WHEN extra_type IN ('WIDE','BYE','LEG_BYE') THEN 0 ELSE runs_scored END) AS runs
            FROM ball_by_ball
            WHERE match_id = %s
            GROUP BY striker_id
        ) bat ON bat.striker_id = u.user_id
        LEFT JOIN (
            SELECT bowler_id, COUNT(*) AS wickets
            FROM ball_by_ball
            WHERE match_id = %s AND is_wicket = 1 AND wicket_type != 'RUNOUT'
            GROUP BY bowler_id
        ) bowl ON bowl.bowler_id = u.user_id
        LEFT JOIN (
            SELECT fielder_id, COUNT(*) AS dismissals
            FROM ball_by_ball
            WHERE match_id = %s AND is_wicket = 1 AND fielder_id IS NOT NULL
            GROUP BY fielder_id
        ) field ON field.fielder_id = u.user_id
        WHERE mp.match_id = %s
        ORDER BY points DESC
    """, (match_id, match_id, match_id, match_id))
    
    players = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return render_template("select_motm.html", match=match, players=players)

@match_bp.route('/save-motm', methods=['POST'])
def save_motm():
    data = request.json
    match_id = data.get("match_id")
    motm_id = data.get("motm_id")
    
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE matches SET man_of_the_match = %s WHERE match_id = %s", (motm_id, match_id))
        conn.commit()
        return jsonify({"message": "Man of the match saved successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()