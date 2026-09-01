import uuid
from datetime import datetime, timedelta
from functools import wraps

from flask import Blueprint, request, redirect, url_for, render_template, flash, g, session

import config
from models.db import get_db, query_db
from models.user import authenticate

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if g.user is None:
            flash('Please log in.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if g.user is None:
                return redirect(url_for('auth.login'))
            if g.user['role'] not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated
    return decorator


@auth_bp.before_app_request
def load_user():
    g.user = None
    g.db = get_db()
    session_id = session.get('session_id')
    if session_id:
        sess = query_db(
            g.db,
            "SELECT * FROM sessions WHERE id = ? AND expires_at > datetime('now')",
            (session_id,),
            one=True,
        )
        if sess:
            g.user = query_db(g.db, "SELECT * FROM users WHERE id = ? AND is_active = 1", (sess['user_id'],), one=True)
        else:
            session.pop('session_id', None)


@auth_bp.teardown_app_request
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if g.user:
        return redirect(url_for('dashboard.index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        db = g.db
        user = authenticate(db, email, password)
        if user:
            session_id = str(uuid.uuid4())
            expires = datetime.utcnow() + timedelta(hours=config.SESSION_LIFETIME_HOURS)
            db.execute(
                "INSERT INTO sessions (id, user_id, expires_at) VALUES (?, ?, ?)",
                (session_id, user['id'], expires.isoformat()),
            )
            db.commit()
            session['session_id'] = session_id
            flash(f'Welcome, {user["name"]}.', 'success')
            return redirect(url_for('dashboard.index'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    session_id = session.pop('session_id', None)
    if session_id:
        g.db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        g.db.commit()
    flash('Logged out.', 'info')
    return redirect(url_for('auth.login'))
