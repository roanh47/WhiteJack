from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db, login_manager


class User(UserMixin, db.Model):
    """Gebruiker model - slaat username, wachtwoord en geld op"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    money = db.Column(db.Integer, default=100)  # Start met €100
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Integer, default=0)

    def set_password(self, password):
        """Hash het wachtwoord voor veilige opslag"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Controleer of het wachtwoord klopt"""
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    """Laad gebruiker op basis van ID (nodig voor Flask-Login)"""
    return User.query.get(int(user_id))
