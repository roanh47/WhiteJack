# Ronde 3 - Laatste ronde, meerdere ticks toegestaan
# Speler kan blijven tikken tot 6 dobbelstenen of bust
# Scar speelt uit aan het einde

from flask import Blueprint, render_template, session, redirect, url_for, request
import random
from game_logic import Game

round3_bp = Blueprint('Round3', __name__)


@round3_bp.route('/r3-action', methods=['POST'])
def action_r3():
    """Ronde 3 acties: tick of snip (laatste ronde)"""
    g = session.get('game')
    if not g or g.get('round') != 3:
        return redirect(url_for('index'))
    
    action = request.form.get('actie')
    rolls = g['rolls']
    
    if action == 'tick':
        # Rol nog een d12
        rolls.append(random.randint(1, 12))
        
    elif action == 'snip':
        # Behoud huidige, eindig spel
        pass
    
    total = sum(rolls)
    
    # Check voor bust
    if total > 24:
        g['result'] = 'Bust'
        g['active'] = False
    
    # Check voor 6 dobbelstenen auto-win
    elif len(rolls) >= 6:
        g['result'] = 'Win (6 dice)'
        g['active'] = False
    
    # Spel eindigt na deze ronde (snip of na tick)
    if not g['result'] or action == 'snip':
        # Scar speelt uit (rolt tot 18, 24, of bust)
        scar = g['scar_rolls']
        while sum(scar) < 18 and sum(scar) != 24:
            scar.append(random.randint(1, 12))
            if sum(scar) > 24:
                break
        g['scar_rolls'] = scar
        
        # Bepaal winnaar
        scar_total = sum(scar)
        if scar_total > 24:
            g['result'] = 'Win (Scar bust)'
        elif total > scar_total:
            g['result'] = 'Win'
        elif total < scar_total:
            g['result'] = 'Lose'
        else:
            g['result'] = 'Push'
    
    g['rolls'] = rolls
    g['game_over'] = True
    g['active'] = False
    session['game'] = g
    
    class Hand:
        pass
    hand = Hand()
    hand.__dict__.update(g)
    
    return render_template('game.html',
        hand=hand,
        scar={'rolls': g['scar_rolls']},
        player_total=total,
        scar_total=sum(g['scar_rolls']),
        round_no=3,
        game_over=True
    )
