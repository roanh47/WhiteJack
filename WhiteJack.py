# WhiteJack - Een dobbelspel met gebruikersauthenticatie
# Doel: kom zo dicht mogelijk bij 24 zonder erover te gaan

from flask import Flask
from sqlalchemy import text
from extensions import db, login_manager
from blueprints.auth import auth_bp
from blueprints.game import game_bp
from blueprints.admin import admin_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'GeweldigeGokSite'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///whitejack.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

app.register_blueprint(auth_bp)
app.register_blueprint(game_bp)
app.register_blueprint(admin_bp)


# =============================================================================
# DATABASE AANMAKEN
# =============================================================================
with app.app_context():
    from models import User
    db.create_all()
    # Migratie: voeg wins/losses kolommen toe aan bestaande databases
    for kolom in ('wins', 'losses', 'is_admin'):
        try:
            db.session.execute(text(f'ALTER TABLE user ADD COLUMN {kolom} INTEGER DEFAULT 0'))
            db.session.commit()
        except Exception:
            db.session.rollback()
    # Zorg dat Roan admin is
    roan = User.query.filter_by(username='Roan').first()
    if roan and not roan.is_admin:
        roan.is_admin = 1
        db.session.commit()


if __name__ == '__main__':
    app.run(debug=True)
