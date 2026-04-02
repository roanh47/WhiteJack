from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from models import User
from extensions import db

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Geen toegang.', 'error')
            return redirect(url_for('game.lobby'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/admin')
@login_required
@admin_required
def admin():
    users = User.query.order_by(User.username).all()
    return render_template('admin.html', users=users)


@admin_bp.route('/admin/create', methods=['POST'])
@login_required
@admin_required
def admin_create():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    money = int(request.form.get('money', 100))
    if not username or not password:
        flash('Gebruikersnaam en wachtwoord zijn verplicht.', 'error')
        return redirect(url_for('admin.admin'))
    if User.query.filter_by(username=username).first():
        flash(f'"{username}" bestaat al.', 'error')
        return redirect(url_for('admin.admin'))
    user = User(username=username, money=money)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    flash(f'Gebruiker "{username}" aangemaakt.', 'success')
    return redirect(url_for('admin.admin'))


@admin_bp.route('/admin/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_delete(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Je kunt jezelf niet verwijderen.', 'error')
        return redirect(url_for('admin.admin'))
    db.session.delete(user)
    db.session.commit()
    flash(f'Gebruiker "{user.username}" verwijderd.', 'success')
    return redirect(url_for('admin.admin'))


@admin_bp.route('/admin/set-money/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_set_money(user_id):
    user = User.query.get_or_404(user_id)
    amount = int(request.form.get('amount', 0))
    user.money = amount
    db.session.commit()
    flash(f'Geld van "{user.username}" ingesteld op €{amount}.', 'success')
    return redirect(url_for('admin.admin'))


@admin_bp.route('/admin/reset-password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_reset_password(user_id):
    user = User.query.get_or_404(user_id)
    new_password = request.form.get('password', '').strip()
    if not new_password:
        flash('Nieuw wachtwoord is verplicht.', 'error')
        return redirect(url_for('admin.admin'))
    user.set_password(new_password)
    db.session.commit()
    flash(f'Wachtwoord van "{user.username}" gereset.', 'success')
    return redirect(url_for('admin.admin'))


@admin_bp.route('/admin/toggle-admin/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Je kunt je eigen admin-status niet wijzigen.', 'error')
        return redirect(url_for('admin.admin'))
    user.is_admin = 0 if user.is_admin else 1
    db.session.commit()
    status = 'admin' if user.is_admin else 'geen admin'
    flash(f'"{user.username}" is nu {status}.', 'success')
    return redirect(url_for('admin.admin'))


@admin_bp.route('/admin/reset-stats/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_reset_stats(user_id):
    user = User.query.get_or_404(user_id)
    user.wins = 0
    user.losses = 0
    db.session.commit()
    flash(f'Stats van "{user.username}" gereset.', 'success')
    return redirect(url_for('admin.admin'))
