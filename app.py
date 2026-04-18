from flask import Flask, render_template
from routes.auth import auth_bp
from routes.team import team_bp   # ✅ NEW LINE
from routes.match import match_bp
from routes.tournament import tournament_bp
from routes.dashboard import dashboard_bp

from flask import render_template



app = Flask(__name__)

app.secret_key = "mysecretkey123"  # Change this to a secure key in production
app.register_blueprint(auth_bp)   # existing
app.register_blueprint(team_bp)   # ✅ NEW LINE
app.register_blueprint(match_bp)  # existing
app.register_blueprint(tournament_bp)
app.register_blueprint(dashboard_bp)



@app.route("/")
def home():
    return render_template("auth.html")

@app.route("/team")
def team_page():
    return render_template("team.html")

@app.route("/match")
def match_page():
    return render_template("match.html")

@app.route("/tourney")
def tourney_page():
    return render_template("tournament.html")

@app.route("/host-tournament")
def host_page():
    return render_template("host_tournament.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/mytourney")
def my_tourney_page():
    return render_template("mytourney.html")

@app.route("/tournament/<int:tournament_id>")
def tournament_detail_page(tournament_id):
    from db import get_connection
    from flask import redirect
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT is_started FROM tournaments WHERE tournament_id=%s", (tournament_id,))
    t = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if t and t['is_started']:
        return redirect(f"/tournament/{tournament_id}/matches")
        
    return render_template("tournament_detail.html", tournament_id=tournament_id)

@app.route("/tournament/<int:tournament_id>/matches")
def tournament_matches_page(tournament_id):
    return render_template("tournament_matches.html")

@app.route('/profile')
@app.route('/profile/<int:user_id>')
def profile(user_id=None):
    from flask import session
    if user_id is None:
        user_id = session.get('user_id')
    return render_template("profile.html", profile_user_id=user_id)

@app.route('/match-history')
@app.route('/match-history/<int:user_id>')
def match_history_page(user_id=None):
    from flask import session
    if user_id is None:
        user_id = session.get('user_id')
    return render_template("match_history.html", history_user_id=user_id)

if __name__ == "__main__":
    app.run(debug=True)



