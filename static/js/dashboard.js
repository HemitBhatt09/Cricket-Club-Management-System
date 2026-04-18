console.log("JS LOADED");

// navigation
function goTo(url) {
    window.location.href = url;
}

// ================= UPCOMING =================
function loadDashboardUpcoming() {
    fetch("/dashboard-upcoming")
    .then(res => res.json())
    .then(matches => {

        const div = document.getElementById("dashboardUpcoming");
        div.innerHTML = "";

        matches.forEach(m => {
            let matchCategory = m.tournament_id ? `🏆 Tournament Match (${m.stage})` : `⚾ Normal Match`;
            let viewTournamentBtn = m.tournament_id ? 
                `<button onclick="window.location.href='/tournament/${m.tournament_id}/matches'"
                        style="margin-top:10px; padding:6px 12px; background:var(--accent-secondary); color:white; border:none; border-radius:5px; cursor:pointer;">
                    View Tournament
                </button>` : '';

            div.innerHTML += `
                <div class="card p-3 mb-2" style="background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid var(--border-color); box-shadow: var(--glass-shadow); margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
                        <h5 style="color: var(--accent-primary); margin: 0; font-size: 1.2rem;">${m.team1_name} <span style="color: var(--text-muted); font-size: 0.9rem;">vs</span> ${m.team2_name}</h5>
                    </div>
                    <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 5px;">📅 ${new Date(m.match_date).toLocaleDateString()}</p>
                    <p style="color: var(--text-color); font-weight: bold; margin-bottom: 5px;">${matchCategory}</p>
                    <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                        ${viewTournamentBtn}
                    </div>
                </div>
            `;
        });

    })
    .catch(err => console.error("UPCOMING ERROR:", err));
}

// ================= RECENT =================
function loadDashboardRecent() {
    fetch("/dashboard-recent")
    .then(res => res.json())
    .then(matches => {

        const div = document.getElementById("dashboardRecent");
        div.innerHTML = "";

        matches.forEach(m => {
            let matchCategory = m.tournament_id ? `🏆 Tournament Match (${m.stage})` : `⚾ Normal Match`;
            let viewTournamentBtn = m.tournament_id ? 
                `<button onclick="window.location.href='/tournament/${m.tournament_id}/matches'"
                        style="margin-top:10px; padding:6px 12px; background:var(--accent-secondary); color:white; border:none; border-radius:5px; cursor:pointer;">
                    View Tournament
                </button>` : '';

            div.innerHTML += `
                <div class="card p-3 mb-2" style="background: var(--bg-card); border-radius: 12px; padding: 20px; border: 1px solid var(--border-color); box-shadow: var(--glass-shadow); margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 15px;">
                        <h5 style="color: var(--accent-primary); margin: 0; font-size: 1.2rem;">${m.team1_name} <span style="color: var(--text-muted); font-size: 0.9rem;">vs</span> ${m.team2_name}</h5>
                    </div>

                    <p style="color: var(--text-color); font-weight: bold; margin-bottom: 10px;">${matchCategory}</p>

                    <div style="background: var(--bg-input); padding: 10px; border-radius: 8px; margin-bottom: 15px; display: grid; gap: 5px;">
                        <div style="display: flex; justify-content: space-between;">
                            <span>${m.team1_name}</span>
                            <b>${m.team1_score ?? '-'} / ${m.team1_wickets ?? '-'} <span style="font-size: 0.8rem; color: var(--text-muted);">(${m.team1_overs ?? '-'} ov)</span></b>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span>${m.team2_name}</span>
                            <b>${m.team2_score ?? '-'} / ${m.team2_wickets ?? '-'} <span style="font-size: 0.8rem; color: var(--text-muted);">(${m.team2_overs ?? '-'} ov)</span></b>
                        </div>
                    </div>

                    <p style="margin-bottom: 15px; color: var(--text-color);"><b>Winner:</b> <span style="color: var(--accent-primary);">${m.winner ?? "Pending"}</span></p>

                    <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                        <button onclick="viewScorecard(${m.match_id})"
                                style="margin-top:10px; padding:6px 12px; background:var(--accent-primary); color:white; border:none; border-radius:5px; cursor:pointer;">
                            View Scorecard
                        </button>
                        ${viewTournamentBtn}
                    </div>
                </div>
            `;
        });

    })
    .catch(err => console.error("RECENT ERROR:", err));
}

// ✅ FINAL LOAD (WORKING)
document.addEventListener("DOMContentLoaded", function() {
    loadDashboardUpcoming();
    loadDashboardRecent();
    loadStats();
    loadPlayersAndTeams();
});

function viewScorecard(matchId) {
    window.location.href = `/scorecard?match_id=${matchId}`;
}

function loadStats() {
    fetch("/dashboard-recent")
    .then(res => res.json())
    .then(data => {
        document.getElementById("totalMatches").innerText = data.length;
    });

    fetch("/dashboard-upcoming")
    .then(res => res.json())
    .then(data => {
        document.getElementById("liveMatch").innerText =
            data.length > 0 ? `${data[0].team1_name} vs ${data[0].team2_name}` : "No Live Match";
    });
}

function showSection(section) {

    document.getElementById("upcomingSection").style.display = "none";
    document.getElementById("recentSection").style.display = "none";
    document.getElementById("playersSection").style.display = "none";

    document.getElementById(section + "Section").style.display = "block";
}

