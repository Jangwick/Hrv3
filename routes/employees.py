"""
Employee management routes for the HR system.
Handles employee listing, details, exports, and salary management.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, Response, send_file
from flask_login import login_required, current_user
from models import User, EmployeeProfile, EmployeeSalary, db
from forms import EmployeeSearchForm, SalaryForm
from utils.decorators import hr_required
import io, csv, tempfile
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

employees_bp = Blueprint('employees', __name__)

@employees_bp.route('/employees')
@login_required
@hr_required
def list():
    """Display list of faculty and staff (Department Heads and Admin only)"""
    form = EmployeeSearchForm(request.args, meta={'csrf': False})
    
    # Base query
    query = User.query.join(User.profile, isouter=True)
    
    # Apply filters if provided
    if form.validate():
        # Filter by search term in name or email
        if form.search.data:
            search_term = f"%{form.search.data}%"
            query = query.filter(
                db.or_(
                    User.username.like(search_term),
                    User.email.like(search_term),
                    EmployeeProfile.first_name.like(search_term),
                    EmployeeProfile.last_name.like(search_term)
                )
            )
        
        # Filter by department
        if form.department.data:
            query = query.filter(User.department == form.department.data)
    
    # Get employees (exclude admins if current user is HR but not admin)
    if current_user.is_admin():
        employees = query.order_by(User.username).all()
    else:
        employees = query.filter(User.role != 'admin').order_by(User.username).all()
    
    return render_template('employee_list.html', employees=employees, form=form)

@employees_bp.route('/employees/<int:employee_id>')
@login_required
@hr_required
def detail(employee_id):
    """Display employee details (HR and Admin only)"""
    user = User.query.get_or_404(employee_id)
    
    # Don't allow HR staff to view admin profiles unless they are admin
    if user.role == 'admin' and not current_user.is_admin():
        flash("You don't have permission to view this profile", "danger")
        return redirect(url_for('employees.list'))
        
    return render_template('employee_detail.html', employee=user)

@employees_bp.route('/employees/<int:employee_id>/salary', methods=['GET', 'POST'])
@login_required
@hr_required
def manage_salary(employee_id):
    """Manage faculty/staff compensation"""
    employee = User.query.get_or_404(employee_id)
    
    # Get current salary if it exists
    current_salary = EmployeeSalary.query.filter_by(
        employee_id=employee_id, end_date=None
    ).first()
    
    # Get salary history
    salary_history = EmployeeSalary.query.filter_by(
        employee_id=employee_id
    ).order_by(EmployeeSalary.effective_date.desc()).all()
    
    form = SalaryForm()
    
    if current_salary and request.method == 'GET':
        # Prefill form with current salary data if available
        form.salary_type.data = current_salary.salary_type
        form.currency.data = current_salary.currency
        form.amount.data = current_salary.amount
        form.contract_type.data = current_salary.contract_type if hasattr(current_salary, 'contract_type') else 'full_time'
    
    if form.validate_on_submit():
        # If there's a current active salary, set its end date to the day before new effective date
        if current_salary and current_salary.effective_date < form.effective_date.data:
            end_date = form.effective_date.data - timedelta(days=1)
            current_salary.end_date = end_date
        
        # Determine academic year based on effective date
        effective_date = form.effective_date.data
        if effective_date.month >= 8:  # August or later
            academic_year = f"{effective_date.year}-{effective_date.year + 1}"
        else:
            academic_year = f"{effective_date.year - 1}-{effective_date.year}"
        
        # Create new salary record
        new_salary = EmployeeSalary(
            employee_id=employee_id,
            salary_type=form.salary_type.data,
            effective_date=form.effective_date.data,
            currency=form.currency.data,
            amount=form.amount.data,
            contract_type=form.contract_type.data,
            academic_year=academic_year,
            created_by=current_user.id
        )
        db.session.add(new_salary)
        db.session.commit()
        
        flash('Compensation information updated successfully!', 'success')
        return redirect(url_for('employees.manage_salary', employee_id=employee_id))
        
    return render_template('employees/salary.html', 
                          employee=employee, 
                          current_salary=current_salary, 
                          salary_history=salary_history, 
                          form=form)

@employees_bp.route('/employees/export', methods=['GET'])
@login_required
@hr_required
def export():
    """Export employees list as CSV or PDF"""
    export_format = request.args.get('format', 'csv')
    
    # Base query - similar to employee_list
    query = User.query.join(User.profile, isouter=True)
    
    # Apply filters if provided in URL params
    search = request.args.get('search', '')
    department = request.args.get('department', '')
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            db.or_(
                User.username.like(search_term),
                User.email.like(search_term),
                EmployeeProfile.first_name.like(search_term),
                EmployeeProfile.last_name.like(search_term)
            )
        )
    
    if department:
        query = query.filter(User.department == department)
    
    # Get employees (exclude admins if current user is HR but not admin)
    if current_user.is_admin():
        employees = query.order_by(User.username).all()
    else:
        employees = query.filter(User.role != 'admin').order_by(User.username).all()
    
    # Prepare data for export
    data = []
    for employee in employees:
        employee_data = {
            'employee_id': employee.id,
            'username': employee.username,
            'email': employee.email,
            'department': employee.department.replace('_', ' ').title(),
            'role': employee.role.title(),
            'first_name': employee.profile.first_name if hasattr(employee, 'profile') and employee.profile else '',
            'last_name': employee.profile.last_name if hasattr(employee, 'profile') and employee.profile else '',
            'position': employee.profile.position if hasattr(employee, 'profile') and employee.profile else '',
            'hire_date': employee.profile.hire_date.strftime('%Y-%m-%d') if hasattr(employee, 'profile') and employee.profile and employee.profile.hire_date else '',
            'phone_number': employee.profile.phone_number if hasattr(employee, 'profile') and employee.profile else ''
        }
        data.append(employee_data)
    
    # Generate timestamp for filename
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    
    if export_format == 'csv':
        # Export to CSV
        output = io.StringIO()
        fieldnames = ['employee_id', 'username', 'email', 'first_name', 'last_name', 
                     'department', 'position', 'role', 'hire_date', 'phone_number']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        
        # Create response
        output.seek(0)
        filename = f"employee_directory_{timestamp}.csv"
        
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
        
    elif export_format == 'pdf':
        # Create a temporary file for the PDF
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Create the PDF document
        doc = SimpleDocTemplate(temp_path, pagesize=letter)
        styles = getSampleStyleSheet()
        elements = []
        
        # Title and header
        title = "Employee Directory"
        date_str = datetime.now().strftime('%B %d, %Y')
        
        elements.append(Paragraph(title, styles['Title']))
        elements.append(Paragraph(f"Generated on {date_str}", styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Add filter information if any
        if search or department:
            filter_text = "Filters: "
            if search:
                filter_text += f"Search term '{search}' "
            if department:
                filter_text += f"Department: {department.replace('_', ' ').title()}"
            elements.append(Paragraph(filter_text, styles['Italic']))
            elements.append(Spacer(1, 10))
        
        # Table data
        table_data = [
            ["Name", "Username", "Email", "Department", "Position", "Role", "Hire Date"]
        ]
        
        # Add employee data
        for emp in data:
            name = f"{emp['first_name']} {emp['last_name']}".strip()
            if not name:
                name = emp['username']
                
            table_data.append([
                name,
                emp['username'],
                emp['email'],
                emp['department'],
                emp['position'],
                emp['role'],
                emp['hire_date']
            ])
        
        # Create the table
        table = Table(table_data)
        
        # Apply styles to the table
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows - alternate row colors
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            
            # Add grids
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        
        # Add table to elements
        elements.append(table)
        
        # Footer
        elements.append(Spacer(1, 20))
        footer_text = "Confidential: This document contains employee information and should be handled according to HR policies."
        elements.append(Paragraph(footer_text, styles['Italic']))
        
        # Build the PDF
        doc.build(elements)
        
        # Return the PDF file as a download
        filename = f"employee_directory_{timestamp}.pdf"
        
        return send_file(
            temp_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=filename
        )
    
    else:
        flash('Invalid export format', 'error')
        return redirect(url_for('employees.list'))

@employees_bp.route('/employees/<int:employee_id>/attendance')
@login_required
@hr_required
def attendance(employee_id):
    """View attendance records for a specific employee"""
    from models import TeachingUnit, UnitAttendance
    
    employee = User.query.get_or_404(employee_id)
    
    # Get teaching units for this employee
    units = TeachingUnit.query.filter_by(employee_id=employee_id).all()
    
    # Get attendance statistics
    attendance_stats = {}
    for unit in units:
        total_attendances = UnitAttendance.query.filter_by(teaching_unit_id=unit.id).count()
        present_attendances = UnitAttendance.query.filter_by(
            teaching_unit_id=unit.id, 
            status='present'
        ).count()
        
        attendance_stats[unit.id] = {
            'total': total_attendances,
            'present': present_attendances,
            'rate': (present_attendances / total_attendances * 100) if total_attendances > 0 else 0
        }
    
    # Get recent attendance records
    recent_records = UnitAttendance.query.join(
        TeachingUnit, UnitAttendance.teaching_unit_id == TeachingUnit.id
    ).filter(
        TeachingUnit.employee_id == employee_id
    ).order_by(UnitAttendance.date.desc()).limit(10).all()
    
    return render_template(
        'attendance/employee.html',
        employee=employee,
        units=units,
        attendance_stats=attendance_stats,
        recent_records=recent_records
    )
