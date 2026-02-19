# Flask-functies voor routes, sessies en templates.
from flask import Flask, session, render_template, redirect, url_for, request
# random gebruiken we om d12-worpen te simuleren.
import random

# Flask-app initialiseren.
app = Flask(__name__)
# Secret key is nodig zodat Flask sessiegegevens veilig kan ondertekenen.
app.secret_key = "geheim-nederlands"


# Gooi 1 d12 en geef het resultaat (1 t/m 12) terug.
def roll_d12() -> int:
    return random.randint(1, 12)


# Bereken het totaal van een lijst worpen.
def total(rolls):
    return sum(rolls)


# Maak een nieuwe speler-hand met standaard startwaarden.
def hand_base(bet: int):
    return {
        # Startworp volgens regels: 2d12.
        "rolls": [roll_d12(), roll_d12()],
        # Inzet van deze hand.
        "bet": bet,
        # Of de hand nog acties mag doen.
        "active": True,
        # Of "cut the fuse" al gebruikt is op deze hand.
        "cut_used": False,
        # Als cut gebruikt is, moet de speler exact 1 keer tick doen.
        "must_tick_once": False,
        # Houdt bij of deze hand in de huidige ronde al actie deed.
        "acted_round": 0,
        # Eindstatus/resultaattekst van deze hand.
        "result": "",
    }


# Werk automatische hand-status bij (24, bust, of 6 worpen zonder bust).
def finalize_hand_state(hand):
    # Huidig totaal van de hand berekenen.
    t = total(hand["rolls"])

    # Exact 24 is directe winst.
    if t == 24 and not hand["result"]:
        hand["result"] = "Win (24)"
        hand["active"] = False
    # Boven 24 is bust en dus einde hand.
    elif t > 24 and not hand["result"]:
        hand["result"] = f"Bust ({t} > 24)"
        hand["active"] = False
    # 6 worpen zonder bust is automatische winst.
    elif len(hand["rolls"]) >= 6 and t <= 24 and not hand["result"]:
        hand["result"] = "Win (6 rolls without bust)"
        hand["active"] = False


# Controleer of alle actieve handen in deze ronde hun actie al gedaan hebben.
def all_player_actions_done_for_round(round_no: int):
    # Door alle spelershanden in de sessie lopen.
    for hand in session.get("hands", []):
        # Eerst altijd automatische status updaten.
        finalize_hand_state(hand)
        # Als hand nog actief is en nog niet handelde in deze ronde: niet klaar.
        if hand["active"] and hand["acted_round"] < round_no:
            return False
    # Anders zijn alle benodigde acties klaar.
    return True


# Verwerk het speciale geval: Scar heeft exact 24.
def resolve_if_scar_24():
    # Huidig Scar-totaal bepalen.
    scar_total = total(session["scar"]["rolls"])
    # Alleen iets doen als Scar echt 24 heeft.
    if scar_total != 24:
        return False

    # Scar-resultaat markeren.
    session["scar"]["result"] = "Scar hits 24"
    # Alle handen aflopen en verliezen behalve handen met eigen 24.
    for hand in session["hands"]:
        finalize_hand_state(hand)
        if hand["result"] != "Win (24)":
            hand["result"] = "Lose (Scar has 24)"
            hand["active"] = False
    # Ronde is definitief afgerond.
    session["round"] = 4
    session["round_resolved"] = True
    return True


# Ronde 2: Scar rolt precies 1 extra d12 (tenzij Scar al 24 had).
def run_round2_scar_roll():
    if total(session["scar"]["rolls"]) != 24:
        session["scar"]["rolls"].append(roll_d12())


# Ronde 3: Scar blijft rollen tot 18, 24 of bust.
def run_round3_scar_rolls():
    # Kortere variabele voor leesbaarheid.
    scar = session["scar"]
    # Doorrollen tot minimaal 18 bereikt is.
    while total(scar["rolls"]) < 18:
        scar["rolls"].append(roll_d12())
        # Stop direct bij 24 of hoger.
        if total(scar["rolls"]) >= 24:
            break


