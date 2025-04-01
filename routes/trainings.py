"""
Training program routes for the HR system.
Handles training program management, enrollments, and feedback.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import TrainingProgram, TrainingEnrollment, User, db
from forms import TrainingProgramForm, EnrollmentForm, TrainingFeedbackForm
from utils.decorators import hr_required
from datetime import datetime

trainings_bp = Blueprint('trainings', __name__)

@trainings_bp.route('/trainings')
@login_required
def index():
    """View all training programs"""
    # Get upcoming and in-progress trainings
    active_trainings = TrainingProgram.query.filter(
        TrainingProgram.status.in_(['upcoming', 'in-progress'])
    ).order_by(TrainingProgram.start_date).all()
    
    # Get completed trainings
    completed_trainings = TrainingProgram.query.filter_by(
        status='completed'
    ).order_by(TrainingProgram.end_date.desc()).limit(5).all()
    
    # Check if the user is already enrolled in each training
    user_enrollments = {
        e.training_id: e for e in TrainingEnrollment.query.filter_by(employee_id=current_user.id).all()
    }
    
    return render_template('trainings/index.html', 
                          active_trainings=active_trainings,
                          completed_trainings=completed_trainings,
                          user_enrollments=user_enrollments)

@trainings_bp.route('/trainings/new', methods=['GET', 'POST'])
@login_required
@hr_required
def new():
    """Create a new training program"""
    form = TrainingProgramForm()
    if form.validate_on_submit():
        training = TrainingProgram(
            title=form.title.data,
            description=form.description.data,
            instructor=form.instructor.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            location=form.location.data,
            max_participants=form.max_participants.data,
            category=form.category.data,
            status=form.status.data,
            created_by=current_user.id
        )
        db.session.add(training)
        db.session.commit()
        flash('Training program created successfully!', 'success')
        return redirect(url_for('trainings.index'))
        
    return render_template('trainings/new.html', form=form)

@trainings_bp.route('/trainings/<int:training_id>')
@login_required
def view(training_id):
    """View a specific training program"""
    training = TrainingProgram.query.get_or_404(training_id)
    
    # Check if the current user is enrolled
    enrollment = TrainingEnrollment.query.filter_by(
        training_id=training_id, employee_id=current_user.id
    ).first()
    
    # Get list of enrolled employees for HR/admin
    enrolled_employees = []
    if current_user.is_hr() or current_user.is_admin():
        enrolled_employees = db.session.query(User, TrainingEnrollment)\
            .join(TrainingEnrollment, User.id == TrainingEnrollment.employee_id)\
            .filter(TrainingEnrollment.training_id == training_id)\
            .all()
    
    return render_template('trainings/view.html', 
                          training=training, 
                          enrollment=enrollment,
                          enrolled_employees=enrolled_employees)

@trainings_bp.route('/trainings/<int:training_id>/edit', methods=['GET', 'POST'])
@login_required
@hr_required
def edit(training_id):
    """Edit a training program"""
    training = TrainingProgram.query.get_or_404(training_id)
    form = TrainingProgramForm(obj=training)
    if form.validate_on_submit():
        form.populate_obj(training)
        db.session.commit()
        flash('Training program updated successfully!', 'success')
        return redirect(url_for('trainings.view', training_id=training.id))
        
    return render_template('trainings/edit.html', form=form, training=training)

@trainings_bp.route('/trainings/<int:training_id>/enroll', methods=['GET', 'POST'])
@login_required
def enroll(training_id):
    """Enroll in a training program"""
    training = TrainingProgram.query.get_or_404(training_id)
    
    # Check if enrollment is still possible
    if training.status not in ['upcoming', 'in-progress']:
        flash('Enrollment is not available for this training.', 'warning')
        return redirect(url_for('trainings.view', training_id=training_id))
    
    # Check if training is full
    if training.is_full:
        flash('This training is at maximum capacity.', 'warning')
        return redirect(url_for('trainings.view', training_id=training_id))
    
    # HR or Admin can enroll multiple employees
    if current_user.is_hr() or current_user.is_admin():
        form = EnrollmentForm()
        
        # Get employees who aren't already enrolled
        enrolled_ids = [e.employee_id for e in TrainingEnrollment.query.filter_by(training_id=training_id).all()]
        available_employees = User.query.filter(User.id.notin_(enrolled_ids) if enrolled_ids else True).all()
        
        form.employees.choices = [(e.id, e.get_display_name() or e.username) for e in available_employees]
        
        if form.validate_on_submit():
            for employee_id in form.employees.data:
                enrollment = TrainingEnrollment(
                    training_id=training_id,
                    employee_id=employee_id
                )
                db.session.add(enrollment)
            
            db.session.commit()
            flash(f'Successfully enrolled {len(form.employees.data)} employees!', 'success')
            return redirect(url_for('trainings.view', training_id=training_id))
            
        return render_template('trainings/enroll.html', form=form, training=training)
    else:
        # Regular employees can only enroll themselves
        # Check if already enrolled
        existing_enrollment = TrainingEnrollment.query.filter_by(
            training_id=training_id, employee_id=current_user.id
        ).first()
        
        if existing_enrollment:
            flash('You are already enrolled in this training.', 'info')
            return redirect(url_for('trainings.view', training_id=training_id))
            
        # Create new enrollment
        enrollment = TrainingEnrollment(
            training_id=training_id,
            employee_id=current_user.id
        )
        db.session.add(enrollment)
        db.session.commit()
        
        flash('You have successfully enrolled in this training!', 'success')
        return redirect(url_for('trainings.view', training_id=training_id))

@trainings_bp.route('/trainings/<int:training_id>/unenroll/<int:employee_id>', methods=['POST'])
@login_required
def unenroll(training_id, employee_id):
    """Unenroll from a training program"""
    # Check if user has permission (self or HR/admin)
    if employee_id != current_user.id and not (current_user.is_hr() or current_user.is_admin()):
        flash("You don't have permission to unenroll other employees.", "danger")
        return redirect(url_for('trainings.view', training_id=training_id))
    
    enrollment = TrainingEnrollment.query.filter_by(
        training_id=training_id, employee_id=employee_id
    ).first_or_404()
    
    db.session.delete(enrollment)
    db.session.commit()
    
    if employee_id == current_user.id:
        flash('You have been unenrolled from this training.', 'success')
    else:
        employee = User.query.get(employee_id)
        flash(f'{employee.username} has been unenrolled from this training.', 'success')
        
    return redirect(url_for('trainings.view', training_id=training_id))

@trainings_bp.route('/trainings/my-enrollments')
@login_required
def my_enrollments():
    """View my training enrollments"""
    # Get active enrollments (upcoming and in-progress)
    active_enrollments = db.session.query(TrainingEnrollment)\
        .join(TrainingProgram, TrainingEnrollment.training_id == TrainingProgram.id)\
        .filter(TrainingEnrollment.employee_id == current_user.id,
                TrainingProgram.status.in_(['upcoming', 'in-progress']))\
        .order_by(TrainingProgram.start_date).all()
    
    # Get completed enrollments
    completed_enrollments = db.session.query(TrainingEnrollment)\
        .join(TrainingProgram, TrainingEnrollment.training_id == TrainingProgram.id)\
        .filter(TrainingEnrollment.employee_id == current_user.id,
                TrainingProgram.status == 'completed')\
        .order_by(TrainingProgram.end_date.desc()).all()
        
    return render_template('trainings/my_enrollments.html',
                          active_enrollments=active_enrollments,
                          completed_enrollments=completed_enrollments)

@trainings_bp.route('/trainings/<int:training_id>/feedback', methods=['GET', 'POST'])
@login_required
def feedback(training_id):
    """Submit feedback for a completed training"""
    training = TrainingProgram.query.get_or_404(training_id)
    
    # Check if the user is enrolled
    enrollment = TrainingEnrollment.query.filter_by(
        training_id=training_id, employee_id=current_user.id
    ).first_or_404()
    
    # Check if training is completed
    if training.status != 'completed':
        flash('Feedback can only be submitted for completed trainings.', 'warning')
        return redirect(url_for('trainings.view', training_id=training_id))
        
    # Check if feedback already submitted
    if enrollment.status == 'completed':
        flash('You have already submitted feedback for this training.', 'info')
        return redirect(url_for('trainings.view', training_id=training_id))
    
    form = TrainingFeedbackForm()
    
    if form.validate_on_submit():
        enrollment.rating = form.rating.data
        enrollment.feedback = form.feedback.data
        enrollment.status = 'completed'
        enrollment.feedback_date = datetime.utcnow()
        
        db.session.commit()
        
        flash('Thank you for your feedback!', 'success')
        return redirect(url_for('trainings.view', training_id=training_id))
        
    return render_template('trainings/feedback.html', form=form, training=training)
