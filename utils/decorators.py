"""
Utility decorators for the HR system.
This file defines decorators used across the application.
"""

from functools import wraps
from flask import redirect, url_for, flash, current_app
from flask_login import current_user

def admin_required(f):
    """Decorator to require admin role for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash("You don't have permission to access this page", "danger")
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

def hr_required(f):
    """Decorator to require HR or admin role for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or (not current_user.is_hr() and not current_user.is_admin()):
            flash("You don't have permission to access this page", "danger")
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

def hr_or_admin_required(f):
    """Decorator to restrict access to HR and Admin users"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return current_app.login_manager.unauthorized()
        
        if not (current_user.is_hr() or current_user.is_admin()):
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('dashboard.index'))
        
        return f(*args, **kwargs)
    return decorated_function
