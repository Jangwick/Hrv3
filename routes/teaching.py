"""
Teaching unit routes for the HR system.
Handles teaching units, attendance tracking, and unit relationships.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from flask_login import login_required, current_user
from models import TeachingUnit, UnitAttendance, teaching_unit_relationships, User, db
from forms import TeachingUnitForm, AttendanceForm
from utils.decorators import hr_required
from datetime import datetime, timedelta
from sqlalchemy import func

teaching_bp = Blueprint('teaching', __name__)

@teaching_bp.route('/teaching-units')
@login_required
def index():
    """View teaching units - employees see their own, HR/admin see all"""
    if current_user.is_admin() or current_user.is_hr():
        # HR and admins can see all units
        active_units = TeachingUnit.query.filter_by(status='active').order_by(TeachingUnit.start_date.desc()).all()
        completed_units = TeachingUnit.query.filter_by(status='completed').order_by(TeachingUnit.end_date.desc()).limit(10).all()
    else:
        # Regular employees only see their own units
        active_units = TeachingUnit.query.filter_by(employee_id=current_user.id, status='active').order_by(TeachingUnit.start_date.desc()).all()
        completed_units = TeachingUnit.query.filter_by(employee_id=current_user.id, status='completed').order_by(TeachingUnit.end_date.desc()).all()
    
    return render_template('teaching/index.html',
                         active_units=active_units,
                         completed_units=completed_units)

@teaching_bp.route('/teaching-units/new', methods=['GET', 'POST'])
@login_required
@hr_required
def new():
    form = TeachingUnitForm()
    
    # Set choices for dropdown fields before validation
    form.employee_id.choices = [(u.id, u.get_display_name()) for u in User.query.all()]
    form.academic_term.choices = [
        ('Fall 2023', 'Fall 2023'),
        ('Spring 2024', 'Spring 2024'),
        ('Summer 2024', 'Summer 2024'),
        ('Fall 2024', 'Fall 2024')
    ]
    form.status.choices = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    
    if form.validate_on_submit():
        # Process the form data
        unit = TeachingUnit(
            title=form.title.data,
            code=form.code.data,
            employee_id=form.employee_id.data,
            academic_term=form.academic_term.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            hours_per_week=form.hours_per_week.data,
            unit_value=form.unit_value.data,
            rate_per_unit=form.rate_per_unit.data,
            status=form.status.data,
            created_by=current_user.id
        )
        
        db.session.add(unit)
        db.session.commit()
        
        flash('Teaching unit created successfully!', 'success')
        return redirect(url_for('teaching.index'))
    
    return render_template('teaching/new.html', form=form)

@teaching_bp.route('/teaching-units/<int:unit_id>')
@login_required
def view(unit_id):
    """View teaching unit details"""
    unit = TeachingUnit.query.get_or_404(unit_id)
    
    # Check if user has permission to view this unit
    if not (current_user.id == unit.employee_id or current_user.is_hr() or current_user.is_admin()):
        flash("You don't have permission to view this teaching unit", "danger")
        return redirect(url_for('dashboard.index'))
    
    # Get attendance records
    attendances = UnitAttendance.query.filter_by(teaching_unit_id=unit_id).order_by(UnitAttendance.date.desc()).all()
    
    return render_template('teaching/view.html', unit=unit, attendances=attendances, db=db, teaching_unit_relationships=teaching_unit_relationships)

@teaching_bp.route('/teaching-units/<int:unit_id>/edit', methods=['GET', 'POST'])
@login_required
@hr_required
def edit(unit_id):
    unit = TeachingUnit.query.get_or_404(unit_id)
    form = TeachingUnitForm(obj=unit)
    
    # Set choices for dropdown fields before validation
    form.employee_id.choices = [(u.id, u.get_display_name()) for u in User.query.all()]
    form.academic_term.choices = [
        ('Fall 2023', 'Fall 2023'),
        ('Spring 2024', 'Spring 2024'),
        ('Summer 2024', 'Summer 2024'),
        ('Fall 2024', 'Fall 2024')
    ]
    form.status.choices = [
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]
    
    if request.method == 'GET':
        form.employee_id.data = unit.employee_id
    
    if form.validate_on_submit():
        unit.employee_id = form.employee_id.data
        unit.title = form.title.data
        unit.code = form.code.data
        unit.hours_per_week = form.hours_per_week.data
        unit.unit_value = form.unit_value.data
        unit.rate_per_unit = form.rate_per_unit.data
        unit.start_date = form.start_date.data
        unit.end_date = form.end_date.data
        unit.academic_term = form.academic_term.data
        unit.status = form.status.data
        
        db.session.commit()
        
        flash('Teaching unit updated successfully!', 'success')
        return redirect(url_for('teaching.view', unit_id=unit.id))
    
    return render_template('teaching/edit.html', form=form, unit=unit)

@teaching_bp.route('/teaching-units/<int:unit_id>/attendance', methods=['GET', 'POST'])
@login_required
def record_attendance(unit_id):
    """Record attendance for a teaching unit"""
    # Get the teaching unit
    unit = TeachingUnit.query.get_or_404(unit_id)
    
    # Check if the user has permission to record attendance
    if not (current_user.is_hr() or current_user.is_admin() or current_user.id == unit.employee_id):
        abort(403)  # Forbidden
    
    form = AttendanceForm()
    
    if form.validate_on_submit():
        # Create attendance record
        attendance = UnitAttendance(
            teaching_unit_id=unit.id,
            date=form.date.data,
            status=form.status.data,
            hours=form.hours.data,
            notes=form.notes.data,
            recorded_by=current_user.id
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        flash(f"Attendance recorded successfully for {unit.title}", "success")
        return redirect(url_for('teaching.view', unit_id=unit.id))
    
    # Pass the datetime module to the template
    return render_template('teaching/attendance.html', unit=unit, form=form, datetime=datetime)

@teaching_bp.route('/teaching-units/<int:unit_id>/attendance/<int:attendance_id>/delete', methods=['POST'])
@login_required
def delete_attendance(unit_id, attendance_id):
    """Delete an attendance record"""
    attendance = UnitAttendance.query.get_or_404(attendance_id)
    unit = TeachingUnit.query.get_or_404(unit_id)
    
    # Check permissions
    if not (current_user.is_hr() or current_user.is_admin() or 
            (current_user.id == unit.employee_id and current_user.id == attendance.recorded_by)):
        flash("You don't have permission to delete this attendance record", "danger")
        return redirect(url_for('teaching.view', unit_id=unit_id))
    
    db.session.delete(attendance)
    db.session.commit()
    
    flash('Attendance record deleted!', 'success')
    return redirect(url_for('teaching.view', unit_id=unit_id))

@teaching_bp.route('/teaching-units/<int:unit_id>/link', methods=['GET', 'POST'])
@login_required
def link_unit(unit_id):
    """Link a teaching unit to another unit"""
    unit = TeachingUnit.query.get_or_404(unit_id)
    
    # Check if user has permission to edit this unit
    if not (current_user.is_admin() or current_user.is_hr() or unit.employee_id == current_user.id):
        flash('You do not have permission to link this teaching unit.', 'danger')
        return redirect(url_for('teaching.view', unit_id=unit_id))
    
    if request.method == 'POST':
        target_unit_id = request.form.get('target_unit_id', type=int)
        relationship_type = request.form.get('relationship_type', 'related')
        
        if target_unit_id:
            target_unit = TeachingUnit.query.get(target_unit_id)
            if target_unit and unit.link_unit(target_unit, relationship_type):
                db.session.commit()
                flash(f'Successfully linked to {target_unit.title}', 'success')
            else:
                flash('Failed to link teaching unit. It may already be linked.', 'warning')
        
        return redirect(url_for('teaching.view', unit_id=unit_id))
    
    # Get potential units to link to (exclude already linked units)
    linked_unit_ids = [u.id for u in unit.get_related_units()]
    available_units = TeachingUnit.query.filter(
        TeachingUnit.id != unit.id,
        ~TeachingUnit.id.in_(linked_unit_ids)
    ).all()
    
    return render_template(
        'teaching/link.html',
        unit=unit,
        available_units=available_units
    )

@teaching_bp.route('/teaching-units/<int:unit_id>/unlink/<int:target_id>', methods=['POST'])
@login_required
def unlink_unit(unit_id, target_id):
    """Unlink a teaching unit from another unit"""
    unit = TeachingUnit.query.get_or_404(unit_id)
    target_unit = TeachingUnit.query.get_or_404(target_id)
    
    # Check if user has permission to edit this unit
    if not (current_user.is_admin() or current_user.is_hr() or unit.employee_id == current_user.id):
        flash('You do not have permission to unlink this teaching unit.', 'danger')
        return redirect(url_for('teaching.view', unit_id=unit_id))
    
    if unit.unlink_unit(target_unit):
        db.session.commit()
        flash(f'Successfully unlinked from {target_unit.title}', 'success')
    else:
        flash('Failed to unlink teaching unit.', 'warning')
    
    return redirect(url_for('teaching.view', unit_id=unit_id))

def get_teaching_data_for_payroll(employee_id, start_date, end_date):
    """
    Get teaching unit data formatted for payroll calculations
    Returns teaching unit hours, rates, and total earnings
    """
    # Get active teaching units for this employee
    teaching_units = TeachingUnit.query.filter(
        TeachingUnit.employee_id == employee_id,
        TeachingUnit.status == 'active'
    ).all()
    
    # Get attendance for these units in the date range
    attendance_records = UnitAttendance.query.filter(
        UnitAttendance.teaching_unit_id.in_([unit.id for unit in teaching_units]),
        UnitAttendance.date.between(start_date, end_date)
    ).all()
    
    unit_data = []
    total_earnings = 0
    
    for unit in teaching_units:
        # Calculate hours taught in this period
        hours_taught = sum(
            record.hours for record in attendance_records 
            if record.teaching_unit_id == unit.id and record.status in ['present', 'late']
        )
        
        # Calculate earnings for this unit
        unit_earnings = hours_taught * unit.rate_per_unit
        total_earnings += unit_earnings
        
        unit_data.append({
            'id': unit.id,
            'title': unit.title,
            'code': unit.code,
            'hours_taught': hours_taught,
            'rate_per_unit': unit.rate_per_unit,
            'earnings': unit_earnings
        })
    
    return {
        'units': unit_data,
        'total_hours': sum(unit['hours_taught'] for unit in unit_data),
        'total_earnings': total_earnings
    }
