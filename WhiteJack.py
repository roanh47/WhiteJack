# WhiteJack - Een dobbelspel gebaseerd op Blackjack maar met d12 dobbelstenen
# Doel: kom zo dicht mogelijk bij 24 zonder erover te gaan

from flask import Flask, render_template, session, redirect, url_for
from game_logic import Game

app = Flask(__name__)
app.secret_key = 'whitejack-secret-key'


@app.route('/')
def index():
    """Startpagina - hier plaats je je inzet"""
    return render_template('index.html')


@app.route('/reset')
def reset():
    """Reset het spel en ga terug naar start"""
    session.clear()
    return redirect(url_for('index'))


# Importeer en registreer de blueprint routes voor elke ronde
from Round1 import round1_bp
from Round2 import round2_bp
from Round3 import round3_bp

app.register_blueprint(round1_bp)
app.register_blueprint(round2_bp)
app.register_blueprint(round3_bp)

if __name__ == '__main__':
    app.run(debug=True)
