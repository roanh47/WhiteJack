
# WhiteJack

Gehost op https://WhiteJack.pythonanywhere.com

Deze Flask-app implementeert het Whitejack dobbelspel (gebaseerd op d12) — een huis genaamd de Scar tegen een speler.

Regels geïmplementeerd
- Ronde start: speler plaatst een inzet en zowel de speler als de Scar gooien 2d12.
	- Ronde start: speler plaatst één of meer inzetten (meerdere handen). Elke hand en de Scar gooien 2d12.
- Als Scar 24 gooit bij de eerste worp, wint Scar direct en verliezen alle spelers.
- Als een speler 24 gooit met zijn hand, wint die hand direct.
- Spelersacties per hand:
	- "Tick": gooi nog een d12 en tel deze op bij het totaal.
	- "Snip": passen (stoppen met gooien) voor die hand.
	- "Feint": als je eerste twee dobbelstenen een paar zijn, mag je splitsen in twee handen (elke hand houdt één dobbelsteen en gooit er nog één bij).
	- "Cut the fuse": na de eerste twee worpen mag je de inzet verdubbelen en krijg je precies één extra tick (slechts één keer per hand mogelijk).
- Automatische winst: als een hand 6 dobbelstenen bereikt zonder te busten (>24), wint deze automatisch.
- Scar-gedrag: nadat de speler op alle handen heeft gepast, gooit Scar tot zijn totaal >= 18 is, of hij 24 gooit, of bust.
- Resultaat: elke hand wordt vergeleken met het eindtotaal van Scar; busts verliezen, hoger niet-bustend totaal wint van Scar, gelijkspel wordt als gelijkspel gemeld.

Snel starten

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=app.py
flask run
```

Open http://127.0.0.1:5000 in je browser.

Notities voor toekomstige functies
- Uitbetalingsberekening, spelersaccount/bank en meerdere spelers
- Mooie UI en dobbelsteenafbeeldingen
- Speciaal gedrag voor bepaalde dobbelsteenwaarden (zoals A/J/Q/K equivalenten)
