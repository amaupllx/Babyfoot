"""
Fonctions de gestion des équipes, matchs et calculs Elo
"""
import csv
import os
from datetime import datetime
import math

# Fichiers CSV
TEAMS_FILE = 'teams.csv'
MATCHES_FILE = 'matches.csv'
SCHEDULED_FILE = 'scheduled_matches.csv'
USERS_FILE = 'users.csv'
BETS_FILE = 'bets.csv'

# Paramètres Elo
K_FACTOR = 32
ELO_BASE = 400


def init_csv_files():
    """Initialise les fichiers CSV s'ils n'existent pas"""
    if not os.path.exists(TEAMS_FILE):
        with open(TEAMS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['name', 'elo', 'poule'])
    
    if not os.path.exists(MATCHES_FILE):
        with open(MATCHES_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['date', 'team1', 'team2', 'score1', 'score2', 
                           'elo1_before', 'elo1_after', 'elo1_change',
                           'elo2_before', 'elo2_after', 'elo2_change'])
    
    if not os.path.exists(SCHEDULED_FILE):
        with open(SCHEDULED_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['id', 'team1', 'team2', 'date_created', 'can_bet'])
    
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['username', 'password', 'credits'])
            # Créer un utilisateur admin et un utilisateur de test
            writer.writerow(['admin', 'admin123', '0'])
            writer.writerow(['user1', 'pass123', '100'])
    
    if not os.path.exists(BETS_FILE):
        with open(BETS_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['bet_id', 'username', 'match_id', 'bet_type', 'amount', 'odds', 'status', 'date'])


# ============ GESTION DES UTILISATEURS ============

def read_users():
    """Lit tous les utilisateurs depuis le CSV"""
    users = []
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            users.append({
                'username': row['username'],
                'password': row['password'],
                'credits': float(row['credits'])
            })
    return users


def verify_user(username, password):
    """Vérifie les identifiants d'un utilisateur"""
    users = read_users()
    for user in users:
        if user['username'] == username and user['password'] == password:
            return True
    return False


def get_user_credits(username):
    """Récupère les crédits d'un utilisateur"""
    users = read_users()
    for user in users:
        if user['username'] == username:
            return user['credits']
    return 0


def update_user_credits(username, new_credits):
    """Met à jour les crédits d'un utilisateur"""
    users = read_users()
    with open(USERS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['username', 'password', 'credits'])
        for user in users:
            if user['username'] == username:
                writer.writerow([username, user['password'], new_credits])
            else:
                writer.writerow([user['username'], user['password'], user['credits']])


def is_admin(username):
    """Vérifie si l'utilisateur est admin"""
    return username == 'admin'


def add_credits_to_all_users(amount=10):
    """Ajoute un montant de crédits à tous les utilisateurs"""
    users = read_users()
    with open(USERS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['username', 'password', 'credits'])
        for user in users:
            new_credits = user['credits'] + amount
            writer.writerow([user['username'], user['password'], new_credits])
            print(f"   💰 {user['username']} a reçu {amount} Wiz (total: {new_credits} Wiz)")
    
    return len(users)


def get_leaderboard(limit=10):
    """Récupère le classement des utilisateurs par crédits (top limit)"""
    users = read_users()
    # Trier par crédits décroissants
    users_sorted = sorted(users, key=lambda x: x['credits'], reverse=True)
    # Retourner seulement les N premiers (et exclure admin si souhaité)
    return [u for u in users_sorted if u['username'] != 'admin'][:limit]


# ============ GESTION DES PARIS ============

