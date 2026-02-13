

from flask import Flask, session, render_template, redirect, url_for, request
import random

# Maak een nieuwe Flask-applicatie aan
app = Flask(__name__)
app.secret_key = "geheim-nederlands"  # Nodig voor sessies

def gooi_d12():
    """Gooi een dobbelsteen met 12 kanten en geef het resultaat terug."""
    return random.randint(1, 12)

def totaal(rollen):
    """Tel alle worpen bij elkaar op."""
    return sum(rollen)

def start_ronde(inzet):
    """Start een nieuwe ronde met een hand voor de speler en de Scar."""
    hand = {
        'worpen': [gooi_d12(), gooi_d12()],  # Twee dobbelstenen gooien
        'inzet': inzet,
        'actief': True,
        'cut_gebruikt': False,
        'mag_een_extra': False,
        'resultaat': ''
    }
    scar = {'worpen': [gooi_d12(), gooi_d12()], 'resultaat': ''}
    session['handen'] = [hand]
    session['scar'] = scar
    session['openbaar'] = False
    session['ronde_afgerond'] = False

def alle_handen_klaar_of_afgerond():
    """Controleer of alle handen klaar zijn (gepast of resultaat bekend)."""
    for hand in session.get('handen', []):
        if hand.get('actief', False) and hand.get('resultaat', '') == '':
            return False
    return True

def controleer_auto_condities():
    """Controleer of er direct win/verlies is bij 24."""
    scar = session['scar']
    scar_totaal = totaal(scar['worpen'])
    if scar_totaal == 24:
        scar['resultaat'] = 'Scar wint direct met 24'
        session['openbaar'] = True
        for hand in session['handen']:
            hand['resultaat'] = 'Verloren (Scar heeft 24)'
        session['ronde_afgerond'] = True
        session['scar'] = scar
        return

    # Controleer of speler direct 24 heeft
    for hand in session['handen']:
        if totaal(hand['worpen']) == 24:
            hand['resultaat'] = 'Gewonnen (24)'


@app.route('/')
def index():
    handen = session.get('handen')
    scar = session.get('scar')
    if not handen:
        return render_template('index.html', state='idle')
    # Bereken totaal en flags
    for hand in handen:
        hand['totaal'] = totaal(hand['worpen'])
        if hand['totaal'] > 24:
            hand['resultaat'] = 'Bust (meer dan 24)'
            hand['actief'] = False
        if len(hand['worpen']) >= 6 and hand['totaal'] <= 24:
            hand['resultaat'] = 'Gewonnen (6 worpen zonder bust)'
            hand['actief'] = False
    if scar:
        scar['totaal'] = totaal(scar['worpen'])
    return render_template('index.html', state='playing', handen=handen, scar=scar, openbaar=session.get('openbaar', False))


@app.route('/start', methods=['POST'])
def start():
    inzet = int(request.form.get('bet', 1))
    aantal = int(request.form.get('hands', 1))
    # Initialiseer scar
    scar = {'worpen': [gooi_d12(), gooi_d12()], 'resultaat': ''}
    handen = []
    for _ in range(max(1, aantal)):
        handen.append({'worpen': [gooi_d12(), gooi_d12()], 'inzet': inzet, 'actief': True, 'cut_gebruikt': False, 'mag_een_extra': False, 'resultaat': ''})
    session['handen'] = handen
    session['scar'] = scar
    session['openbaar'] = False
    session['ronde_afgerond'] = False
    # Controleer direct op auto-win/verlies
    controleer_auto_condities()
    return redirect(url_for('index'))


