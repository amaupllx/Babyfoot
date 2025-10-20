"""
Application Flask principale - Routes API
"""
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from utils import (
    init_csv_files, read_teams, write_team, update_team, delete_team,
    calculate_odds, add_match, read_matches,
    read_scheduled_matches, add_scheduled_match, delete_scheduled_match,
    verify_user, get_user_credits, is_admin, add_bet, get_user_bets
)

app = Flask(__name__)
app.secret_key = 'weeznamax_secret_key_2024'  # Changez ceci en production


# ========== ROUTES PUBLIQUES ==========

@app.route('/')
def login_page():
    """Page de connexion"""
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    """Connexion utilisateur"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if verify_user(username, password):
        session['username'] = username
        session['is_admin'] = is_admin(username)
        return jsonify({
            'success': True, 
            'is_admin': is_admin(username),
            'redirect': '/admin' if is_admin(username) else '/user'
        })
    else:
        return jsonify({'success': False, 'message': 'Identifiants incorrects'}), 401


@app.route('/logout')
def logout():
    """Déconnexion"""
    session.clear()
    return redirect(url_for('login_page'))


# ========== ROUTES ADMIN ==========

@app.route('/admin')
def admin():
    """Page d'administration"""
    if 'username' not in session or not session.get('is_admin'):
        return redirect(url_for('login_page'))
    return render_template('index.html')


@app.route('/api/teams', methods=['GET', 'POST'])
def teams():
    """API pour gérer les équipes"""
    if 'username' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'POST':
        data = request.json
        write_team(data['name'], data['elo'], data.get('poule', ''))
        return jsonify({'success': True})
    else:
        return jsonify(read_teams())


@app.route('/api/teams/update', methods=['PUT'])
def update_team_route():
    """API pour modifier une équipe"""
    if 'username' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    update_team(
        data['old_name'], 
        data['new_name'], 
        data['new_elo'], 
        data['new_poule']
    )
    return jsonify({'success': True})


@app.route('/api/teams/<name>', methods=['DELETE'])
def delete_team_route(name):
    """API pour supprimer une équipe"""
    if 'username' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    delete_team(name)
    return jsonify({'success': True})


@app.route('/api/scheduled', methods=['GET', 'POST'])
def scheduled():
    """API pour gérer les matchs programmés"""
    if 'username' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    if request.method == 'POST':
        data = request.json
        match_id = add_scheduled_match(data['team1'], data['team2'])
        return jsonify({'success': True, 'id': match_id})
    else:
        return jsonify(read_scheduled_matches())


@app.route('/api/scheduled/<int:match_id>', methods=['DELETE'])
def delete_scheduled(match_id):
    """API pour supprimer un match programmé"""
    if 'username' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    delete_scheduled_match(match_id)
    return jsonify({'success': True})


@app.route('/api/match', methods=['POST'])
def match():
    """API pour enregistrer un match terminé"""
    if 'username' not in session or not session.get('is_admin'):
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    result = add_match(
        data['team1'], 
        data['team2'], 
        data['score1'], 
        data['score2'],
        data.get('scheduled_id')
    )
    if result:
        return jsonify(result)
    return jsonify({'error': 'Error adding match'}), 400


@app.route('/api/history')
def history():
    """API pour l'historique des matchs"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify(read_matches())


# ========== ROUTES UTILISATEUR ==========

@app.route('/user')
def user_page():
    """Page utilisateur"""
    if 'username' not in session or session.get('is_admin'):
        return redirect(url_for('login_page'))
    return render_template('user.html')


@app.route('/api/user/info')
def user_info():
    """Récupère les infos de l'utilisateur connecté"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session['username']
    return jsonify({
        'username': username,
        'credits': get_user_credits(username)
    })


@app.route('/api/user/matches')
def user_matches():
    """Récupère les matchs disponibles pour parier"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify(read_scheduled_matches())


@app.route('/api/odds')
def odds():
    """API pour calculer les cotes"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    team1 = request.args.get('team1')
    team2 = request.args.get('team2')
    
    teams = read_teams()
    team1_data = next((t for t in teams if t['name'] == team1), None)
    team2_data = next((t for t in teams if t['name'] == team2), None)
    
    if not team1_data or not team2_data:
        return jsonify({'error': 'Team not found'}), 404
    
    elo1 = team1_data['elo']
    elo2 = team2_data['elo']
    
    odds_data = calculate_odds(elo1, elo2)
    
    return jsonify({
        'team1': team1, 'team2': team2,
        'elo1': elo1, 'elo2': elo2,
        **odds_data
    })


@app.route('/api/user/bet', methods=['POST'])
def place_bet():
    """Placer un pari"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session['username']
    data = request.json
    
    match_id = data['match_id']
    bet_type = data['bet_type']  # 'team1', 'team2', ou 'draw'
    amount = float(data['amount'])
    odds = float(data['odds'])
    
    # Vérifier que l'utilisateur a assez de crédits
    credits = get_user_credits(username)
    if amount > credits:
        return jsonify({'error': 'Crédits insuffisants'}), 400
    
    if amount <= 0:
        return jsonify({'error': 'Montant invalide'}), 400
    
    bet_id = add_bet(username, match_id, bet_type, amount, odds)
    
    return jsonify({
        'success': True,
        'bet_id': bet_id,
        'new_credits': get_user_credits(username)
    })


@app.route('/api/user/bets')
def user_bets():
    """Récupère les paris de l'utilisateur"""
    if 'username' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    username = session['username']
    return jsonify(get_user_bets(username))


if __name__ == '__main__':
    init_csv_files()
    print("🏆 Serveur Weeznamax démarré !")
    print("📊 Ouvrez votre navigateur à l'adresse: http://localhost:5000")
    print("💾 Les données sont sauvegardées dans:")
    print("   - teams.csv (équipes)")
    print("   - scheduled_matches.csv (matchs programmés)")
    print("   - matches.csv (matchs terminés)")
    print("   - users.csv (utilisateurs)")
    print("   - bets.csv (paris)")
    print("\n👤 Comptes créés par défaut:")
    print("   Admin: admin / admin123")
    print("   User:  user1 / pass123 (100 Wiz)")
    app.run(debug=True, port=5000)