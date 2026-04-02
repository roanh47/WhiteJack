# WhiteJack - Een dobbelspel met gebruikersauthenticatie
# Doel: kom zo dicht mogelijk bij 24 zonder erover te gaan

from flask import Flask, render_template, session, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import text
from functools import wraps
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'GeweldigeGokSite'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///whitejack.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# =============================================================================
# DATABASE MODELLEN
# =============================================================================
class User(UserMixin, db.Model):
    """Gebruiker model - slaat username, wachtwoord en geld op"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    money = db.Column(db.Integer, default=100)  # Start met €100
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Integer, default=0)
    
    def set_password(self, password):
        """Hash het wachtwoord voor veilige opslag"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Controleer of het wachtwoord klopt"""
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    """Laad gebruiker op basis van ID (nodig voor Flask-Login)"""
    return User.query.get(int(user_id))


# =============================================================================
# AUTHENTICATIE ROUTES (Login / Register)
# =============================================================================
@app.route('/')
def index():
    """Start pagina - als niet ingelogd, toon login/register keuze"""
    if current_user.is_authenticated:
        return redirect(url_for('lobby'))
    return render_template('auth.html')


@app.route('/login', methods=['POST'])
def login():
    """Inloggen met bestaand account"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        login_user(user)
        return redirect(url_for('lobby'))
    else:
        flash('Verkeerde gebruikersnaam of wachtwoord', 'error')
        return redirect(url_for('index'))


@app.route('/register', methods=['POST'])
def register():
    """Nieuw account aanmaken"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Check of username al bestaat
    if User.query.filter_by(username=username).first():
        flash('Gebruikersnaam is al in gebruik', 'error')
        return redirect(url_for('index'))
    
    # Maak nieuwe gebruiker
    new_user = User(username=username, money=100)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()
    
    # Log direct in
    login_user(new_user)
    flash('Account aangemaakt! Je krijgt €100 startgeld.', 'success')
    return redirect(url_for('lobby'))


@app.route('/logout')
@login_required
def logout():
    """Uitloggen"""
    logout_user()
    session.pop('spel', None)
    return redirect(url_for('index'))


# =============================================================================
# LOBBY - Waar je het spel start
# =============================================================================
@app.route('/lobby')
@login_required
def lobby():
    """Lobby - toon je geld en start knop"""
    return render_template('lobby.html', user=current_user)


# =============================================================================
# SPEL LOGICA (aangepast voor gebruikers)
# =============================================================================
@app.route('/start', methods=['POST'])
@login_required
def start():
    """Start een nieuw spel - check of gebruiker genoeg geld heeft"""
    bet = int(request.form.get('bet', 1))
    
    # Check of gebruiker genoeg geld heeft
    if bet > current_user.money:
        flash('Je hebt niet genoeg geld!', 'error')
        return redirect(url_for('lobby'))
    
    # Start spel
    session['spel'] = {
        'bet': bet,
        'original_bet': bet,
        'rolls': [],
        'scar_rolls': [],
        'cut_used': False,
        'resultaat': None,
        'game_over': False,
        'player_done': False
    }
    
    return redirect(url_for('game'))


@app.route('/game', methods=['GET', 'POST'])
@login_required
def game():
    """Het spel zelf"""
    
    if request.method == 'POST':
        actie = request.form.get('actie')
        spel = session.get('spel')
        
        if not spel or spel.get('game_over'):
            return redirect(url_for('lobby'))
        
        # TICK: first tick performs the initial 2d12 opening deal, later ticks add 1 die.
        if actie == 'tick':
            if not openingsworp_gedaan(spel):
                doe_openingsworp(spel)
                verwerk_openingsworp(spel)
            else:
                spel['rolls'].append(rol_d12())

            if not spel['game_over']:
                verwerk_speler_totaal(spel)
        
        # SNIP: Stand, let Scar play
        elif actie == 'snip':
            if not openingsworp_gedaan(spel):
                flash('Je moet eerst je openingsworp doen.', 'error')
            else:
                spel['player_done'] = True
                bepaal_winaar(spel)
                spel['game_over'] = True
        
        # CUT: Double down, roll exactly 1 more, then stand
        elif actie == 'cut':
            if spel['cut_used']:
                flash('Cut the Fuse is al gebruikt!', 'error')
            elif not openingsworp_gedaan(spel):
                flash('Cut the Fuse kan pas na je eerste twee ticks.', 'error')
            else:
                spel['cut_used'] = True
                spel['bet'] *= 2
                spel['rolls'].append(rol_d12())

                if not verwerk_speler_totaal(spel):
                    # Cut always ends player's turn
                    spel['player_done'] = True
                    bepaal_winaar(spel)
                    spel['game_over'] = True
        
        session['spel'] = spel
    
    spel = session.get('spel')
    if not spel:
        return redirect(url_for('lobby'))
    
    # Check if this is an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if is_ajax:
        from flask import jsonify
        return jsonify({
            'rolls': spel.get('rolls', []),
            'scar_rolls': spel.get('scar_rolls', []),
            'player_total': sum(spel.get('rolls', [])),
            'scar_total': sum(spel.get('scar_rolls', [])),
            'game_over': spel.get('game_over', False),
            'resultaat': spel.get('resultaat'),
            'bet': spel.get('bet'),
            'cut_used': spel.get('cut_used', False),
            'is_initial_deal': (len(spel.get('rolls', [])) == 2 and len(spel.get('scar_rolls', [])) == 2),
            'money': current_user.money
        })
    
    return render_template('game.html',
        spel=spel,
        player_total=sum(spel.get('rolls', [])),
        scar_total=sum(spel.get('scar_rolls', [])),
        user=current_user,
        is_initial_deal=(len(spel.get('rolls', [])) == 2 and len(spel.get('scar_rolls', [])) == 2)
    )