def read_bets():
    """Lit tous les paris depuis le CSV"""
    bets = []
    with open(BETS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            bets.append(row)
    return bets


def add_bet(username, match_id, bet_type, amount, odds):
    """Ajoute un pari"""
    bets = read_bets()
    # Trouver le prochain ID
    if bets:
        next_id = max(int(b['bet_id']) for b in bets) + 1
    else:
        next_id = 1
    
    with open(BETS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            next_id, username, match_id, bet_type, amount, odds, 'pending',
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    # Déduire les crédits
    current_credits = get_user_credits(username)
    update_user_credits(username, current_credits - amount)
    
    return next_id


def get_user_bets(username):
    """Récupère tous les paris d'un utilisateur"""
    bets = read_bets()
    return [bet for bet in bets if bet['username'] == username]


def process_match_bets(match_id, team1, team2, score1, score2):
    """Traite tous les paris d'un match terminé - APPELÉ PAR L'ADMIN"""
    bets = read_bets()
    
    # Déterminer le résultat
    if score1 > score2:
        result = 'team1'
    elif score2 > score1:
        result = 'team2'
    else:
        result = 'draw'
    
    print(f"🎯 Traitement des paris pour le match ID {match_id}")
    print(f"   Résultat: {result} ({team1} {score1}-{score2} {team2})")
    
    # Mettre à jour tous les paris pour ce match
    with open(BETS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['bet_id', 'username', 'match_id', 'bet_type', 'amount', 'odds', 'status', 'date'])
        print(len(bets))
        for bet in bets:
            if bet['match_id'] == str(match_id) and bet['status'] == 'pending':
                # Ce pari concerne ce match
                if result == 'draw':
                    # Match nul : rembourser tous les paris
                    refund_amount = float(bet['amount'])
                    current_credits = get_user_credits(bet['username'])
                    update_user_credits(bet['username'], current_credits + refund_amount)
                    print(f"   🔄 {bet['username']} a été remboursé de {refund_amount:.2f} Wiz (match nul)")
                    writer.writerow([bet['bet_id'], bet['username'], bet['match_id'], 
                                   bet['bet_type'], bet['amount'], bet['odds'], 'refunded', bet['date']])
                elif bet['bet_type'] == result:
                    # L'utilisateur a gagné
                    winnings = float(bet['amount']) * float(bet['odds'])
                    current_credits = get_user_credits(bet['username'])
                    update_user_credits(bet['username'], current_credits + winnings)
                    print(f"   ✅ {bet['username']} a gagné {winnings:.2f} Wiz")
                    writer.writerow([bet['bet_id'], bet['username'], bet['match_id'], 
                                   bet['bet_type'], bet['amount'], bet['odds'], 'won', bet['date']])
                else:
                    # L'utilisateur a perdu
                    print(f"   ❌ {bet['username']} a perdu {bet['amount']} Wiz")
                    writer.writerow([bet['bet_id'], bet['username'], bet['match_id'], 
                                   bet['bet_type'], bet['amount'], bet['odds'], 'lost', bet['date']])
            else:
                # Garder les autres paris tels quels
                writer.writerow([bet['bet_id'], bet['username'], bet['match_id'], 
                               bet['bet_type'], bet['amount'], bet['odds'], bet['status'], bet['date']])


# ============ GESTION DES ÉQUIPES ============

def read_teams():
    """Lit toutes les équipes depuis le CSV"""
    teams = []
    with open(TEAMS_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            teams.append({
                'name': row['name'], 
                'elo': int(row['elo']),
                'poule': row.get('poule', '')
            })
    return teams


def write_team(name, elo, poule=''):
    """Ajoute une équipe au CSV"""
    with open(TEAMS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([name, elo, poule])


def update_team(old_name, new_name, new_elo, new_poule):
    """Met à jour une équipe (nom, elo, poule)"""
    teams = read_teams()
    with open(TEAMS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'elo', 'poule'])
        for team in teams:
            if team['name'] == old_name:
                writer.writerow([new_name, new_elo, new_poule])
            else:
                writer.writerow([team['name'], team['elo'], team['poule']])


def delete_team(name):
    """Supprime une équipe"""
    teams = read_teams()
    with open(TEAMS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'elo', 'poule'])
        for team in teams:
            if team['name'] != name:
                writer.writerow([team['name'], team['elo'], team['poule']])


def update_team_elo(name, new_elo):
    """Met à jour uniquement l'Elo d'une équipe"""
    teams = read_teams()
    with open(TEAMS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['name', 'elo', 'poule'])
        for team in teams:
            if team['name'] == name:
                writer.writerow([name, new_elo, team['poule']])
            else:
                writer.writerow([team['name'], team['elo'], team['poule']])


# ============ MATCHS PROGRAMMÉS ============

def read_scheduled_matches():
    """Lit tous les matchs programmés"""
    matches = []
    with open(SCHEDULED_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            matches.append(row)
    return matches


def add_scheduled_match(team1, team2):
    """Ajoute un match programmé avec can_bet=True par défaut"""
    matches = read_scheduled_matches()
    # Trouver le prochain ID
    if matches:
        next_id = max(int(m['id']) for m in matches) + 1
    else:
        next_id = 1
    
    with open(SCHEDULED_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([next_id, team1, team2, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'True'])
    
    return next_id


def delete_scheduled_match(match_id):
    """Supprime un match programmé"""
    matches = read_scheduled_matches()
    with open(SCHEDULED_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'team1', 'team2', 'date_created', 'can_bet'])
        for match in matches:
            if match['id'] != str(match_id):
                can_bet = match.get('can_bet', 'True')  # Par défaut True pour la rétrocompatibilité
                writer.writerow([match['id'], match['team1'], match['team2'], match['date_created'], can_bet])


def toggle_bet_status(match_id):
    """Bascule le statut can_bet d'un match (True <-> False)"""
    matches = read_scheduled_matches()
    with open(SCHEDULED_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id', 'team1', 'team2', 'date_created', 'can_bet'])
        for match in matches:
            if match['id'] == str(match_id):
                # Inverser le statut
                current_status = match.get('can_bet', 'True')
                new_status = 'False' if current_status == 'True' else 'True'
                writer.writerow([match['id'], match['team1'], match['team2'], match['date_created'], new_status])
                print(f"🔒 Match {match_id}: Paris {'bloqués' if new_status == 'False' else 'ouverts'}")
            else:
                can_bet = match.get('can_bet', 'True')
                writer.writerow([match['id'], match['team1'], match['team2'], match['date_created'], can_bet])
    
    # Retourner le nouveau statut
    matches = read_scheduled_matches()
    match = next((m for m in matches if m['id'] == str(match_id)), None)
    return match.get('can_bet', 'True') == 'True' if match else True


def check_can_bet(match_id):
    """Vérifie si un match accepte les paris"""
    matches = read_scheduled_matches()
    match = next((m for m in matches if m['id'] == str(match_id)), None)
    if not match:
        return False
    return match.get('can_bet', 'True') == 'True'


# ============ CALCULS ELO ============

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


def calculate_odds(elo1, elo2):
    """Calcule les cotes pour un match entre deux équipes (sans match nul)"""
    # Calcul des probabilités directes (victoire team1 vs team2)
    prob1 = 1 / (1 + math.pow(10, (elo2 - elo1) / ELO_BASE))
    prob2 = 1 - prob1
    
    # Calcul des cotes
    odds1 = round(1 / prob1, 2)
    odds2 = round(1 / prob2, 2)
    
    return {
        'prob1': round(prob1 * 100, 1),
        'prob2': round(prob2 * 100, 1),
        'odds1': odds1,
        'odds2': odds2
    }


# ============ MATCHS TERMINÉS ============

def add_match(team1, team2, score1, score2, scheduled_id=None):
    """Enregistre un match terminé et met à jour les Elos + TRAITE LES PARIS"""
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
    
    # 🔥 TRAITER LES PARIS AUTOMATIQUEMENT
    if scheduled_id:
        process_match_bets(scheduled_id, team1, team2, score1, score2)
        delete_scheduled_match(scheduled_id)
    
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

def add_user(username, password, credits=100):
    """Ajoute un nouvel utilisateur"""
    with open(USERS_FILE, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([username, password, credits])


def update_user(old_username, new_username, new_password, new_credits):
    """Met à jour un utilisateur"""
    users = read_users()
    with open(USERS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['username', 'password', 'credits'])
        for user in users:
            if user['username'] == old_username:
                writer.writerow([new_username, new_password, new_credits])
            else:
                writer.writerow([user['username'], user['password'], user['credits']])


def delete_user(username):
    """Supprime un utilisateur"""
    if username == 'admin':
        return False  # Empêcher la suppression de l'admin
    
    users = read_users()
    with open(USERS_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['username', 'password', 'credits'])
        for user in users:
            if user['username'] != username:
                writer.writerow([user['username'], user['password'], user['credits']])
    return True