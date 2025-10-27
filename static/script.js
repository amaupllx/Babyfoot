let currentTeams = [];

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(tabName).classList.add('active');
    
    if (tabName === 'programme') {
        loadTeams();
        loadScheduledMatches();
    } else if (tabName === 'history') {
        loadHistory();
    } else if (tabName === 'teams') {
        loadTeams();
    }
}

// ========== GESTION DES ÉQUIPES ==========

document.getElementById('addTeamForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('teamName').value;
    const elo = document.getElementById('teamElo').value;
    const poule = document.getElementById('teamPoule').value;
    
    const response = await fetch('/api/teams', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({name, elo: parseInt(elo), poule})
    });
    
    if (response.ok) {
        document.getElementById('teamName').value = '';
        document.getElementById('teamElo').value = '1500';
        document.getElementById('teamPoule').value = '';
        loadTeams();
    }
});

async function loadTeams() {
    const response = await fetch('/api/teams');
    currentTeams = await response.json();
    
    const teamsList = document.getElementById('teamsList');
    teamsList.innerHTML = currentTeams.map(team => `
        <div class="team-card">
            <div class="team-header">
                <div class="team-name">${team.name}</div>
            </div>
            <div class="team-elo">${team.elo}</div>
            <div class="team-poule">${team.poule ? 'Poule ' + team.poule : 'Aucune poule'}</div>
            <div class="team-actions">
                <button class="secondary" onclick="openEditModal('${team.name}', ${team.elo}, '${team.poule}')">Modifier</button>
                <button class="danger" onclick="deleteTeam('${team.name}')">Supprimer</button>
            </div>
        </div>
    `).join('');
    
    // Mettre à jour les selects pour le programme
    const selects = ['progTeam1', 'progTeam2'];
    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            select.innerHTML = '<option value="">Sélectionner une équipe</option>' +
                currentTeams.map(team => `<option value="${team.name}">${team.name} (${team.elo})</option>`).join('');
        }
    });
}

function openEditModal(name, elo, poule) {
    document.getElementById('editOldName').value = name;
    document.getElementById('editName').value = name;
    document.getElementById('editElo').value = elo;
    document.getElementById('editPoule').value = poule;
    document.getElementById('editModal').style.display = 'block';
}

function closeEditModal() {
    document.getElementById('editModal').style.display = 'none';
}

document.getElementById('editTeamForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const oldName = document.getElementById('editOldName').value;
    const newName = document.getElementById('editName').value;
    const newElo = parseInt(document.getElementById('editElo').value);
    const newPoule = document.getElementById('editPoule').value;
    
    const response = await fetch('/api/teams/update', {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({old_name: oldName, new_name: newName, new_elo: newElo, new_poule: newPoule})
    });
    
    if (response.ok) {
        closeEditModal();
        loadTeams();
    }
});

async function deleteTeam(name) {
    if (!confirm(`Êtes-vous sûr de vouloir supprimer l'équipe "${name}" ?`)) {
        return;
    }
    
    const response = await fetch(`/api/teams/${name}`, {
        method: 'DELETE'
    });
    
    if (response.ok) {
        loadTeams();
    }
}

// ========== MATCHS PROGRAMMÉS ==========

async function addScheduledMatch() {
    const team1 = document.getElementById('progTeam1').value;
    const team2 = document.getElementById('progTeam2').value;
    
    if (!team1 || !team2) {
        alert('Veuillez sélectionner deux équipes');
        return;
    }
    
    if (team1 === team2) {
        alert('Veuillez sélectionner deux équipes différentes');
        return;
    }
    
    const response = await fetch('/api/scheduled', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({team1, team2})
    });
    
    if (response.ok) {
        document.getElementById('progTeam1').value = '';
        document.getElementById('progTeam2').value = '';
        loadScheduledMatches();
    }
}

