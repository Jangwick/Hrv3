"""
Main application file for the HR System.
This file initializes the Flask application, configures it, and registers the routes.
"""

import os
from flask import Flask, render_template, send_from_directory, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user
from models import db, User
from argon2 import PasswordHasher
from functools import wraps
from flask_mail import Mail
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from flask_wtf.csrf import CSRFProtect
import sqlite3

# Import the register_routes function from routes module
from routes import register_routes

# Load environment variables
load_dotenv()

# Create the Flask application
def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)

    # Configure the application
    app.config['SECRET_KEY'] = os.urandom(24)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///school_hr.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Mail configuration
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = 'welptest12@gmail.com'  # Replace with your Gmail
    app.config['MAIL_PASSWORD'] = 'ylwz hhwq bvjz gpgb'  # Use App Password, not regular password
    app.config['MAIL_DEFAULT_SENDER'] = ('HR System', 'no-reply@gmail.com')

    # Configure upload folder
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit uploads to 16MB

    # Initialize extensions
    mail = Mail(app)

    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Initialize database
    db.init_app(app)

    # Initialize Argon2 password hasher
    ph = PasswordHasher()

    # Initialize CSRF protection
    csrf = CSRFProtect(app)

    # Helper context processor to make utility functions available in templates
    @app.context_processor
    def utility_processor():
        from cloud_config import get_optimized_url
        
        def get_profile_image_url(profile_image, width=300, height=300, version=None):
            # Handle the default case
            if not profile_image or profile_image == 'default-profile':
                return url_for('static', filename='img/default-profile.png')
            
            # Get optimized URL with version for cache busting if available
            return get_optimized_url(profile_image, width, height, version=version)
            
        # Add current date to context for templates
        now = datetime.now()
        
        return dict(get_profile_image_url=get_profile_image_url, now=now)

    # Ensure static files are served correctly
    @app.route('/static/<path:filename>')
    def static_files(filename):
        return send_from_directory(os.path.join(app.root_path, 'static'), filename)

    # Database migration route
    @app.route('/db/run-migrations')
    @login_required
    def run_db_migrations():
        """Run database migrations"""
        # Import admin_required from utils for this specific route
        from utils.decorators import admin_required
        
        @admin_required
        def protected_migration():
            try:
                from migrations.add_created_at_to_payroll_deduction import run_migration
                run_migration()
                flash('Database migrations executed successfully!', 'success')
            except Exception as e:
                flash(f'Error running migrations: {str(e)}', 'danger')
            
            return redirect(url_for('dashboard.index'))
        
        return protected_migration()

    # Register routes
    register_routes(app)

    return app

# Create database tables
def init_db():
    with app.app_context():
        db.create_all()

# Run the application
if __name__ == '__main__':
    # Create utils directory if it doesn't exist
    os.makedirs('utils', exist_ok=True)
    
    # Initialize the Flask application
    app = create_app()
    
    # Initialize the database
    init_db()
    
    # Run the app
    app.run(debug=True)
else:
    # Create utils directory if it doesn't exist
    os.makedirs('utils', exist_ok=True)
    
    # Initialize the Flask application
    app = create_app()
    
    # Initialize the database
    init_db()