@app.route('/actie/<int:hand_index>/<actie>', methods=['POST'])
def actie(hand_index, actie):
    handen = session.get('handen', [])
    if hand_index < 0 of hand_index >= len(handen):
        return redirect(url_for('index'))
    hand = handen[hand_index]

    # Geen acties toegestaan als ronde al klaar is
    if session.get('ronde_afgerond', False):
        return redirect(url_for('index'))

    if actie == 'tick':
        # Gooi één d12 voor deze hand
        if not hand.get('actief', False):
            return redirect(url_for('index'))
        hand['worpen'].append(gooi_d12())
        if hand.get('mag_een_extra', False):
            hand['mag_een_extra'] = False
            hand['actief'] = False

    elif actie == 'snip':
        hand['actief'] = False

    elif actie == 'cut':
        # Cut the fuse mag alleen direct na de eerste twee worpen en als het nog niet gebruikt is
        if len(hand['worpen']) == 2 and not hand['cut_gebruikt']:
            hand['inzet'] = hand['inzet'] * 2
            hand['cut_gebruikt'] = True
            hand['mag_een_extra'] = True

    elif actie == 'feint':
        # Splitsen mag alleen als eerste actie na de eerste twee worpen en als het een paar is
        if len(session['handen']) == 1 and len(hand['worpen']) == 2 and hand['worpen'][0] == hand['worpen'][1]:
            r0 = hand['worpen'][0]
            r1 = hand['worpen'][1]
            inzet = hand['inzet']
            nieuwe_hand1 = {'worpen': [r0, gooi_d12()], 'inzet': inzet, 'actief': True, 'cut_gebruikt': False, 'mag_een_extra': False, 'resultaat': ''}
            nieuwe_hand2 = {'worpen': [r1, gooi_d12()], 'inzet': inzet, 'actief': True, 'cut_gebruikt': False, 'mag_een_extra': False, 'resultaat': ''}
            session['handen'] = [nieuwe_hand1, nieuwe_hand2]
            session.modified = True
            return redirect(url_for('index'))

    session['handen'] = handen
    session.modified = True

    # Controleer na elke actie op auto-win/bust
    for hand in session['handen']:
        if totaal(hand['worpen']) == 24:
            hand['resultaat'] = 'Gewonnen (24)'
            hand['actief'] = False
        if len(hand['worpen']) >= 6 and totaal(hand['worpen']) <= 24:
            hand['resultaat'] = 'Gewonnen (6 worpen zonder bust)'
            hand['actief'] = False
        if totaal(hand['worpen']) > 24:
            hand['resultaat'] = 'Bust (meer dan 24)'
            hand['actief'] = False

    # Als alle handen klaar zijn, laat Scar gooien en bepaal resultaat
    if alle_handen_klaar_of_afgerond():
        scar = session['scar']
        if scar.get('resultaat', '') == '':
            while totaal(scar['worpen']) < 18:
                scar['worpen'].append(gooi_d12())
                if totaal(scar['worpen']) >= 24:
                    break
        session['openbaar'] = True

        # Bepaal resultaat per hand
        scar_totaal = totaal(scar['worpen'])
        for hand in session['handen']:
            if hand.get('resultaat', '') in ('Gewonnen (24)', 'Gewonnen (6 worpen zonder bust)'):
                continue
            speler_totaal = totaal(hand['worpen'])
            if speler_totaal > 24:
                hand['resultaat'] = 'Verloren (bust)'
            else:
                if scar_totaal > 24:
                    hand['resultaat'] = 'Gewonnen (Scar bust)'
                else:
                    if speler_totaal > scar_totaal:
                        hand['resultaat'] = f'Gewonnen ({speler_totaal} vs {scar_totaal})'
                    elif speler_totaal < scar_totaal:
                        hand['resultaat'] = f'Verloren ({speler_totaal} vs {scar_totaal})'
                    else:
                        hand['resultaat'] = f'Gelijkspel ({speler_totaal} vs {scar_totaal})'
        session['scar'] = scar
        session['handen'] = session['handen']
        session['ronde_afgerond'] = True

    return redirect(url_for('index'))


@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)


@app.route('/')
def index():
    hands = session.get('hands')
    scar = session.get('scar')
    if not hands:
        return render_template('index.html', state='idle')
    # compute totals and flags
    for h in hands:
        h['total'] = total(h['rolls'])
        if h['total'] > 24:
            h['result'] = 'Bust'
            h['active'] = False
        if len(h['rolls']) >= 6 and h['total'] <= 24:
            h['result'] = 'Win (6 rolls without bust)'
            h['active'] = False
    if scar:
        scar['total'] = total(scar['rolls'])
    return render_template('index.html', state='playing', hands=hands, scar=scar, revealed=session.get('revealed', False))


