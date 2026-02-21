# WhiteJack - Een dobbelspel gebaseerd op Blackjack met d12
# Doel: kom zo dicht mogelijk bij 24 zonder erover te gaan

from flask import Flask, render_template, session, redirect, url_for, request
import random

app = Flask(__name__)
app.secret_key = 'whitejack-secret-key'


@app.route('/')
def index():
    """Start pagina"""
    return render_template('index.html')


@app.route('/game', methods=['GET', 'POST'])
def game():
    """
    Het hele spel op één pagina.
    We gebruiken 'ronde' om bij te houden waar we zijn:
    - ronde 1: Start, eerste tick (2d12)
    - ronde 2: Keuze uit tick/snip/cut (1 tick max)
    - ronde 3: Laatste kans, meerdere ticks mogelijk
    """
    
    if request.method == 'POST':
        actie = request.form.get('actie')
        spel = session.get('spel')
        
        if not spel:
            return redirect(url_for('index'))
        
        ronde = spel['ronde']
        
        # =====================================================================
        # RONDE 1: Eerste tick - beide rollen 2d12
        # =====================================================================
        if ronde == 1 and actie == 'tick':
            spel['rolls'] = [rol_d12(), rol_d12()]
            spel['scar_rolls'] = [rol_d12(), rol_d12()]
            
            # Check Whitejack (24)
            if sum(spel['rolls']) == 24:
                spel['resultaat'] = 'Whitejack! Je wint!'
                spel['game_over'] = True
            elif sum(spel['scar_rolls']) == 24:
                spel['resultaat'] = 'Scar heeft Whitejack!'
                spel['game_over'] = True
            else:
                # Door naar ronde 2
                spel['ronde'] = 2
        
        # =====================================================================
        # RONDE 2: Tick (1 keer), Snip, of Cut
        # =====================================================================
        elif ronde == 2:
            
            if actie == 'tick':
                # Slechts 1 tick in ronde 2
                spel['rolls'].append(rol_d12())
                # Scar rolt mee
                if sum(spel['scar_rolls']) != 24:
                    spel['scar_rolls'].append(rol_d12())
                    # Check of Scar bust
                    if sum(spel['scar_rolls']) > 24:
                        spel['resultaat'] = 'Scar bust! Je wint!'
                        spel['game_over'] = True
                
                # Check of speler bust
                if sum(spel['rolls']) > 24:
                    spel['resultaat'] = 'Bust!'
                    spel['game_over'] = True
                    scar_speelt_uit(spel)
                
                # Na tick: altijd door naar ronde 3 (tenzij game over)
                if not spel['game_over']:
                    spel['ronde'] = 3
            
            elif actie == 'cut':
                # Cut the fuse: bet x2, 1 roll, dan door
                spel['bet'] *= 2
                spel['cut_used'] = True
                spel['rolls'].append(rol_d12())
                
                # Scar rolt mee
                if sum(spel['scar_rolls']) != 24:
                    spel['scar_rolls'].append(rol_d12())
                    if sum(spel['scar_rolls']) > 24:
                        spel['resultaat'] = 'Scar bust! Je wint!'
                        spel['game_over'] = True
                
                # Na cut: door naar ronde 3
                if not spel['game_over']:
                    spel['ronde'] = 3
            
            elif actie == 'snip':
                # Geen rollen, direct door naar ronde 3
                spel['ronde'] = 3
        
        # =====================================================================
        # RONDE 3: Laatste ronde - tick of snip om te eindigen
        # =====================================================================
        elif ronde == 3:
            
            if actie == 'tick':
                spel['rolls'].append(rol_d12())
                
                # Check bust of 6 dice
                if sum(spel['rolls']) > 24:
                    spel['resultaat'] = 'Bust!'
                    spel['game_over'] = True
                elif len(spel['rolls']) >= 6:
                    spel['resultaat'] = '6 dice! Auto-win!'
                    spel['game_over'] = True
                
                # In ronde 3: na tick altijd eindigen
                if not spel['game_over']:
                    bepaal_winaar(spel)
                    spel['game_over'] = True
            
            elif actie == 'snip':
                # Eindig spel, bepaal winnaar
                bepaal_winaar(spel)
                spel['game_over'] = True
        
        session['spel'] = spel
    
    # Toon de game
    spel = session.get('spel')
    if not spel:
        return redirect(url_for('index'))
    
    return render_template('game.html',
        spel=spel,
        ronde=spel['ronde'],
        player_total=sum(spel['rolls']),
        scar_total=sum(spel['scar_rolls'])
    )


@app.route('/start', methods=['POST'])
def start():
    """Maak nieuw spel aan"""
    bet = int(request.form.get('bet', 1))
    
    session['spel'] = {
        'bet': bet,
        'rolls': [],
        'scar_rolls': [],
        'ronde': 1,        # We beginnen in ronde 1
        'cut_used': False,
        'resultaat': None,
        'game_over': False
    }
    
    return redirect(url_for('game'))


@app.route('/reset')
def reset():
    """Reset het spel"""
    session.pop('spel', None)
    return redirect(url_for('index'))


# =============================================================================
# HELPERS
# =============================================================================
def rol_d12():
    """Rol een d12 (1-12)"""
    return random.randint(1, 12)


def scar_speelt_uit(spel):
    """Scar rolt tot 18, 24, of bust"""
    scar = spel['scar_rolls']
    while sum(scar) < 18 and sum(scar) != 24:
        scar.append(rol_d12())
        if sum(scar) > 24:
            break
    spel['scar_rolls'] = scar


def bepaal_winaar(spel):
    """Bepaal wie wint"""
    speler = sum(spel['rolls'])
    scar = sum(spel['scar_rolls'])
    
    # Scar speelt uit als nodig
    if sum(spel['scar_rolls']) < 18 and sum(spel['scar_rolls']) != 24:
        scar_speelt_uit(spel)
        scar = sum(spel['scar_rolls'])
    
    if scar > 24:
        spel['resultaat'] = 'Je wint! Scar is bust.'
    elif speler > scar:
        spel['resultaat'] = 'Je wint!'
    elif speler < scar:
        spel['resultaat'] = 'Je verliest!'
    else:
        spel['resultaat'] = 'Gelijkspel!'


if __name__ == '__main__':
    app.run(debug=True)
