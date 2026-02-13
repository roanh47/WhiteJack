from flask import Flask, session, render_template, redirect, url_for, request
import random

app = Flask(__name__)
app.secret_key = "dev-secret-change-me"

def roll_d12():
    return random.randint(1, 12)


def total(rolls):
    return sum(rolls)


def init_round(bet):
    # Create player hands; default single hand. For multiple bets create multiple hands.
    hand = {
        'rolls': [roll_d12(), roll_d12()],
        'bet': bet,
        'active': True,
        'cut_used': False,
        'allowed_one_extra': False,
        'result': ''
    }
    scar = {'rolls': [roll_d12(), roll_d12()], 'result': ''}
    session['hands'] = [hand]
    session['scar'] = scar
    session['revealed'] = False
    session['round_resolved'] = False


def all_hands_stood_or_resolved():
    for h in session.get('hands', []):
        if h.get('active', False) and h.get('result', '') == '':
            return False
    return True


def check_auto_conditions():
    # Check immediate conditions: scar initial 24 makes scar win all
    scar = session['scar']
    scar_total = total(scar['rolls'])
    if scar_total == 24:
        scar['result'] = 'Scar auto-win with 24'
        session['revealed'] = True
        for h in session['hands']:
            h['result'] = 'Lose (Scar has 24)'
        session['round_resolved'] = True
        session['scar'] = scar
        return

    # Check player initial 24s
    for h in session['hands']:
        if total(h['rolls']) == 24:
            h['result'] = 'Win (24)'


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