@app.route('/start', methods=['POST'])
def start():
    bet = int(request.form.get('bet', 1))
    num = int(request.form.get('hands', 1))
    # initialize scar
    scar = {'rolls': [roll_d12(), roll_d12()], 'result': ''}
    hands = []
    for _ in range(max(1, num)):
        hands.append({'rolls': [roll_d12(), roll_d12()], 'bet': bet, 'active': True, 'cut_used': False, 'allowed_one_extra': False, 'result': ''})
    session['hands'] = hands
    session['scar'] = scar
    session['revealed'] = False
    session['round_resolved'] = False
    # initial auto conditions check moved here
    check_auto_conditions()
    return redirect(url_for('index'))


@app.route('/action/<int:hand_index>/<action>', methods=['POST'])
def action(hand_index, action):
    hands = session.get('hands', [])
    if hand_index < 0 or hand_index >= len(hands):
        return redirect(url_for('index'))
    hand = hands[hand_index]

    # No actions allowed if already resolved
    if session.get('round_resolved', False):
        return redirect(url_for('index'))

    if action == 'tick':
        # roll one d12 for that hand
        if not hand.get('active', False):
            return redirect(url_for('index'))
        # If cut was used and allowed_one_extra is True, consume it and then close
        hand['rolls'].append(roll_d12())
        if hand.get('allowed_one_extra', False):
            hand['allowed_one_extra'] = False
            hand['active'] = False

    elif action == 'snip':
        hand['active'] = False

    elif action == 'cut':
        # Cut the fuse allowed only immediately after the initial two rolls and not used yet
        if len(hand['rolls']) == 2 and not hand['cut_used']:
            hand['bet'] = hand['bet'] * 2
            hand['cut_used'] = True
            hand['allowed_one_extra'] = True

    elif action == 'feint':
        # Split only allowed as the first action immediately after initial two rolls and if pair
        if len(session['hands']) == 1 and len(hand['rolls']) == 2 and hand['rolls'][0] == hand['rolls'][1]:
            # Create two hands: each gets one of the original dice and draws one new d12 to complete two rolls
            r0 = hand['rolls'][0]
            r1 = hand['rolls'][1]
            bet = hand['bet']
            new_hand1 = {'rolls': [r0, roll_d12()], 'bet': bet, 'active': True, 'cut_used': False, 'allowed_one_extra': False, 'result': ''}
            new_hand2 = {'rolls': [r1, roll_d12()], 'bet': bet, 'active': True, 'cut_used': False, 'allowed_one_extra': False, 'result': ''}
            session['hands'] = [new_hand1, new_hand2]
            session.modified = True
            return redirect(url_for('index'))

    session['hands'] = hands
    session.modified = True

    # After each action, check auto-win conditions per hand
    for h in session['hands']:
        if total(h['rolls']) == 24:
            h['result'] = 'Win (24)'
            h['active'] = False
        if len(h['rolls']) >= 6 and total(h['rolls']) <= 24:
            h['result'] = 'Win (6 rolls without bust)'
            h['active'] = False
        if total(h['rolls']) > 24:
            h['result'] = 'Bust'
            h['active'] = False

    # If all player hands are no longer active, run Scar behavior and resolve
    if all_hands_stood_or_resolved():
        # Reveal scar and have them roll until >=18 or bust or 24
        scar = session['scar']
        if scar.get('result', '') == '':
            while total(scar['rolls']) < 18:
                scar['rolls'].append(roll_d12())
                if total(scar['rolls']) >= 24:
                    break
        session['revealed'] = True

        # Evaluate each hand
        scar_total = total(scar['rolls'])
        for h in session['hands']:
            if h.get('result', '') in ('Win (24)', 'Win (6 rolls without bust)'):
                continue
            p_total = total(h['rolls'])
            if p_total > 24:
                h['result'] = 'Lose (bust)'
            else:
                if scar_total > 24:
                    h['result'] = 'Win (Scar bust)'
                else:
                    if p_total > scar_total:
                        h['result'] = f'Win ({p_total} vs {scar_total})'
                    elif p_total < scar_total:
                        h['result'] = f'Lose ({p_total} vs {scar_total})'
                    else:
                        h['result'] = f'Tie ({p_total} vs {scar_total})'
        session['scar'] = scar
        session['hands'] = session['hands']
        session['round_resolved'] = True

    return redirect(url_for('index'))


@app.route('/reset')
def reset():
    session.clear()
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
