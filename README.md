# WhiteJack

This Flask app implements the Whitejack dice game rules (d12-based) you described — a house called the Scar vs a player.

Rules implemented
- Round start: player places a bet and both player and Scar roll 2d12.
    - Round start: player places one or more bets (multiple hands). Each hand and the Scar roll 2d12.
- If Scar rolls 24 on initial roll, Scar immediately wins and all players lose.
- If a player rolls 24 on their hand, that hand immediately wins.
- Player actions per hand:
	- "Tick": roll another d12 and add to the total.
	- "Snip": stand (stop rolling) for that hand.
	- "Feint": if your initial two dice are a pair, you may split into two hands (each keeps one die and draws one more to complete two rolls).
	- "Cut the fuse": after initial two rolls, double the bet and gain exactly one extra tick (only available once per hand).
- Auto-win: if a hand reaches 6 dice without busting (>24), it wins automatically.
- Scar behavior: after player stands on all hands Scar rolls until their total is >= 18, or they hit 24, or bust.
- Result: each hand is compared against Scar's final total; busts lose, higher non-bust beats Scar, tie is reported as tie.

Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=app.py
flask run
```

Open http://127.0.0.1:5000 in your browser.

Notes for future features
- Payout calculation, player account/bankroll and multiple players
- Fancy UI and dice artwork
- Special behavior for particular dice values (like A/J/Q/K equivalents)
