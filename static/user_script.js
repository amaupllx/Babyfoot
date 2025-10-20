let currentUser = null;
let currentMatches = [];

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    event.target.classList.add('active');
    document.getElementById(tabName).classList.add('active');
    
    if (tabName === 'matches') {
        loadMatches();
    } else if (tabName === 'mybets') {
        loadMyBets();
    }
}

async function loadUserInfo() {
    const response = await fetch('/api/user/info');
    const data = await response.json();
    
    currentUser = data;
    document.getElementById('userName').textContent = data.username;
    document.getElementById('userCredits').textContent = data.credits.toFixed(2);
}

async function loadMatches() {
    const response = await fetch('/api/user/matches');
    currentMatches = await response.json();
    
    const container = document.getElementById('matchesList');
    
    if (currentMatches.length === 0) {
        container.innerHTML = '<p style="color: #666; text-align: center; padding: 40px; background: #f9f9f9; border-radius: 4px;">Aucun match disponible pour le moment</p>';
        return;
    }
    
    let html = '';
    for (const match of currentMatches) {
        // Récupérer les cotes
        const oddsResponse = await fetch(`/api/odds?team1=${match.team1}&team2=${match.team2}`);
        const oddsData = await oddsResponse.json();
        
        html += `
            <div class="match-item">
                <div class="match-header">
                    <div class="match-teams">${match.team1} vs ${match.team2}</div>
                </div>
                <div class="match-odds">
                    <div class="bet-card" onclick="openBetModal(${match.id}, '${match.team1}', '${match.team2}', 'team1', ${oddsData.odds1})">
                        <div class="odds-label">Victoire ${match.team1}</div>
                        <div class="odds-value-small">${oddsData.odds1}</div>
                        <div style="color: #999; font-size: 0.9em; margin-top: 5px;">${oddsData.prob1}%</div>
                    </div>
                    <div class="bet-card" onclick="openBetModal(${match.id}, '${match.team1}', '${match.team2}', 'team2', ${oddsData.odds2})">
                        <div class="odds-label">Victoire ${match.team2}</div>
                        <div class="odds-value-small">${oddsData.odds2}</div>
                        <div style="color: #999; font-size: 0.9em; margin-top: 5px;">${oddsData.prob2}%</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    container.innerHTML = html;
}

function openBetModal(matchId, team1, team2, betType, odds) {
    let betLabel = '';
    if (betType === 'team1') {
        betLabel = `Victoire de ${team1}`;
    } else if (betType === 'team2') {
        betLabel = `Victoire de ${team2}`;
    } else {
        betLabel = 'Match Nul';
    }
    
    const maxBet = currentUser.credits;
    
    document.getElementById('betModalContent').innerHTML = `
        <div style="margin-bottom: 25px; padding: 20px; background: #f9f9f9; border-radius: 8px;">
            <div style="font-size: 1.1em; color: #333; margin-bottom: 10px;">
                <strong>Match:</strong> ${team1} vs ${team2}
            </div>
            <div style="font-size: 1.1em; color: #333; margin-bottom: 10px;">
                <strong>Pari:</strong> ${betLabel}
            </div>
            <div style="font-size: 1.1em; color: #333;">
                <strong>Cote:</strong> <span style="color: #ff0000; font-size: 1.5em; font-weight: bold;">${odds}</span>
            </div>
        </div>
        <div class="form-group">
            <label for="betAmount" style="font-size: 1.1em;">Montant du pari (Wiz)</label>
            <input type="number" id="betAmount" min="0.01" max="${maxBet}" step="0.01" placeholder="0.00" required>
            <small style="color: #666; font-size: 1em;">Crédits disponibles: ${maxBet.toFixed(2)} Wiz</small>
        </div>
        <div style="margin: 25px 0; padding: 20px; background: #f0fff0; border: 2px solid #00aa00; border-radius: 8px;">
            <div style="font-size: 1.1em; color: #333; margin-bottom: 5px;"><strong>Gain potentiel:</strong></div>
            <div id="potentialWin" style="color: #00aa00; font-size: 1.8em; font-weight: bold;">0.00 Wiz</div>
        </div>
        <button onclick="placeBet(${matchId}, '${betType}', ${odds})" class="score-button">
            VALIDER
        </button>
    `;
    // Calculer le gain potentiel en temps réel
    document.getElementById('betAmount').addEventListener('input', (e) => {
        const amount = parseFloat(e.target.value) || 0;
        const potentialWin = (amount * odds).toFixed(2);
        document.getElementById('potentialWin').textContent = potentialWin + ' Wiz';
    });
    
    document.getElementById('betModal').style.display = 'block';
}

function closeBetModal() {
    document.getElementById('betModal').style.display = 'none';
}

async function placeBet(matchId, betType, odds) {
    const amount = parseFloat(document.getElementById('betAmount').value);
    
    if (!amount || amount <= 0) {
        alert('Veuillez entrer un montant valide');
        return;
    }
    
    if (amount > currentUser.credits) {
        alert('Crédits insuffisants !');
        return;
    }
    
    try {
        const response = await fetch('/api/user/bet', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({match_id: matchId, bet_type: betType, amount, odds})
        });
        
        const data = await response.json();
        
        if (data.success) {
            closeBetModal();
            loadUserInfo();
            
            // Rediriger vers l'onglet "Mes paris"
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            document.querySelector('.tab[onclick*="mybets"]').classList.add('active');
            document.getElementById('mybets').classList.add('active');
            
            loadMyBets();
        } else {
            alert('Erreur: ' + data.error);
        }
    } catch (error) {
        alert('Erreur lors de la création du pari');
    }
}

async function loadMyBets() {
    const response = await fetch('/api/user/bets');
    const bets = await response.json();
    
    const container = document.getElementById('betsList');
    
    if (bets.length === 0) {
        container.innerHTML = '<p style="color: #666; text-align: center; padding: 40px; background: #f9f9f9; border-radius: 4px;">Vous n\'avez pas encore placé de paris</p>';
        return;
    }
    
    // Récupérer les infos des matchs
    const matchesResponse = await fetch('/api/user/matches');
    const matches = await matchesResponse.json();
    
    // Séparer les paris en attente et terminés
    const pendingBets = bets.filter(bet => bet.status === 'pending');
    const completedBets = bets.filter(bet => bet.status !== 'pending');
    
    // Afficher d'abord les paris en attente, puis les terminés
    const sortedBets = [...pendingBets, ...completedBets];
    
    container.innerHTML = sortedBets.map(bet => {
        const match = matches.find(m => m.id === bet.match_id);
        
        let betLabel = '';
        if (bet.bet_type === 'team1') {
            betLabel = `Victoire ${match ? match.team1 : 'Équipe 1'}`;
        } else if (bet.bet_type === 'team2') {
            betLabel = `Victoire ${match ? match.team2 : 'Équipe 2'}`;
        } else {
            betLabel = 'Match Nul';
        }
        
        let statusColor = '#666';
        let statusText = 'En attente';
        if (bet.status === 'won') {
            statusColor = '#00aa00';
            statusText = `Gagné ! +${(parseFloat(bet.amount) * parseFloat(bet.odds)).toFixed(2)} Wiz`;
        } else if (bet.status === 'lost') {
            statusColor = '#ff0000';
            statusText = `Perdu -${parseFloat(bet.amount).toFixed(2)} Wiz`;
        }
        
        return `
            <div class="match-item">
                <div class="match-date">${bet.date}</div>
                <div style="margin: 10px 0; color: #333;">
                    <strong style="color: #333;">${match ? match.team1 + ' vs ' + match.team2 : 'Match terminé'}</strong><br>
                    <span style="color: #333;">Pari: ${betLabel}</span><br>
                    <span style="color: #333;">Mise: ${parseFloat(bet.amount).toFixed(2)} Wiz | Cote: ${bet.odds}</span>
                </div>
                <div style="font-weight: bold; color: ${statusColor}; font-size: 1.1em;">
                    ${statusText}
                </div>
            </div>
        `;
    }).join('');
}

// Charger les infos au démarrage
loadUserInfo();
loadMatches();

// Vérifier les résultats toutes les 30 secondes
setInterval(() => {
    // Recharger les crédits et les paris si on est sur l'onglet "Mes paris"
    const myBetsTab = document.getElementById('mybets');
    if (myBetsTab && myBetsTab.classList.contains('active')) {
        loadUserInfo();
        loadMyBets();
    }
    // Recharger les matchs disponibles si on est sur l'onglet "Matches"
    const matchesTab = document.getElementById('matches');
    if (matchesTab && matchesTab.classList.contains('active')) {
        loadMatches();
    }
}, 30000); // Toutes les 30 secondes