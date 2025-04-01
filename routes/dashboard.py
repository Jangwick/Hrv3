"""
Dashboard routes for the HR system.
Handles the main dashboard view for users.
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from models import EmployeeProfile, TeachingUnit, UnitAttendance, LeaveRequest, TrainingEnrollment, TrainingProgram, Payroll, db
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def index():
    """View teaching units - employees see their own, HR/admin see all"""
    # Get the current user's profile
    profile = EmployeeProfile.query.filter_by(user_id=current_user.id).first()
    
    # If no profile exists yet, create a default one
    if not profile:
        profile = EmployeeProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    
    # Get attendance statistics for this user
    teaching_units = TeachingUnit.query.filter_by(
        employee_id=current_user.id, 
        status='active'
    ).all()
    
    # Calculate attendance rate across all units
    attendance_stats = {'rate': 0}
    if teaching_units:
        total_rate = sum(unit.attendance_rate for unit in teaching_units)
        attendance_stats['rate'] = round(total_rate / len(teaching_units), 1)
    
    # Get leave statistics
    leave_stats = {
        'pending': LeaveRequest.query.filter_by(
            employee_id=current_user.id, 
            status='pending'
        ).count(),
        'approved': LeaveRequest.query.filter_by(
            employee_id=current_user.id, 
            status='approved'
        ).count()
    }
    
    # Get training statistics
    training_stats = {
        'upcoming': TrainingEnrollment.query.filter_by(
            employee_id=current_user.id, 
            status='enrolled'
        ).join(TrainingEnrollment.training).filter(
            TrainingProgram.status == 'upcoming'
        ).count(),
        'active': TrainingEnrollment.query.filter_by(
            employee_id=current_user.id
        ).join(TrainingEnrollment.training).filter(
            TrainingProgram.status == 'in-progress'
        ).count()
    }
    
    # Get teaching statistics
    teaching_stats = {
        'active': TeachingUnit.query.filter_by(
            employee_id=current_user.id,
            status='active'
        ).count()
    }
    
    # Get recent activities - more comprehensive data collection
    recent_activities = []
    
    # Add login activity as the first item
    login_activity = {
        'title': 'Logged in successfully',
        'description': 'Welcome to your dashboard',
        'time': datetime.now().strftime('%b %d, %Y'),
        'icon': 'fa-sign-in-alt',
        'icon_class': 'bg-primary'
    }
    recent_activities.append(login_activity)
    
    # Add recent attendance records with more details
    recent_attendances = UnitAttendance.query.join(
        TeachingUnit, UnitAttendance.teaching_unit_id == TeachingUnit.id
    ).filter(
        TeachingUnit.employee_id == current_user.id
    ).order_by(UnitAttendance.date.desc()).limit(3).all()
    
    for attendance in recent_attendances:
        # Determine appropriate icon and class based on status
        if attendance.status == 'present':
            icon_class = 'bg-success'
            icon = 'fa-check-circle'
        elif attendance.status == 'absent':
            icon_class = 'bg-danger'
            icon = 'fa-times-circle'
        elif attendance.status == 'late':
            icon_class = 'bg-warning'
            icon = 'fa-clock'
        else:
            icon_class = 'bg-info'
            icon = 'fa-info-circle'
        
        # Format time to be more readable
        formatted_time = attendance.date.strftime('%b %d, %Y')
        
        # Add detailed description
        description = f"{attendance.status.capitalize()} - {attendance.hours} hours"
        if attendance.notes:
            description += f" - {attendance.notes}"
        
        recent_activities.append({
            'title': f"Attendance: {attendance.teaching_unit.title}",
            'description': description,
            'time': formatted_time,
            'icon': icon,
            'icon_class': icon_class
        })
    
    # Add recent leave requests with improved details
    recent_leaves = LeaveRequest.query.filter_by(
        employee_id=current_user.id
    ).order_by(LeaveRequest.created_at.desc()).limit(3).all()
    
    for leave in recent_leaves:
        # Customize icon and class based on leave status
        if leave.status == 'approved':
            icon_class = 'bg-success'
            icon = 'fa-check-circle'
        elif leave.status == 'denied':
            icon_class = 'bg-danger'
            icon = 'fa-times-circle'
        elif leave.status == 'pending':
            icon_class = 'bg-warning'
            icon = 'fa-hourglass-half'
        else:
            icon_class = 'bg-info'
            icon = 'fa-calendar-alt'
            
        # Format date range
        date_range = f"{leave.start_date.strftime('%b %d')} to {leave.end_date.strftime('%b %d, %Y')}"
        
        # Create descriptive title and description
        title = f"Leave Request: {leave.leave_type.replace('_', ' ').title()}"
        description = f"Status: {leave.status.title()} - {date_range}"
        
        recent_activities.append({
            'title': title,
            'description': description,
            'time': leave.created_at.strftime('%b %d, %Y'),
            'icon': icon,
            'icon_class': icon_class
        })
    
    # Add recent training enrollments and payroll information...
    # ...existing code...
    
    # Sort activities by time (most recent first)
    # Ensure all activities have a parseable time string first
    for activity in recent_activities:
        if 'time' not in activity or not activity['time'] or activity['time'] == 'N/A':
            activity['time'] = datetime.now().strftime('%b %d, %Y')
    
    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, '%b %d, %Y %H:%M')
        except ValueError:
            return datetime.strptime(date_str, '%b %d, %Y')

    recent_activities.sort(key=lambda x: parse_date(x['time']), reverse=True)
    
    # Limit to most recent 5 activities
    recent_activities = recent_activities[:5]
    
    # Get attendance data for the chart - use real data
    chart_data = {
        'labels': [],
        'attendance_rates': []
    }
    
    # Get attendance records for the last 7 days
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=6)  # Last 7 days including today
    
    # Generate date range for last 7 days
    date_range = [(start_date + timedelta(days=i)) for i in range(7)]
    
    # Format dates as labels for chart
    chart_data['labels'] = [date.strftime('%a %d') for date in date_range]
    
    # Get attendance rate for each day in the range
    for day in date_range:
        # Query records for this specific day
        day_records = UnitAttendance.query.join(
            TeachingUnit, UnitAttendance.teaching_unit_id == TeachingUnit.id
        ).filter(
            TeachingUnit.employee_id == current_user.id,
            UnitAttendance.date == day
        ).all()
        
        # Calculate attendance rate for the day
        if day_records:
            present_records = sum(1 for r in day_records if r.status == 'present')
            rate = (present_records / len(day_records)) * 100 if day_records else 0
            chart_data['attendance_rates'].append(round(rate, 1))
        else:
            # No records for this day
            chart_data['attendance_rates'].append(0)
    
    # Pass the profile, stats, and chart data to the template
    return render_template('dashboard.html', 
                          profile=profile,
                          attendance_stats=attendance_stats,
                          leave_stats=leave_stats,
                          training_stats=training_stats,
                          teaching_stats=teaching_stats,
                          teaching_units=teaching_units,
                          recent_activities=recent_activities,
                          chart_data=chart_data)

@dashboard_bp.route('/')
def landing():
    """Landing page for new visitors"""
    # If user is logged in, redirect to dashboard
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    return render_template('index.html')