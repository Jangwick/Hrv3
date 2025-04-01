"""
HR routes for the HR system.
Handles HR dashboard and HR-specific functionality.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from utils.decorators import hr_or_admin_required
from models import User, EmployeeProfile, db

# Define the blueprint with the correct name
hr_bp = Blueprint('hr', __name__)

@hr_bp.route('/dashboard')
@login_required
@hr_or_admin_required
def dashboard():
    """Display HR dashboard with employee management options"""
    # Get all users for directory
    users = User.query.all()
    
    # Explicitly render hr_dashboard.html
    return render_template('hr_dashboard.html', users=users)
