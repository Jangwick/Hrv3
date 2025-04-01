"""
Routes initialization module.
"""
# Import all blueprints
from .auth import auth_bp
from .dashboard import dashboard_bp
from .admin import admin_bp
from .profile import profile_bp
from .employees import employees_bp
from .leaves import leaves_bp
from .trainings import trainings_bp
from .teaching import teaching_bp
from .attendance import attendance_bp
from .payroll import payroll_bp
from .reports import reports_bp
from .api import api_bp
from .hr import hr_bp

# Export all blueprints
__all__ = [
    'auth_bp', 
    'dashboard_bp', 
    'admin_bp', 
    'profile_bp',
    'employees_bp', 
    'leaves_bp', 
    'trainings_bp', 
    'teaching_bp',
    'attendance_bp', 
    'payroll_bp', 
    'reports_bp', 
    'api_bp',
    'hr_bp'
]

def register_routes(app):
    """Register all blueprint routes with the app"""
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(leaves_bp)
    app.register_blueprint(trainings_bp)
    app.register_blueprint(teaching_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(payroll_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(hr_bp, url_prefix='/hr')
    app.register_blueprint(auth_bp)
