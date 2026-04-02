from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import User
from extensions import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    """Start pagina - als niet ingelogd, toon login/register keuze"""
    if current_user.is_authenticated:
        return redirect(url_for('game.lobby'))
    return render_template('auth.html')


@auth_bp.route('/login', methods=['POST'])
def login():
    """Inloggen met bestaand account"""
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        login_user(user)
        return redirect(url_for('game.lobby'))
    else:
        flash('Verkeerde gebruikersnaam of wachtwoord', 'error')
        return redirect(url_for('auth.index'))


@auth_bp.route('/register', methods=['POST'])
def register():
    """Nieuw account aanmaken"""
    username = request.form.get('username')
    password = request.form.get('password')
    if User.query.filter_by(username=username).first():
        flash('Gebruikersnaam is al in gebruik', 'error')
        return redirect(url_for('auth.index'))
    new_user = User(username=username, money=100)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    login_user(new_user)
    flash('Account aangemaakt! Je krijgt €100 startgeld.', 'success')
    return redirect(url_for('game.lobby'))


@auth_bp.route('/logout')
@login_required
def logout():
    """Uitloggen"""
    logout_user()
    session.pop('spel', None)
    return redirect(url_for('auth.index'))
