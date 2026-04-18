from flask import Blueprint, request, jsonify, session
from db import get_connection

team_bp = Blueprint('team', __name__)


# ==========================
# 🏏 GET ALL PLAYERS (for dropdown)
# ==========================
@team_bp.route('/players', methods=['GET'])
def get_players():

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT user_id, name, profile_pic FROM users")
    players = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(players)


# ==========================
# 🏏 CREATE TEAM (FINAL)
# ==========================
@team_bp.route('/create-team', methods=['POST'])
def create_team():

    data = request.get_json()

    team_name = data.get('team_name')
    captain_id = data.get('captain_id')
    players = data.get('players')   # list of user_ids

    # Basic validation
    if not team_name or not captain_id or not players:
        return jsonify({"error": "Missing data"}), 400

    # Rule: team size 11–15
    if len(players) < 11 or len(players) > 15:
        return jsonify({"error": "Team must have 11 to 15 players"}), 400

    # Rule: captain must be in players list
    if captain_id not in players:
        return jsonify({"error": "Captain must be in player list"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 🏏 Create team
        cursor.execute(
            "INSERT INTO teams (team_name, created_by) VALUES (%s, %s)",
            (team_name, captain_id)
        )
        team_id = cursor.lastrowid

        # 👥 Insert players
        for user_id in players:

            is_captain = (user_id == captain_id)

            cursor.execute("""
                INSERT INTO team_members (team_id, user_id, is_captain, is_vice_captain)
                VALUES (%s, %s, %s, %s)
            """, (team_id, user_id, is_captain, False))

        conn.commit()

        return jsonify({
            "message": "Team created successfully",
            "team_id": team_id
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

    finally:
        cursor.close()
        conn.close()


# ==========================
# 👥 GET MY TEAMS
# ==========================
@team_bp.route('/my-teams/<int:user_id>', methods=['GET'])
def get_my_teams(user_id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT t.team_id, t.team_name
    FROM teams t
    JOIN team_members tm ON t.team_id = tm.team_id
    WHERE tm.user_id = %s
    """

    cursor.execute(query, (user_id,))
    teams = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(teams)

@team_bp.route('/team-players/<int:team_id>', methods=['GET'])
def get_team_players(team_id):

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT u.user_id, u.name, tm.is_captain
        FROM team_members tm
        JOIN users u ON tm.user_id = u.user_id
        WHERE tm.team_id = %s
    """, (team_id,))

    players = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(players)

# ==========================
# 👑 GET MY CREATED TEAMS
# ==========================
@team_bp.route('/my-created-teams', methods=['GET'])
def get_created_teams():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT t.team_id, t.team_name
            FROM teams t
            WHERE t.created_by = %s
        """, (user_id,))
        teams = cursor.fetchall()

        for team in teams:
            cursor.execute("""
                SELECT u.user_id, u.name, tm.is_captain
                FROM team_members tm
                JOIN users u ON tm.user_id = u.user_id
                WHERE tm.team_id = %s
            """, (team['team_id'],))
            team['players'] = cursor.fetchall()
            
        return jsonify(teams)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# ==========================
# ✏️ UPDATE TEAM
# ==========================
@team_bp.route('/update-team/<int:team_id>', methods=['POST'])
def update_team(team_id):
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    team_name = data.get('team_name')
    captain_id = data.get('captain_id')
    players = data.get('players')   # list of user_ids

    # Basic validation
    if not team_name or not captain_id or not players:
        return jsonify({"error": "Missing data"}), 400

    if len(players) < 11 or len(players) > 15:
        return jsonify({"error": "Team must have 11 to 15 players"}), 400

    if captain_id not in players:
        return jsonify({"error": "Captain must be in player list"}), 400

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Check if the user owns this team
        cursor.execute("SELECT created_by FROM teams WHERE team_id = %s", (team_id,))
        team = cursor.fetchone()
        if not team or team[0] != user_id:
            return jsonify({"error": "Unauthorized or team not found"}), 403

        # Update team name
        cursor.execute("UPDATE teams SET team_name = %s WHERE team_id = %s", (team_name, team_id))

        # Update members
        cursor.execute("DELETE FROM team_members WHERE team_id = %s", (team_id,))
        
        for p_id in players:
            is_captain = (p_id == captain_id)
            cursor.execute("""
                INSERT INTO team_members (team_id, user_id, is_captain, is_vice_captain)
                VALUES (%s, %s, %s, %s)
            """, (team_id, p_id, is_captain, False))

        conn.commit()
        return jsonify({"message": "Team updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

# ==========================
# 🛡️ GET ALL TEAMS (For Dashboard)
# ==========================
@team_bp.route('/all-teams', methods=['GET'])
def get_all_teams():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT team_id, team_name FROM teams")
        teams = cursor.fetchall()
        return jsonify(teams)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()