@app.route('/scoreboard')
@login_required
def scoreboard():
    """Scoreboard - overzicht van alle spelers"""
    spelers = User.query.order_by(User.money.desc()).all()
    return render_template('scoreboard.html', spelers=spelers)


@app.route('/reset')
@login_required
def reset():
    """Reset het spel en start opnieuw met dezelfde inzet"""
    spel = session.get('spel')
    original_bet = spel.get('original_bet', 1) if spel else 1

    if original_bet > current_user.money:
        session.pop('spel', None)
        return redirect(url_for('lobby'))

    session['spel'] = {
        'bet': original_bet,
        'original_bet': original_bet,
        'rolls': [],
        'scar_rolls': [],
        'cut_used': False,
        'resultaat': None,
        'game_over': False,
        'player_done': False
    }
    return redirect(url_for('game'))


# =============================================================================
# GELD BEHEER
# =============================================================================
def win_money(amount):
    """Geef winst aan gebruiker"""
    current_user.money += amount
    current_user.wins += 1
    db.session.commit()
    flash(f'Je wint €{amount}!', 'success')


def lose_money(amount):
    """Haal verlies af van gebruiker"""
    current_user.money -= amount
    current_user.losses += 1
    db.session.commit()
    flash(
        f'Je hebt de vorige ronde {amount} euro verloren. '
        '99% van alle ex-gokkers zijn gestopt voor het winnen van de jackpot.',
        'error'
    )


# =============================================================================
# HELPERS
# =============================================================================
def rol_d12():
    """Rol een d12"""
    return random.randint(1, 12)


def openingsworp_gedaan(spel):
    """Check of de eerste worp voor speler en Scar al is gedaan."""
    return len(spel['rolls']) >= 2 and len(spel['scar_rolls']) >= 2


def beeindig_spel(spel, resultaat, bedrag=None, uitkomst=None):
    """Zet de eindstatus van het spel en verwerkt winst/verlies."""
    spel['resultaat'] = resultaat
    spel['game_over'] = True
    spel['player_done'] = True

    if uitkomst == 'win' and bedrag is not None:
        win_money(bedrag)
    elif uitkomst == 'lose' and bedrag is not None:
        lose_money(bedrag)


def doe_openingsworp(spel):
    """Geef speler en Scar hun eerste twee dobbelstenen."""
    spel['rolls'] = [rol_d12(), rol_d12()]
    spel['scar_rolls'] = [rol_d12(), rol_d12()]


def verwerk_openingsworp(spel):
    """Verwerk directe Whitejack-resultaten van de openingsworp."""
    player_total = sum(spel['rolls'])
    scar_total = sum(spel['scar_rolls'])

    if player_total == 24 and scar_total == 24:
        beeindig_spel(spel, 'Gelijkspel! Jullie hebben allebei Whitejack!')
        flash('Gelijkspel - je krijgt je inzet terug', 'info')
    elif player_total == 24:
        beeindig_spel(spel, 'Whitejack! Je wint!', spel['bet'] * 2, 'win')
    elif scar_total == 24:
        beeindig_spel(spel, 'Scar heeft Whitejack! Je verliest.', spel['bet'], 'lose')


def verwerk_speler_totaal(spel):
    """Controleer of de speler bust gaat of automatisch wint."""
    player_total = sum(spel['rolls'])

    if player_total > 24:
        beeindig_spel(spel, 'Bust! Je bent over 24.', spel['bet'], 'lose')
        return True

    if len(spel['rolls']) >= 6:
        beeindig_spel(spel, '6 dice! Auto-win!', spel['bet'] * 2, 'win')
        return True

    return False


