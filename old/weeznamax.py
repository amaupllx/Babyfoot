from flask import Flask, render_template_string, request, jsonify
import csv
import os
from datetime import datetime
import math

app = Flask(__name__)

# Fichiers CSV
TEAMS_FILE = 'teams.csv'
MATCHES_FILE = 'matches.csv'

# Paramètres Elo
K_FACTOR = 32
ELO_BASE = 400

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weeznamax - Paris Babyfoot</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0a0a;
            min-height: 100vh;
            padding: 20px;
            color: #ffffff;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        h1 {
            text-align: center;
            color: #ff0000;
            margin-bottom: 40px;
            font-size: 3em;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 3px;
            text-shadow: 0 0 20px rgba(255, 0, 0, 0.5);
        }
        
        .card {
            background: #1a1a1a;
            border-radius: 8px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(255, 0, 0, 0.1);
            border: 1px solid #2a2a2a;
        }
        
        h2 {
            color: #ff0000;
            margin-bottom: 20px;
            border-bottom: 2px solid #ff0000;
            padding-bottom: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #ffffff;
            font-weight: 600;
        }
        
        input, select {
            width: 100%;
            padding: 12px;
            border: 1px solid #333;
            border-radius: 4px;
            font-size: 16px;
            transition: border-color 0.3s;
            background: #0a0a0a;
            color: #ffffff;
        }
        
        input:focus, select:focus {
            outline: none;
            border-color: #ff0000;
        }
        
        button {
            background: #ff0000;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 4px;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        button:hover {
            background: #cc0000;
        }
        
        button:active {
            background: #990000;
        }
        
        .teams-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .team-card {
            background: #0a0a0a;
            padding: 20px;
            border-radius: 4px;
            text-align: center;
            border: 1px solid #333;
            transition: border-color 0.3s;
        }
        
        .team-card:hover {
            border-color: #ff0000;
        }
        
        .team-name {
            font-size: 1.3em;
            font-weight: bold;
            color: #ffffff;
            margin-bottom: 10px;
        }
        
        .team-elo {
            font-size: 2em;
            color: #ff0000;
            font-weight: bold;
        }
        
        .odds-display {
            background: #0a0a0a;
            padding: 30px;
            border-radius: 4px;
            margin-top: 20px;
            border: 1px solid #ff0000;
        }
        
        .odds-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-top: 20px;
        }
        
        .odds-result {
            background: #1a1a1a;
            padding: 20px;
            border-radius: 4px;
            text-align: center;
            border: 1px solid #333;
        }
        
        .odds-result h4 {
            color: #ff0000;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        
        .odds-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #ff0000;
            display: block;
            margin: 10px 0;
        }
        
        .odds-prob {
            color: #999;
            font-size: 1.1em;
        }
        
        .match-history {
            margin-top: 20px;
        }
        
        .match-item {
            background: #0a0a0a;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 10px;
            border-left: 3px solid #ff0000;
        }
        
        .match-date {
            font-size: 0.9em;
            color: #666;
        }
        
        .match-score {
            font-size: 1.2em;
            font-weight: bold;
            margin: 5px 0;
            color: #ffffff;
        }
        
        .winner {
            color: #00ff00;
        }
        
        .loser {
            color: #ff0000;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .tab {
            padding: 10px 20px;
            background: #0a0a0a;
            border: 1px solid #333;
            border-radius: 4px 4px 0 0;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
            color: #ffffff;
            font-weight: 600;
        }
        
        .tab.active {
            background: #1a1a1a;
            border-bottom: 2px solid #ff0000;
        }
        
        .tab:hover {
            background: #1a1a1a;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .score-inputs {
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 20px;
            align-items: center;
            margin: 20px 0;
        }
        
        .vs {
            font-size: 2em;
            font-weight: bold;
            color: #ff0000;
        }
        
        select option {
            background: #0a0a0a;
            color: #ffffff;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>⚽ WEEZNAMAX</h1>
        
        <div class="card">
            <div class="tabs">
                <button class="tab active" onclick="switchTab('teams')">Équipes</button>
                <button class="tab" onclick="switchTab('odds')">Cotes</button>
                <button class="tab" onclick="switchTab('match')">Ajouter Match</button>
                <button class="tab" onclick="switchTab('history')">Historique</button>
            </div>
            
            <!-- Onglet Équipes -->
            <div id="teams" class="tab-content active">
                <h2>Ajouter une Équipe</h2>
                <form id="addTeamForm">
                    <div class="form-group">
                        <label for="teamName">Nom de l'équipe</label>
                        <input type="text" id="teamName" required>
                    </div>
                    <div class="form-group">
                        <label for="teamElo">Elo initial</label>
                        <input type="number" id="teamElo" value="1500" required>
                    </div>
                    <button type="submit">Ajouter l'équipe</button>
                </form>
                
                <h2 style="margin-top: 40px;">Équipes Enregistrées</h2>
                <div id="teamsList" class="teams-grid"></div>
            </div>
            
            <!-- Onglet Cotes -->
            <div id="odds" class="tab-content">
                <h2>Calculer les Cotes</h2>
                <div class="form-group">
                    <label for="team1Select">Équipe 1</label>
                    <select id="team1Select"></select>
                </div>
                <div class="form-group">
                    <label for="team2Select">Équipe 2</label>
                    <select id="team2Select"></select>
                </div>
                <button onclick="calculateOdds()">Calculer les cotes</button>
                
                <div id="oddsResult"></div>
            </div>
            
            <!-- Onglet Ajouter Match -->
            <div id="match" class="tab-content">
                <h2>Enregistrer un Match</h2>
                <div class="form-group">
                    <label for="matchTeam1">Équipe 1</label>
                    <select id="matchTeam1"></select>
                </div>
                <div class="score-inputs">
                    <div class="form-group">
                        <label for="score1">Score Équipe 1</label>
                        <input type="number" id="score1" min="0" required>
                    </div>
                    <div class="vs">VS</div>
                    <div class="form-group">
                        <label for="score2">Score Équipe 2</label>
                        <input type="number" id="score2" min="0" required>
                    </div>
                </div>
                <div class="form-group">
                    <label for="matchTeam2">Équipe 2</label>
                    <select id="matchTeam2"></select>
                </div>
                <button onclick="addMatch()">Enregistrer le match</button>
            </div>
            
            <!-- Onglet Historique -->
            <div id="history" class="tab-content">
                <h2>Historique des Matchs</h2>
                <div id="matchHistory" class="match-history"></div>
            </div>
        </div>
    </div>
    
    <script>
        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            event.target.classList.add('active');
            document.getElementById(tabName).classList.add('active');
            
            if (tabName === 'odds' || tabName === 'match' || tabName === 'history') {
                loadTeams();
            }
            if (tabName === 'history') {
                loadHistory();
            }
        }
        
        document.getElementById('addTeamForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('teamName').value;
            const elo = document.getElementById('teamElo').value;
            
            const response = await fetch('/api/teams', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, elo: parseInt(elo)})
            });
            
            if (response.ok) {
                document.getElementById('teamName').value = '';
                document.getElementById('teamElo').value = '1500';
                loadTeams();
                alert('Équipe ajoutée avec succès !');
            }
        });
        
        async function loadTeams() {
            const response = await fetch('/api/teams');
            const teams = await response.json();
            
            const teamsList = document.getElementById('teamsList');
            teamsList.innerHTML = teams.map(team => `
                <div class="team-card">
                    <div class="team-name">${team.name}</div>
                    <div class="team-elo">${team.elo}</div>
                    <div style="margin-top: 10px; font-size: 0.9em; color: #666;">ELO Rating</div>
                </div>
            `).join('');
            
            const selects = ['team1Select', 'team2Select', 'matchTeam1', 'matchTeam2'];
            selects.forEach(selectId => {
                const select = document.getElementById(selectId);
                select.innerHTML = '<option value="">Sélectionner une équipe</option>' +
                    teams.map(team => `<option value="${team.name}">${team.name} (${team.elo})</option>`).join('');
            });
        }
        
        async function calculateOdds() {
            const team1 = document.getElementById('team1Select').value;
            const team2 = document.getElementById('team2Select').value;
            
            if (!team1 || !team2) {
                alert('Veuillez sélectionner deux équipes');
                return;
            }
            
            if (team1 === team2) {
                alert('Veuillez sélectionner deux équipes différentes');
                return;
            }
            
            const response = await fetch(`/api/odds?team1=${team1}&team2=${team2}`);
            const data = await response.json();
            
            document.getElementById('oddsResult').innerHTML = `
                <div class="odds-display">
                    <h3 style="margin-bottom: 20px; color: #ff0000;">Cotes du Match</h3>
                    <div class="odds-grid">
                        <div class="odds-result">
                            <h4>Victoire ${data.team1}</h4>
                            <div style="color: #999; margin-bottom: 10px;">${data.elo1} ELO</div>
                            <span class="odds-value">${data.odds1}</span>
                            <div class="odds-prob">${data.prob1}%</div>
                        </div>
                        <div class="odds-result">
                            <h4>Match Nul</h4>
                            <div style="color: #999; margin-bottom: 10px;">Égalité</div>
                            <span class="odds-value">${data.odds_draw}</span>
                            <div class="odds-prob">${data.prob_draw}%</div>
                        </div>
                        <div class="odds-result">
                            <h4>Victoire ${data.team2}</h4>
                            <div style="color: #999; margin-bottom: 10px;">${data.elo2} ELO</div>
                            <span class="odds-value">${data.odds2}</span>
                            <div class="odds-prob">${data.prob2}%</div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        async function addMatch() {
            const team1 = document.getElementById('matchTeam1').value;
            const team2 = document.getElementById('matchTeam2').value;
            const score1 = parseInt(document.getElementById('score1').value);
            const score2 = parseInt(document.getElementById('score2').value);
            
            if (!team1 || !team2) {
                alert('Veuillez sélectionner deux équipes');
                return;
            }
            
            if (team1 === team2) {
                alert('Veuillez sélectionner deux équipes différentes');
                return;
            }
            
            if (isNaN(score1) || isNaN(score2)) {
                alert('Veuillez entrer des scores valides');
                return;
            }
            
            const response = await fetch('/api/match', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({team1, team2, score1, score2})
            });
            
            const result = await response.json();
            
            alert(`Match enregistré !
${result.team1}: ${result.old_elo1} → ${result.new_elo1} (${result.change1 > 0 ? '+' : ''}${result.change1})
${result.team2}: ${result.old_elo2} → ${result.new_elo2} (${result.change2 > 0 ? '+' : ''}${result.change2})`);
            
            document.getElementById('score1').value = '';
            document.getElementById('score2').value = '';
            loadTeams();
        }
        
        async function loadHistory() {
            const response = await fetch('/api/history');
            const matches = await response.json();
            
            const historyDiv = document.getElementById('matchHistory');
            if (matches.length === 0) {
                historyDiv.innerHTML = '<p>Aucun match enregistré</p>';
                return;
            }
            
            historyDiv.innerHTML = matches.map(match => `
                <div class="match-item">
                    <div class="match-date">${match.date}</div>
                    <div class="match-score">
                        <span class="${match.score1 > match.score2 ? 'winner' : 'loser'}">${match.team1}</span>
                        ${match.score1} - ${match.score2}
                        <span class="${match.score2 > match.score1 ? 'winner' : 'loser'}">${match.team2}</span>
                    </div>
                    <div style="font-size: 0.9em; color: #666; margin-top: 5px;">
                        ${match.team1}: ${match.elo1_before} → ${match.elo1_after} (${match.elo1_change > 0 ? '+' : ''}${match.elo1_change})
                        | ${match.team2}: ${match.elo2_before} → ${match.elo2_after} (${match.elo2_change > 0 ? '+' : ''}${match.elo2_change})
                    </div>
                </div>
            `).reverse().join('');
        }
        
        loadTeams();
    </script>
</body>
</html>
'''

def init_csv_files():
    """Initialise les fichiers CSV s'ils n'existent pas"""
    if not os.path.exists(TEAMS_FILE):
        with open(TEAMS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'elo'])
    
    if not os.path.exists(MATCHES_FILE):
        with open(MATCHES_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['date', 'team1', 'team2', 'score1', 'score2', 
                           'elo1_before', 'elo1_after', 'elo1_change',
                           'elo2_before', 'elo2_after', 'elo2_change'])

def read_teams():
    """Lit toutes les équipes depuis le CSV"""
    teams = []
    with open(TEAMS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            teams.append({'name': row['name'], 'elo': int(row['elo'])})
    return teams

def write_team(name, elo):
    """Ajoute une équipe au CSV"""
    with open(TEAMS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([name, elo])

def update_team_elo(name, new_elo):
    """Met à jour l'Elo d'une équipe"""
    teams = read_teams()
    with open(TEAMS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'elo'])
        for team in teams:
            if team['name'] == name:
                writer.writerow([name, new_elo])
            else:
                writer.writerow([team['name'], team['elo']])

def calculate_elo_change(elo1, elo2, score1, score2):
    """Calcule le changement d'Elo avec prise en compte de l'écart de buts"""
    # Probabilité de victoire de l'équipe 1
    expected1 = 1 / (1 + math.pow(10, (elo2 - elo1) / ELO_BASE))
    
    # Résultat réel (1 = victoire, 0 = défaite, 0.5 = match nul)
    if score1 > score2:
        actual1 = 1
    elif score1 < score2:
        actual1 = 0
    else:
        actual1 = 0.5
    
    # Multiplicateur basé sur l'écart de buts
    goal_diff = abs(score1 - score2)
    if goal_diff <= 1:
        multiplier = 1.0
    elif goal_diff <= 2:
        multiplier = 1.5
    else:
        multiplier = math.log(goal_diff + 1) + 1
    
    # Changement d'Elo
    change1 = round(K_FACTOR * (actual1 - expected1) * multiplier)
    change2 = -change1
    
    return change1, change2

def add_match(team1, team2, score1, score2):
    """Enregistre un match et met à jour les Elos"""
    teams = read_teams()
    
    team1_data = next((t for t in teams if t['name'] == team1), None)
    team2_data = next((t for t in teams if t['name'] == team2), None)
    
    if not team1_data or not team2_data:
        return None
    
    elo1_before = team1_data['elo']
    elo2_before = team2_data['elo']
    
    change1, change2 = calculate_elo_change(elo1_before, elo2_before, score1, score2)
    
    elo1_after = elo1_before + change1
    elo2_after = elo2_before + change2
    
    update_team_elo(team1, elo1_after)
    update_team_elo(team2, elo2_after)
    
    with open(MATCHES_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            team1, team2, score1, score2,
            elo1_before, elo1_after, change1,
            elo2_before, elo2_after, change2
        ])
    
    return {
        'team1': team1, 'team2': team2,
        'old_elo1': elo1_before, 'new_elo1': elo1_after, 'change1': change1,
        'old_elo2': elo2_before, 'new_elo2': elo2_after, 'change2': change2
    }

def read_matches():
    """Lit l'historique des matchs"""
    matches = []
    with open(MATCHES_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            matches.append(row)
    return matches

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/teams', methods=['GET', 'POST'])
def teams():
    if request.method == 'POST':
        data = request.json
        write_team(data['name'], data['elo'])
        return jsonify({'success': True})
    else:
        return jsonify(read_teams())

@app.route('/api/odds')
def odds():
    team1 = request.args.get('team1')
    team2 = request.args.get('team2')
    
    teams = read_teams()
    team1_data = next((t for t in teams if t['name'] == team1), None)
    team2_data = next((t for t in teams if t['name'] == team2), None)
    
    if not team1_data or not team2_data:
        return jsonify({'error': 'Team not found'}), 404
    
    elo1 = team1_data['elo']
    elo2 = team2_data['elo']
    
    # Calcul des probabilités de base (sans match nul)
    prob1_base = 1 / (1 + math.pow(10, (elo2 - elo1) / ELO_BASE))
    prob2_base = 1 - prob1_base
    
    # Probabilité de match nul (diminue avec la différence d'Elo)
    elo_diff = abs(elo1 - elo2)
    # Base de 12% pour des équipes égales, diminue avec la différence
    prob_draw = max(0.05, 0.12 - (elo_diff / 500) * 0.07)
    
    # Ajustement des probabilités de victoire
    prob1 = prob1_base * (1 - prob_draw)
    prob2 = prob2_base * (1 - prob_draw)
    
    # Calcul des cotes
    odds1 = round(1 / prob1, 2)
    odds2 = round(1 / prob2, 2)
    odds_draw = round(1 / prob_draw, 2)
    
    return jsonify({
        'team1': team1, 'team2': team2,
        'elo1': elo1, 'elo2': elo2,
        'prob1': round(prob1 * 100, 1), 
        'prob2': round(prob2 * 100, 1),
        'prob_draw': round(prob_draw * 100, 1),
        'odds1': odds1, 
        'odds2': odds2,
        'odds_draw': odds_draw
    })

@app.route('/api/match', methods=['POST'])
def match():
    data = request.json
    result = add_match(data['team1'], data['team2'], data['score1'], data['score2'])
    if result:
        return jsonify(result)
    return jsonify({'error': 'Error adding match'}), 400

@app.route('/api/history')
def history():
    return jsonify(read_matches())

if __name__ == '__main__':
    init_csv_files()
    print("🏆 Serveur de Paris Babyfoot démarré !")
    print("📊 Ouvrez votre navigateur à l'adresse: http://localhost:5000")
    print("💾 Les données sont sauvegardées dans teams.csv et matches.csv")
    app.run(debug=True, port=5000)