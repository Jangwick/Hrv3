"""
Profile routes for the HR system.
Handles user profile management.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from models import EmployeeProfile, db
from forms import ProfileForm

profile_bp = Blueprint('profile', __name__)

def save_profile_image(form_picture, user_id, old_image=None):
    """Save profile picture to Cloudinary and return the upload result"""
    from cloud_config import upload_profile_image, delete_profile_image
    
    if not form_picture:
        return None

    # Generate a unique ID for the image
    from datetime import datetime
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    public_id = f"user_{user_id}_{timestamp}"

    # Delete old image if it exists and is not the default
    if old_image and old_image != 'default-profile':
        # This is where the deletion occurs - let's make sure it works properly
        success = delete_profile_image(old_image)
        if not success:
            current_app.logger.warning(f"Failed to delete old profile image: {old_image}")

    # Upload to Cloudinary
    return upload_profile_image(form_picture, public_id)

@profile_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def index():
    """User profile page and editing"""
    # Get or create user profile
    user_profile = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    if not user_profile:
        user_profile = EmployeeProfile(user_id=current_user.id)
        db.session.add(user_profile)
        db.session.commit()
        
    form = ProfileForm(obj=user_profile)
    if form.validate_on_submit():
        # Store form fields except profile_image in a dict
        # This avoids the AttributeError with the profile_image property
        form_data = {field.name: field.data for field in form if field.name != 'profile_image' and field.name != 'submit'}
        
        # Update user profile fields manually
        for field, value in form_data.items():
            setattr(user_profile, field, value)
        
        # Handle profile image if provided
        if form.profile_image.data:
            # Save the old image public_id for deletion after successful upload
            old_image = user_profile.cloudinary_public_id if user_profile.has_profile_image() else None
            
            # Upload to Cloudinary
            result = save_profile_image(form.profile_image.data, current_user.id, old_image)
            
            # Update the profile with Cloudinary data
            if result:
                user_profile.set_profile_image(result)
                current_app.logger.info(f"Profile image updated for user {current_user.id}, old image: {old_image}")
        
        db.session.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('profile.index'))
        
    return render_template('profile.html', form=form, user=current_user, profile=user_profile)