def scar_speelt_uit(spel):
    """Scar rolt tot 18, 24, of bust"""
    scar = spel['scar_rolls']
    while sum(scar) < 18 and sum(scar) != 24:
        scar.append(rol_d12())
        if sum(scar) > 24:
            break
    spel['scar_rolls'] = scar


def bepaal_winaar(spel):
    """Bepaal winnaar en update geld"""
    speler = sum(spel['rolls'])
    scar = sum(spel['scar_rolls'])
    
    if sum(spel['scar_rolls']) < 18 and sum(spel['scar_rolls']) != 24:
        scar_speelt_uit(spel)
        scar = sum(spel['scar_rolls'])
    
    if scar > 24:
        spel['resultaat'] = 'Je wint! Scar is bust.'
        win_money(spel['bet'] * 2)
    elif speler > scar:
        spel['resultaat'] = 'Je wint!'
        win_money(spel['bet'] * 2)
    elif speler < scar:
        spel['resultaat'] = 'Je verliest!'
        lose_money(spel['bet'])
    else:
        spel['resultaat'] = 'Gelijkspel!'
        flash('Gelijkspel - je krijgt je inzet terug', 'info')


# =============================================================================
# ADMIN
# =============================================================================
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Geen toegang.', 'error')
            return redirect(url_for('lobby'))
        return f(*args, **kwargs)
    return decorated


@app.route('/admin')
@login_required
@admin_required
def admin():
    users = User.query.order_by(User.username).all()
    return render_template('admin.html', users=users)


@app.route('/admin/create', methods=['POST'])
@login_required
@admin_required
def admin_create():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    money = int(request.form.get('money', 100))
    if not username or not password:
        flash('Gebruikersnaam en wachtwoord zijn verplicht.', 'error')
        return redirect(url_for('admin'))
    if User.query.filter_by(username=username).first():
        flash(f'"{username}" bestaat al.', 'error')
        return redirect(url_for('admin'))
    user = User(username=username, money=money)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash(f'Gebruiker "{username}" aangemaakt.', 'success')
    return redirect(url_for('admin'))


@app.route('/admin/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Je kunt jezelf niet verwijderen.', 'error')
        return redirect(url_for('admin'))
    db.session.delete(user)
    db.session.commit()
    flash(f'Gebruiker "{user.username}" verwijderd.', 'success')
    return redirect(url_for('admin'))


@app.route('/admin/set-money/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_set_money(user_id):
    user = User.query.get_or_404(user_id)
    amount = int(request.form.get('amount', 0))
    user.money = amount
    db.session.commit()
    flash(f'Geld van "{user.username}" ingesteld op €{amount}.', 'success')
    return redirect(url_for('admin'))


@app.route('/admin/reset-password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('password', '').strip()
    if not new_password:
        flash('Nieuw wachtwoord is verplicht.', 'error')
        return redirect(url_for('admin'))
    user.set_password(new_password)
    db.session.commit()
    flash(f'Wachtwoord van "{user.username}" gereset.', 'success')
    return redirect(url_for('admin'))


@app.route('/admin/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Je kunt je eigen admin-status niet wijzigen.', 'error')
        return redirect(url_for('admin'))
    user.is_admin = 0 if user.is_admin else 1
    db.session.commit()
    status = 'admin' if user.is_admin else 'geen admin'
    flash(f'"{user.username}" is nu {status}.', 'success')
    return redirect(url_for('admin'))


@app.route('/admin/reset-stats/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_reset_stats(user_id):
    user = User.query.get_or_404(user_id)
    user.wins = 0
    user.losses = 0
    db.session.commit()
    flash(f'Stats van "{user.username}" gereset.', 'success')
    return redirect(url_for('admin'))


# =============================================================================
# DATABASE AANMAKEN
# =============================================================================
with app.app_context():
    db.create_all()
    # Migratie: voeg wins/losses kolommen toe aan bestaande databases
    for kolom in ('wins', 'losses', 'is_admin'):
        try:
            db.session.execute(text(f'ALTER TABLE user ADD COLUMN {kolom} INTEGER DEFAULT 0'))
            db.session.commit()
        except Exception:
            db.session.rollback()
    # Zorg dat Roan admin is
    roan = User.query.filter_by(username='Roan').first()
    if roan and not roan.is_admin:
        roan.is_admin = 1
        db.session.commit()


if __name__ == '__main__':
    app.run(debug=True)
    