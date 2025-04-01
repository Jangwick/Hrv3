"""
Admin routes for the HR system.
Handles administrator functionality.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import User, LoginAttempt, db
from functools import wraps
import sqlite3
from datetime import datetime

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Define admin_required locally to avoid circular imports
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash("You don't have permission to access this page", "danger")
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    users = User.query.all()
    return render_template('admin_dashboard.html', users=users)

@admin_bp.route('/login-attempts')
@login_required
@admin_required
def login_attempts():
    # Get all login attempts, ordered by most recent first
    attempts = LoginAttempt.query.order_by(LoginAttempt.timestamp.desc()).limit(100).all()
    return render_template('admin_login_attempts.html', attempts=attempts)

@admin_bp.route('/fix-database')
@login_required
@admin_required
def fix_database():
    """Fix database schema"""
    try:
        # Run the migration directly
        from migrations.add_created_at_to_payroll_deduction import run_migration
        success = run_migration()
        
        if success:
            flash('Successfully fixed the database schema!', 'success')
        else:
            flash('Database schema fix attempted but may not have been successful.', 'warning')
    except Exception as e:
        flash(f'Error fixing database: {str(e)}', 'danger')
        
    return redirect(url_for('admin.dashboard'))

@admin_bp.route('/migrate/payroll-deduction')
@login_required
@admin_required
def migrate_payroll_deduction():
    """Run migration to add created_at column to payroll_deduction table"""
    try:
        app = current_app._get_current_object()
        conn = sqlite3.connect(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
        cursor = conn.cursor()
        
        # Check if the column already exists
        cursor.execute("PRAGMA table_info(payroll_deduction)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'created_at' not in columns:
            cursor.execute("ALTER TABLE payroll_deduction ADD COLUMN created_at TIMESTAMP")
            
            # Update all existing rows to have the current timestamp
            now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(f"UPDATE payroll_deduction SET created_at = '{now}'")
            
            conn.commit()
            flash('Migration successful: Added created_at column to payroll_deduction table', 'success')
        else:
            flash('Column already exists in the database', 'info')
            
        conn.close()
        
    except Exception as e:
        flash(f'Migration error: {str(e)}', 'danger')
        
    return redirect(url_for('dashboard.index'))