// ================= PLAYERS & TEAMS =================
let allPlayersData = [];
let allTeamsData = [];

function loadPlayersAndTeams() {
    fetch("/players")
        .then(res => res.json())
        .then(data => {
            allPlayersData = data;
            renderPlayers(allPlayersData);
        }).catch(err => console.error("PLAYERS ERROR:", err));

    fetch("/all-teams")
        .then(res => res.json())
        .then(data => {
            allTeamsData = data;
            renderTeams(allTeamsData);
        }).catch(err => console.error("TEAMS ERROR:", err));
}

function renderPlayers(players) {
    const div = document.getElementById("playersList");
    div.innerHTML = "";
    if (players.length === 0) {
        div.innerHTML = "<p style='color: var(--text-muted);'>No players found.</p>";
        return;
    }
    players.forEach(p => {
        let avatarHtml = p.profile_pic 
            ? `<img src="/static/uploads/profiles/${p.profile_pic}" style="width: 100%; height: 100%; border-radius: 50%; object-fit: cover;">`
            : p.name.charAt(0).toUpperCase();

        div.innerHTML += `
            <div onclick="openPlayerModal(${p.user_id})" style="cursor: pointer; background: var(--bg-input); padding: 12px 15px; border-radius: 8px; border: 1px solid var(--border-color); display: flex; align-items: center; gap: 15px; transition: transform 0.2s;">
                <div style="width: 40px; height: 40px; border-radius: 50%; background: var(--accent-primary); color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.2rem; overflow: hidden;">
                    ${avatarHtml}
                </div>
                <div>
                    <h5 style="margin: 0; color: var(--text-color);">${p.name} <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: normal; margin-left: 5px;">(#${p.user_id})</span></h5>
                </div>
            </div>
        `;
    });
}

function searchPlayers() {
    let q = document.getElementById("playerSearch").value.toLowerCase();
    let filtered = allPlayersData.filter(p => p.name.toLowerCase().includes(q));
    renderPlayers(filtered);
}

function renderTeams(teams) {
    const div = document.getElementById("teamsList");
    div.innerHTML = "";
    if (teams.length === 0) {
        div.innerHTML = "<p style='color: var(--text-muted);'>No teams found.</p>";
        return;
    }
    teams.forEach(t => {
        div.innerHTML += `
            <div onclick="openTeamModal(${t.team_id})" style="cursor: pointer; background: var(--bg-input); padding: 12px 15px; border-radius: 8px; border: 1px solid var(--border-color); display: flex; align-items: center; gap: 15px; transition: transform 0.2s;">
                <div style="width: 40px; height: 40px; border-radius: 8px; background: var(--accent-secondary); color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.2rem;">
                    ${t.team_name.charAt(0).toUpperCase()}
                </div>
                <div>
                    <h5 style="margin: 0; color: var(--text-color);">${t.team_name} <span style="font-size: 0.8rem; color: var(--text-muted); font-weight: normal; margin-left: 5px;">(#${t.team_id})</span></h5>
                </div>
            </div>
        `;
    });
}

function searchTeams() {
    let q = document.getElementById("teamSearch").value.toLowerCase();
    let filtered = allTeamsData.filter(t => t.team_name.toLowerCase().includes(q));
    renderTeams(filtered);
}

// 🛡️ TEAM DETAILS MODAL LOGIC
function openTeamModal(teamId) {
    const team = allTeamsData.find(t => t.team_id === teamId);
    if(!team) return;

    document.getElementById("modalTeamName").innerText = team.team_name;
    document.getElementById("modalTeamPlayers").innerHTML = "<p style='color: var(--text-muted);'>Loading players...</p>";
    document.getElementById("teamDetailsModal").style.display = "flex";

    fetch(`/team-players/${teamId}`)
    .then(res => res.json())
    .then(players => {
        let html = "";
        if(players.length === 0) {
            html = "<p style='color: var(--text-muted);'>No players found in this team.</p>";
        } else {
            players.forEach(p => {
                let role = p.is_captain ? '<span style="background: var(--accent-primary); color: white; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; margin-left: 5px;">(C)</span>' : '';
                html += `
                <div onclick="window.location.href='/profile/${p.user_id}'" style="cursor: pointer; background: var(--bg-input); padding: 10px 15px; border-radius: 8px; display: flex; align-items: center; border: 1px solid var(--border-color); transition: transform 0.2s;" onmouseover="this.style.transform='scale(1.02)'" onmouseout="this.style.transform='scale(1)'">
                    <div style="width: 30px; height: 30px; border-radius: 50%; background: var(--accent-secondary); color: white; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1rem; margin-right: 15px;">
                        ${p.name.charAt(0).toUpperCase()}
                    </div>
                    <div style="color: var(--text-color); font-weight: 500;">
                        ${p.name}${role}
                    </div>
                </div>`;
            });
        }
        document.getElementById("modalTeamPlayers").innerHTML = html;
    })
    .catch(err => {
        console.error(err);
        document.getElementById("modalTeamPlayers").innerHTML = "<p style='color: red;'>Failed to load players.</p>";
    });
}

function closeTeamModal() {
    document.getElementById("teamDetailsModal").style.display = "none";
}

function openPlayerModal(userId) {
    window.location.href = `/profile/${userId}`;
}

function closePlayerModal() {
    document.getElementById("playerDetailsModal").style.display = "none";
}