# Vergelijk alle handen met Scar en zet definitieve uitslag.
def resolve_final_results():
    # Scar-totaal eenmalig bepalen.
    scar_total = total(session["scar"]["rolls"])

    # Elke hand afzonderlijk beoordelen.
    for hand in session["hands"]:
        # Eerst automatische status nogmaals afdwingen.
        finalize_hand_state(hand)

        # Deze twee wincondities blijven altijd staan.
        if hand["result"] in ("Win (24)", "Win (6 rolls without bust)"):
            continue

        # Totaal speler voor vergelijking.
        player_total = total(hand["rolls"])

        # Uitkomstmatrix speler vs Scar.
        if player_total > 24:
            hand["result"] = "Lose (bust)"
        elif scar_total > 24:
            hand["result"] = "Win (Scar bust)"
        elif player_total > scar_total:
            hand["result"] = f"Win ({player_total} vs {scar_total})"
        elif player_total < scar_total:
            hand["result"] = f"Lose ({player_total} vs {scar_total})"
        else:
            hand["result"] = f"Tie ({player_total} vs {scar_total})"

        # Hand na eindvergelijking inactief zetten.
        hand["active"] = False

    # Hele partij afronden.
    session["round"] = 4
    session["round_resolved"] = True


# Hoofdroute: toont startscherm of actief spelbord.
@app.route("/")
def index():
    # Probeer handen uit sessie te lezen.
    hands = session.get("hands")

    # Geen actieve sessie -> startscherm.
    if not hands:
        return render_template("index.html", state="idle")

    # Scar uit sessie lezen met veilige fallback.
    scar = session.get("scar", {"rolls": [], "result": ""})

    # Totaal en automatische status per hand updaten voor de UI.
    for hand in hands:
        finalize_hand_state(hand)
        hand["total"] = total(hand["rolls"])

    # Scar totaal voor weergave.
    scar["total"] = total(scar["rolls"])

    # Speelscherm renderen met alle benodigde state.
    return render_template(
        "index.html",
        state="playing",
        hands=hands,
        scar=scar,
        round_no=session.get("round", 1),
        round_resolved=session.get("round_resolved", False),
    )


# Start een nieuwe partij.
@app.route("/start", methods=["POST"])
def start():
    # Ronde 1: inzetten plaatsen + initiële 2d12 voor speler(s) en Scar.

    # Bet en aantal handen uit formulier lezen met ondergrens 1.
    bet = max(1, int(request.form.get("bet", 1)))
    num_hands = max(1, int(request.form.get("hands", 1)))

    # Spelerhanden initialiseren.
    session["hands"] = [hand_base(bet) for _ in range(num_hands)]
    # Scar initialiseren met 2 startworpen.
    session["scar"] = {"rolls": [roll_d12(), roll_d12()], "result": ""}
    # Start in ronde 1.
    session["round"] = 1
    # Nog geen einduitslag.
    session["round_resolved"] = False

    # Eventuele auto-win/auto-bust direct op start toepassen.
    for hand in session["hands"]:
        finalize_hand_state(hand)

    # Speciale Scar-24 regel direct afhandelen.
    resolve_if_scar_24()
    # Markeer sessie als gewijzigd.
    session.modified = True
    # Terug naar hoofdpagina.
    return redirect(url_for("index"))


# Handmatige overgang van ronde 1 naar ronde 2.
@app.route("/next_round", methods=["POST"])
def next_round():
    # Ronde 2 start alleen vanuit ronde 1 en als spel niet al klaar is.
    if session.get("round", 1) != 1 or session.get("round_resolved", False):
        return redirect(url_for("index"))

    # Zet huidige ronde naar 2.
    session["round"] = 2
    session.modified = True
    return redirect(url_for("index"))


