"""
Authentication routes for the HR system.
Handles login, logout, signup, and password reset functionality.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from models import User, LoginAttempt, db
from forms import LoginForm, SignupForm, RequestResetForm, ResetPasswordForm
from datetime import datetime
from flask_mail import Message

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        # Handle login form submission
        username_or_email = form.username_or_email.data
        user = User.authenticate(username_or_email, form.password.data)
        
        if user:
            # Successful login - reset login attempts
            LoginAttempt.log_attempt(request.remote_addr, username_or_email, success=True, user_agent=request.user_agent.string)
            LoginAttempt.reset_for_ip(request.remote_addr)
            
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            
            # Log the successful login
            current_app.logger.info(f"Successful login for user {user.username} from IP {request.remote_addr}")
            
            return redirect(next_page or url_for('dashboard.index'))
        else:
            # Failed login - record the attempt
            LoginAttempt.log_attempt(request.remote_addr, username_or_email, success=False, user_agent=request.user_agent.string)
            
            # Get updated count for display
            is_limited, limit_message, attempts_left = LoginAttempt.is_rate_limited(request.remote_addr)
            
            if attempts_left <= 0:
                flash('Too many failed login attempts. Your account has been temporarily locked.', 'danger')
            else:
                flash(f'Invalid username/email or password. You have {attempts_left} attempts remaining.', 'danger')
            
            # Log the failed attempt
            current_app.logger.warning(f"Failed login attempt for {username_or_email} from IP {request.remote_addr}")
                
    return render_template('login.html', form=form, attempts=5-attempts_left if 'attempts_left' in locals() else 0)

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    
    # Check if admin exists to modify form choices
    admin_exists = User.query.filter_by(role='admin').first() is not None
    
    form = SignupForm()
    # Modify role choices if admin already exists
    if admin_exists:
        form.role.choices = [
            ('employee', 'Employee'),
            ('hr', 'HR')
        ]
    
    if form.validate_on_submit():
        # Check if user already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('Email already registered', 'danger')
            return render_template('signup.html', form=form, admin_exists=admin_exists)
        
        # Check if username already exists
        existing_username = User.query.filter_by(username=form.username.data).first()
        if existing_username:
            flash('Username already taken', 'danger')
            return render_template('signup.html', form=form, admin_exists=admin_exists)
        
        # Check if the first user is being created
        is_first_user = User.query.count() == 0
        
        # Determine appropriate role
        role = form.role.data
        
        # If not the first user and trying to register as admin without being an admin
        if not is_first_user and role == 'admin' and not current_user.is_authenticated:
            flash('Admin role requires authorization. Your account has been created with Employee role.', 'warning')
            role = 'employee'
        elif not is_first_user and role == 'hr' and not current_user.is_authenticated:
            flash('HR role requires authorization. Your account has been created with Employee role.', 'warning')
            role = 'employee'
        
        # Create new user
        new_user = User(
            username=form.username.data,
            email=form.email.data,
            department=form.department.data,
            role=role  # Use the determined role
        )
        new_user.set_password(form.password.data)
        
        # Save user to database
        db.session.add(new_user)
        db.session.commit()
        
        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('signup.html', form=form, admin_exists=admin_exists)

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('dashboard.landing'))

def send_reset_email(user):
    from flask import current_app
    token = user.get_reset_token()
    mail = current_app.extensions['mail']
    msg = Message('Password Reset Request',
                  recipients=[user.email])
    
    # Plain text version for email clients that don't support HTML
    msg.body = f'''To reset your password, visit the following link:
{url_for('auth.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    
    # HTML version with styling that matches your website
    reset_link = url_for('auth.reset_token', token=token, _external=True)
    msg.html = f'''
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #333;
                line-height: 1.6;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .card {{
                border-radius: 8px;
                overflow: hidden;
                border: 1px solid #ddd;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            }}
            .card-header {{
                background-color: #0d6efd;
                color: white;
                padding: 16px;
                text-align: center;
            }}
            .card-body {{
                padding: 20px;
                background-color: #fff;
            }}
             .btn {{
                display: inline-block;
                background-color: #0066cc; 
                color: #ffffff !important;
                text-decoration: none;
                padding: 12px 30px;
                border-radius: 4px;
                text-align: center;
                font-weight: bold;
                margin: 20px 0;
                font-size: 16px;
                letter-spacing: 0.5px;
                text-shadow: 0px 1px 1px rgba(0,0,0,0.2);
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .text-muted {{
                color: #6c757d;
                font-size: 0.9em;
            }}
            .text-center {{
                text-align: center;
            }}
            .footer {{
                text-align: center;
                margin-top: 20px;
                color: #6c757d;
                font-size: 0.85em;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="card">
                <div class="card-header">
                    <h2 style="margin: 0;">Password Reset Request</h2>
                </div>
                <div class="card-body">
                    <h3>Hello!</h3>
                    <p>You are receiving this email because a password reset request was made for your account.</p>
                    <p>Please click the button below to reset your password:</p>
                    
                    <div class="text-center">
                        <a href="{reset_link}" class="btn">Reset Your Password</a>
                    </div>
                    
                    <p>If the button doesn't work, copy and paste the following link into your browser:</p>
                    <p><a href="{reset_link}">{reset_link}</a></p>
                    
                    <p class="text-muted">If you didn't request a password reset, please ignore this email and no changes will be made to your account.</p>
                </div>
            </div>
            <div class="footer">
                <p>© {datetime.now().year} HR Management System</p>
                <p>This is an automated message, please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    mail.send(msg)

@auth_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('auth.login'))
    return render_template('reset_request.html', form=form)

@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('auth.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('auth.login'))
    return render_template('reset_token.html', form=form)
