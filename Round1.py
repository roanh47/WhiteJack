# Ronde 1 - Start van het spel
# Speler klikt eerst 'Tick', daarna rollen beide partijen 2d12

from flask import Blueprint, render_template, session, redirect, url_for, request
from game_logic import Game
import random

round1_bp = Blueprint('Round1', __name__)


@round1_bp.route('/start', methods=['POST'])
def start():
    """Start Ronde 1 - toon een lege tafel met Tick knop"""
    bet = int(request.form.get('bet', 1))
    
    # Maak nieuw spel met lege worpen
    game = Game(bet)
    
    # Sla spel op in sessie (nog geen worpen)
    session['game'] = {
        'bet': game.hand.bet,
        'rolls': [],           # Leeg - nog niet gerold
        'cut_used': game.hand.cut_used,
        'result': game.hand.result,
        'active': game.hand.active,
        'scar_rolls': [],      # Leeg - nog niet gerold
        'round': 1,
        'game_over': False
    }
    
    # Toon lege tafel met Tick knop
    class EmptyHand:
        def __init__(self, bet):
            self.bet = bet
            self.rolls = []
            self.cut_used = False
            self.result = None
            self.active = True
    
    empty_hand = EmptyHand(bet)
    
    return render_template('game.html',
        hand=empty_hand,
        scar={'rolls': []},
        player_total=0,
        scar_total=0,
        round_no=1,
        game_over=False
    )


@round1_bp.route('/tick-r1', methods=['POST'])
def tick_r1():
    """Tick in Ronde 1: beide rollen 2d12, daarna door naar Ronde 2"""
    g = session.get('game')
    if not g or g.get('round') != 1:
        return redirect(url_for('index'))
    
    # Rol 2d12 voor speler
    g['rolls'] = [random.randint(1, 12), random.randint(1, 12)]
    
    # Rol 2d12 voor Scar
    g['scar_rolls'] = [random.randint(1, 12), random.randint(1, 12)]
    
    player_total = sum(g['rolls'])
    scar_total = sum(g['scar_rolls'])
    
    # Check voor instant Whitejack (24)
    if player_total == 24:
        g['result'] = 'Whitejack! Win!'
        g['active'] = False
        g['game_over'] = True
    elif scar_total == 24:
        g['result'] = 'Lose (Scar Whitejack)'
        g['active'] = False
        g['game_over'] = True
    
    # Ga naar Ronde 2 (tenzij spel afgelopen)
    if not g['game_over']:
        g['round'] = 2
    
    session['game'] = g
    
    class Hand:
        pass
    hand = Hand()
    hand.__dict__.update(g)
    
    return render_template('game.html',
        hand=hand,
        scar={'rolls': g['scar_rolls']},
        player_total=player_total,
        scar_total=scar_total,
        round_no=2 if not g['game_over'] else 1,
        game_over=g['game_over']
    )
