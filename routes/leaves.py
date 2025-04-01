"""
Leave request routes for the HR system.
Handles leave requests, approvals, and denials.
"""

from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from models import LeaveRequest, db
from forms import LeaveRequestForm, LeaveApprovalForm
from utils.decorators import hr_required
from datetime import datetime

leaves_bp = Blueprint('leaves', __name__)

@leaves_bp.route('/leaves')
@login_required
def index():
    """View leave requests - employees see their own, HR/admin see all"""
    if current_user.is_admin() or current_user.is_hr():
        # HR and admins see all pending requests
        pending_requests = LeaveRequest.query.filter_by(status='pending').order_by(LeaveRequest.start_date).all()
        # Also see recent approved/denied requests
        processed_requests = LeaveRequest.query.filter(
            LeaveRequest.status.in_(['approved', 'denied'])
        ).order_by(LeaveRequest.updated_at.desc()).limit(10).all()
    else:
        # Regular employees only see their own requests
        pending_requests = LeaveRequest.query.filter_by(
            employee_id=current_user.id, status='pending'
        ).order_by(LeaveRequest.start_date).all()
        processed_requests = LeaveRequest.query.filter(
            LeaveRequest.employee_id==current_user.id,
            LeaveRequest.status.in_(['approved', 'denied'])
        ).order_by(LeaveRequest.updated_at.desc()).all()
        
    return render_template('leaves/index.html', 
                          pending_requests=pending_requests, 
                          processed_requests=processed_requests)

@leaves_bp.route('/leaves/new', methods=['GET', 'POST'])
@login_required
def new():
    """Create a new leave request"""
    form = LeaveRequestForm()
    if form.validate_on_submit():
        leave_request = LeaveRequest(
            employee_id=current_user.id,
            leave_type=form.leave_type.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            reason=form.reason.data,
            status='pending'
        )
        db.session.add(leave_request)
        db.session.commit()
        flash('Your leave request has been submitted successfully!', 'success')
        return redirect(url_for('leaves.index'))
        
    return render_template('leaves/new.html', form=form)

@leaves_bp.route('/leaves/<int:leave_id>')
@login_required
def view(leave_id):
    """View details of a specific leave request"""
    leave = LeaveRequest.query.get_or_404(leave_id)
    
    # Check if user has permission to view this leave request
    if not (current_user.id == leave.employee_id or current_user.is_hr() or current_user.is_admin()):
        flash("You don't have permission to view this leave request", "danger")
        return redirect(url_for('dashboard.index'))
        
    return render_template('leaves/view.html', leave=leave)

@leaves_bp.route('/leaves/<int:leave_id>/process', methods=['GET', 'POST'])
@login_required
@hr_required
def process(leave_id):
    """Process (approve/deny) a leave request"""
    leave = LeaveRequest.query.get_or_404(leave_id)
    
    # Ensure the request is still pending
    if leave.status != 'pending':
        flash('This leave request has already been processed', 'warning')
        return redirect(url_for('leaves.view', leave_id=leave.id))
    
    form = LeaveApprovalForm()
    if form.validate_on_submit():
        leave.status = form.status.data
        leave.approval_comment = form.comment.data
        leave.approver_id = current_user.id
        leave.updated_at = datetime.utcnow()
        db.session.commit()
        
        status_text = 'approved' if leave.status == 'approved' else 'denied'
        flash(f'The leave request has been {status_text}', 'success')
        return redirect(url_for('leaves.index'))
        
    return render_template('leaves/process.html', form=form, leave=leave)
