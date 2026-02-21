# Ronde 2 - Speler mag 1 keer ticken (rollen) of snippen (passen)
# Scar rolt mee als speler tickt

from flask import Blueprint, render_template, session, redirect, url_for, request
import random
from game_logic import Game

round2_bp = Blueprint('Round2', __name__)


@round2_bp.route('/r2-action', methods=['POST'])
def action_r2():
    """Ronde 2 acties: tick (1 keer), snip, of cut the fuse"""
    g = session.get('game')
    if not g or g.get('round') != 2:
        return redirect(url_for('index'))
    
    action = request.form.get('actie')
    rolls = g['rolls']
    
    if action == 'tick':
        # Speler rolt 1d12 (slechts 1 tick toegestaan in ronde 2)
        rolls.append(random.randint(1, 12))
        # Scar rolt ook mee (tenzij die al 24 heeft)
        scar_busted = False
        if sum(g['scar_rolls']) != 24:
            g['scar_rolls'].append(random.randint(1, 12))
            # Check of Scar bust is
            if sum(g['scar_rolls']) > 24:
                g['result'] = 'Win (Scar bust)'
                g['active'] = False
                g['game_over'] = True
                scar_busted = True
        
        # Check of speler bust is
        if sum(rolls) > 24:
            g['result'] = 'Bust'
            g['active'] = False
            g['game_over'] = True
            # Scar speelt uit
            scar = g['scar_rolls']
            while sum(scar) < 18 and sum(scar) != 24:
                scar.append(random.randint(1, 12))
                if sum(scar) > 24:
                    break
            g['scar_rolls'] = scar
        
        # Na tick altijd door naar Ronde 3 (tenzij spel afgelopen)
        g['rolls'] = rolls
        session['game'] = g
        if not g['game_over']:
            g['round'] = 3
            session['game'] = g
            return redirect(url_for('Round3.show'))
        
    elif action == 'cut':
        # Cut the fuse: verdubbel inzet, rol 1 keer, dan door naar r3
        g['bet'] *= 2
        g['cut_used'] = True
        rolls.append(random.randint(1, 12))
        # Scar rolt ook mee (tenzij die al 24 heeft)
        scar_busted = False
        if sum(g['scar_rolls']) != 24:
            g['scar_rolls'].append(random.randint(1, 12))
            # Check of Scar bust is
            if sum(g['scar_rolls']) > 24:
                g['result'] = 'Win (Scar bust)'
                g['active'] = False
                g['game_over'] = True
                scar_busted = True
        g['rolls'] = rolls
        session['game'] = g
        # Als Scar bust is, eindig spel. Anders door naar Ronde 3
        if scar_busted:
            class Hand:
                pass
            hand = Hand()
            hand.__dict__.update(g)
            return render_template('game.html',
                hand=hand,
                scar={'rolls': g['scar_rolls']},
                player_total=sum(rolls),
                scar_total=sum(g['scar_rolls']),
                round_no=3,
                game_over=True
            )
        g['round'] = 3
        return redirect(url_for('Round3.show'))
        
    elif action == 'snip':
        # Behoud huidige totaal, ga naar ronde 3 (geen rollen)
        g['rolls'] = rolls
        g['round'] = 3
        session['game'] = g
        return redirect(url_for('Round3.show'))
    
    # Check voor bust
    total = sum(rolls)
    if total > 24:
        g['result'] = 'Bust'
        g['active'] = False
        g['game_over'] = True
        # Scar speelt uit
        scar = g['scar_rolls']
        while sum(scar) < 18 and sum(scar) != 24:
            scar.append(random.randint(1, 12))
            if sum(scar) > 24:
                break
        g['scar_rolls'] = scar
    
    # Check voor 6 dobbelstenen auto-win
    elif len(rolls) >= 6:
        g['result'] = 'Win (6 dice)'
        g['active'] = False
        g['game_over'] = True
        # Scar speelt uit
        scar = g['scar_rolls']
        while sum(scar) < 18 and sum(scar) != 24:
            scar.append(random.randint(1, 12))
            if sum(scar) > 24:
                break
        g['scar_rolls'] = scar
    
    g['rolls'] = rolls
    session['game'] = g
    
    # Maak mock object voor template
    class Hand:
        pass
    hand = Hand()
    hand.__dict__.update(g)
    
    return render_template('game.html',
        hand=hand,
        scar={'rolls': g['scar_rolls']},
        player_total=sum(rolls),
        scar_total=sum(g['scar_rolls']),
        round_no=2 if not g['game_over'] else 3,
        game_over=g['game_over']
    )