# Actions: tick, snip, feint, cut.
@app.route("/action/<int:hand_index>/<action>", methods=["POST"])
def action(hand_index: int, action: str):
    # Huidige handen en ronde uit sessie lezen.
    hands = session.get("hands", [])
    round_no = session.get("round", 1)

    # Blokkeer acties als spel voorbij is of ronde ongeldig.
    if session.get("round_resolved", False) or round_no not in (1, 2, 3):
        return redirect(url_for("index"))

    # Blokkeer ongeldige hand-index.
    if hand_index < 0 or hand_index >= len(hands):
        return redirect(url_for("index"))

    # Geselecteerde hand ophalen.
    hand = hands[hand_index]
    # Status updaten voordat actie verwerkt wordt.
    finalize_hand_state(hand)

    # Geen acties op inactieve/eindigde hand.
    if not hand["active"]:
        return redirect(url_for("index"))

    # Ronde 1: feint.
    if action == "feint" and round_no == 1:
        # Ronde 1 actie: feint alleen bij een openings-paar.
        if len(hand["rolls"]) == 2 and hand["rolls"][0] == hand["rolls"][1]:
            # Linker hand: eerste dobbelsteen + nieuwe d12.
            left = {
                "rolls": [hand["rolls"][0], roll_d12()],
                "bet": hand["bet"],
                "active": True,
                "cut_used": False,
                "must_tick_once": False,
                "acted_round": 0,
                "result": "",
            }
            # Rechter hand: tweede dobbelsteen + nieuwe d12.
            right = {
                "rolls": [hand["rolls"][1], roll_d12()],
                "bet": hand["bet"],
                "active": True,
                "cut_used": False,
                "must_tick_once": False,
                "acted_round": 0,
                "result": "",
            }
            # Vervang huidige hand door twee nieuwe handen.
            hands[hand_index : hand_index + 1] = [left, right]
            # Auto-status direct op beide nieuwe handen toepassen.
            for h in hands:
                finalize_hand_state(h)

        # Sessie opslaan en terug.
        session["hands"] = hands
        session.modified = True
        return redirect(url_for("index"))

    # Ronde 1: cut.
    if action == "cut" and round_no == 1:
        # Ronde 1 actie: cut the fuse verdubbelt inzet en geeft exact 1 extra tick.
        if len(hand["rolls"]) == 2 and not hand["cut_used"]:
            hand["bet"] *= 2
            hand["cut_used"] = True
            hand["must_tick_once"] = True

        # Sessie opslaan en terug.
        session["hands"] = hands
        session.modified = True
        return redirect(url_for("index"))

    # Alleen tick/snip toegestaan in ronde 2 of 3.
    if action not in ("tick", "snip") or round_no not in (2, 3):
        return redirect(url_for("index"))

    # Elke hand mag maar 1 actie per ronde doen.
    if hand["acted_round"] >= round_no:
        return redirect(url_for("index"))

    # Tick: gooi een extra d12.
    if action == "tick":
        hand["rolls"].append(roll_d12())
    # Snip: stoppen met deze hand, maar niet als cut nog verplichte tick verwacht.
    elif action == "snip" and not hand.get("must_tick_once", False):
        hand["active"] = False
    # Alles buiten bovenstaande is ongeldig.
    else:
        return redirect(url_for("index"))

    # Markeer dat de hand in deze ronde een actie deed.
    hand["acted_round"] = round_no

    # Als cut actief was: verplichte extra tick verbruikt en hand sluiten.
    if hand.get("must_tick_once", False):
        hand["must_tick_once"] = False
        hand["active"] = False

    # Auto-status bijwerken na actie.
    finalize_hand_state(hand)
    session["hands"] = hands

    # Als alle handen klaar zijn voor deze ronde, Scar-fase uitvoeren.
    if all_player_actions_done_for_round(round_no):
        # Einde ronde 2: Scar rolt 1 keer, dan eventueel door naar ronde 3.
        if round_no == 2:
            run_round2_scar_roll()
            if not resolve_if_scar_24():
                session["round"] = 3
        # Einde ronde 3: Scar speelt uit en eindresultaten worden gezet.
        elif round_no == 3:
            run_round3_scar_rolls()
            resolve_final_results()

    # Sessiewijzigingen bevestigen.
    session.modified = True
    return redirect(url_for("index"))


# Reset het spel volledig door sessie te wissen.
@app.route("/reset")
def reset():
    session.clear()
    return redirect(url_for("index"))


# Start lokale Flask-devserver als dit bestand direct wordt uitgevoerd.
if __name__ == "__main__":
    app.run(debug=True)