async function loadScheduledMatches() {
    const response = await fetch('/api/scheduled');
    const matches = await response.json();
    
    const container = document.getElementById('scheduledMatches');
    
    if (matches.length === 0) {
        container.innerHTML = '<p style="color: #666; text-align: center; padding: 40px; background: #f9f9f9; border-radius: 4px;">Aucun match programmé</p>';
        return;
    }
    
    let html = '';
    for (const match of matches) {
        // Récupérer les infos des équipes
        const team1Data = currentTeams.find(t => t.name === match.team1);
        const team2Data = currentTeams.find(t => t.name === match.team2);
        
        if (!team1Data || !team2Data) continue;
        
        // Calculer les cotes
        const oddsResponse = await fetch(`/api/odds?team1=${match.team1}&team2=${match.team2}`);
        const oddsData = await oddsResponse.json();
        
        html += `
            <div class="match-item">
                <div class="match-header">
                    <div class="match-teams">${match.team1} vs ${match.team2}</div>
                </div>
                <div class="match-odds">
                    <div class="odds-box">
                        <div class="odds-label">Victoire ${match.team1}</div>
                        <div class="odds-value-small">${oddsData.odds1}</div>
                        <div style="color: #999; font-size: 0.9em;">${oddsData.prob1}%</div>
                    </div>
                    <div class="odds-box">
                        <div class="odds-label">Victoire ${match.team2}</div>
                        <div class="odds-value-small">${oddsData.odds2}</div>
                        <div style="color: #999; font-size: 0.9em;">${oddsData.prob2}%</div>
                    </div>
                </div>
                <div class="score-input-container">
                    <div class="score-input-row">
                        <div class="score-team-section">
                            <div class="score-team-name">${match.team1}</div>
                            <input type="number" id="score1_${match.id}" min="0" placeholder="0">
                        </div>
                        <span class="vs-small">-</span>
                        <div class="score-team-section">
                            <div class="score-team-name">${match.team2}</div>
                            <input type="number" id="score2_${match.id}" min="0" placeholder="0">
                        </div>
                    </div>
                    <button class="score-button" onclick="enterScore(${match.id}, '${match.team1}', '${match.team2}')">
                        ✓ VALIDER LE SCORE
                    </button>
                </div>
                <div class="delete-match-btn">
                    <button class="danger" onclick="deleteScheduledMatch(${match.id})">🗑️ Supprimer</button>
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

async function enterScore(matchId, team1, team2) {
    const score1 = parseInt(document.getElementById(`score1_${matchId}`).value);
    const score2 = parseInt(document.getElementById(`score2_${matchId}`).value);
    
    if (isNaN(score1) || isNaN(score2)) {
        alert('Veuillez entrer des scores valides');
        return;
    }
    
    const response = await fetch('/api/match', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({team1, team2, score1, score2, scheduled_id: matchId})
    });
    
    const result = await response.json();
    
    loadTeams();
    loadScheduledMatches();
}

async function deleteScheduledMatch(matchId) {
    if (!confirm('Voulez-vous vraiment supprimer ce match du programme ?')) {
        return;
    }
    
    const response = await fetch(`/api/scheduled/${matchId}`, {
        method: 'DELETE'
    });
    
    if (response.ok) {
        loadScheduledMatches();
    }
}

// ========== HISTORIQUE ==========

async function loadHistory() {
    const response = await fetch('/api/history');
    const matches = await response.json();
    
    const historyDiv = document.getElementById('matchHistory');
    if (matches.length === 0) {
        historyDiv.innerHTML = '<p style="color: #666; text-align: center; padding: 40px; background: #f9f9f9; border-radius: 4px;">Aucun match enregistré</p>';
        return;
    }
    
    historyDiv.innerHTML = matches.map(match => `
        <div class="match-item">
            <div class="match-date">${match.date}</div>
            <div class="match-score">
                <span class="${match.score1 > match.score2 ? 'winner' : (match.score1 < match.score2 ? 'loser' : '')}">${match.team1}</span>
                ${match.score1} - ${match.score2}
                <span class="${match.score2 > match.score1 ? 'winner' : (match.score2 < match.score1 ? 'loser' : '')}">${match.team2}</span>
            </div>
            <div style="font-size: 0.9em; color: #666; margin-top: 10px; padding-top: 10px; border-top: 1px solid #e0e0e0;">
                <strong>${match.team1}:</strong> ${match.elo1_before} → ${match.elo1_after} 
                <span style="color: ${match.elo1_change > 0 ? '#00aa00' : '#ff0000'}; font-weight: bold;">
                    (${match.elo1_change > 0 ? '+' : ''}${match.elo1_change})
                </span>
                <br>
                <strong>${match.team2}:</strong> ${match.elo2_before} → ${match.elo2_after} 
                <span style="color: ${match.elo2_change > 0 ? '#00aa00' : '#ff0000'}; font-weight: bold;">
                    (${match.elo2_change > 0 ? '+' : ''}${match.elo2_change})
                </span>
            </div>
        </div>
    `).reverse().join('');
}

function distributeCredits() {
    if (!confirm('Êtes-vous sûr de vouloir distribuer 10 Wiz à tous les utilisateurs ?')) {
        return;
    }
    
    fetch('/admin/add_credits', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: 'amount=10'
    })
    .then(response => response.json())
    .then(data => {
        const messageDiv = document.getElementById('credits-message');
        if (data.success) {
            messageDiv.innerHTML = `<div style="padding: 10px; background: #d4edda; color: #155724; border-radius: 5px;">${data.message}</div>`;
            setTimeout(() => location.reload(), 2000);
        } else {
            messageDiv.innerHTML = `<div style="padding: 10px; background: #f8d7da; color: #721c24; border-radius: 5px;">${data.message}</div>`;
        }
    })
    .catch(error => {
        console.error('Erreur:', error);
        document.getElementById('credits-message').innerHTML = 
            '<div style="padding: 10px; background: #f8d7da; color: #721c24; border-radius: 5px;">Erreur lors de la distribution</div>';
    });
}

// Charger le classement des utilisateurs
function loadLeaderboard() {
    fetch('/api/leaderboard')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayLeaderboard(data.leaderboard);
            }
        })
        .catch(error => console.error('Erreur:', error));
}


// Afficher le classement
function displayLeaderboard(leaderboard) {
    const container = document.getElementById('leaderboardList');
    
    if (leaderboard.length === 0) {
        container.innerHTML = '<p style="text-align: center; color: #666;">Aucun utilisateur trouvé</p>';
        return;
    }
    
    let html = '<table class="leaderboard-table">';
    html += '<thead><tr><th>Rang</th><th>Utilisateur</th><th>Crédits</th></tr></thead>';
    html += '<tbody>';
    
    leaderboard.forEach((user, index) => {
        const rank = index + 1;
        let medal = '';
        
        // Ajouter des médailles pour le top 3
        if (rank === 1) medal = '🥇';
        else if (rank === 2) medal = '🥈';
        else if (rank === 3) medal = '🥉';
        
        const rankDisplay = medal ? `${medal} ${rank}` : rank;
        
        html += `
            <tr class="rank-${rank}">
                <td class="rank-cell">${rankDisplay}</td>
                <td class="username-cell">${user.username}</td>
                <td class="credits-cell">${user.credits.toFixed(2)} Wiz</td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

function switchTab(tabName) {
    // Masquer tous les onglets
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => tab.classList.remove('active'));
    
    // Masquer tous les boutons actifs
    const tabButtons = document.querySelectorAll('.tab');
    tabButtons.forEach(btn => btn.classList.remove('active'));
    
    // Afficher l'onglet sélectionné
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');
    
    // Charger les données selon l'onglet
    if (tabName === 'teams') {
        loadTeams();
    } else if (tabName === 'programme') {
        loadScheduledMatches();
        loadTeamSelects();
    } else if (tabName === 'history') {
        loadHistory();
    } else if (tabName === 'leaderboard') {
        loadLeaderboard();  // ← Ajoute cette condition
    }
}

// Charger les équipes au démarrage
loadTeams();