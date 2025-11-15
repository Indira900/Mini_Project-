from flask import render_template, session, redirect, url_for, flash
from functools import wraps
from models import User

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Chore Companion route
# Note: 'app' is injected when this module is imported by main.py
def register_chore_routes(app):
    @app.route('/chore_companion')
    @login_required
    def chore_companion():
        user = User.query.get(session['user_id'])
        if user.user_type != 'patient':
            flash('Access denied.', 'error')
            return redirect(url_for('patient_dashboard'))
        
        # For now, just render a basic template
        return render_template('chore_companion.html', user=user)
