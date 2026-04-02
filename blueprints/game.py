import random
from flask import Blueprint, render_template, session, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from models import User
from extensions import db

game_bp = Blueprint('game', __name__)


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
# ROUTES
# =============================================================================
@game_bp.route('/lobby')
@login_required
def lobby():
    """Lobby - toon je geld en start knop"""
    return render_template('lobby.html', user=current_user)


@game_bp.route('/start', methods=['POST'])
@login_required
def start():
    """Start een nieuw spel - check of gebruiker genoeg geld heeft"""
    bet = int(request.form.get('bet', 1))
    if bet > current_user.money:
        flash('Je hebt niet genoeg geld!', 'error')
        return redirect(url_for('game.lobby'))
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
    return redirect(url_for('game.game'))


@game_bp.route('/game', methods=['GET', 'POST'])
@login_required
def game():
    """Het spel zelf"""
    if request.method == 'POST':
        actie = request.form.get('actie')
        spel = session.get('spel')
        if not spel or spel.get('game_over'):
            return redirect(url_for('game.lobby'))

        if actie == 'tick':
            if not openingsworp_gedaan(spel):
                doe_openingsworp(spel)
                verwerk_openingsworp(spel)
            else:
                spel['rolls'].append(rol_d12())
            if not spel['game_over']:
                verwerk_speler_totaal(spel)

        elif actie == 'snip':
            if not openingsworp_gedaan(spel):
                flash('Je moet eerst je openingsworp doen.', 'error')
            else:
                spel['player_done'] = True
                bepaal_winaar(spel)
                spel['game_over'] = True

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
                    spel['player_done'] = True
                    bepaal_winaar(spel)
                    spel['game_over'] = True

        session['spel'] = spel

    spel = session.get('spel')
    if not spel:
        return redirect(url_for('game.lobby'))

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if is_ajax:
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


@game_bp.route('/scoreboard')
@login_required
def scoreboard():
    """Scoreboard - overzicht van alle spelers"""
    spelers = User.query.order_by(User.money.desc()).all()
    return render_template('scoreboard.html', spelers=spelers)


@game_bp.route('/reset')
@login_required
def reset():
    """Reset het spel en start opnieuw met dezelfde inzet"""
    spel = session.get('spel')
    original_bet = spel.get('original_bet', 1) if spel else 1
    if original_bet > current_user.money:
        session.pop('spel', None)
        return redirect(url_for('game.lobby'))
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
    return redirect(url_for('game.game'))
