"""
Payroll routes for the HR system.
Handles payroll processing, deductions, and reports.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, abort
from flask_login import login_required, current_user
# Update model imports to use the correct names
from models import db, User, Payroll, PayrollDeduction, PayrollUnit, EmployeeProfile
from forms import PayrollForm, PayrollDeductionForm, PayrollSearchForm
from utils.decorators import hr_or_admin_required
from datetime import datetime, timedelta
import calendar

# Import functions from attendance and teaching modules
from routes.attendance import get_attendance_for_payroll
from routes.teaching import get_teaching_data_for_payroll

payroll_bp = Blueprint('payroll', __name__)

@payroll_bp.route('/payroll')
@login_required
def index():
    """Show list of payroll records"""
    # Initialize the search form
    form = PayrollSearchForm(request.args, meta={'csrf': False})
    
    # Set employee choices if admin or HR
    if current_user.is_admin() or current_user.is_hr():
        employees = User.query.all()
        form.employee.choices = [('', 'All Employees')] + [(str(u.id), u.get_display_name()) for u in employees]
    
    # Build query based on search criteria
    query = Payroll.query
    
    # Filter by employee
    if not (current_user.is_admin() or current_user.is_hr()):
        # Regular users can only see their own payroll
        query = query.filter_by(employee_id=current_user.id)
    elif form.employee.data and form.employee.data != '':
        # Convert the string back to integer for database query
        query = query.filter_by(employee_id=int(form.employee.data))
    
    # Filter by period
    if form.period.data:
        today = datetime.utcnow().date()
        if form.period.data == 'current_month':
            start_date = datetime(today.year, today.month, 1).date()
            if today.month == 12:
                end_date = datetime(today.year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(today.year, today.month + 1, 1).date() - timedelta(days=1)
            query = query.filter(Payroll.period_start >= start_date, Payroll.period_end <= end_date)
        elif form.period.data == 'previous_month':
            if today.month == 1:
                start_date = datetime(today.year - 1, 12, 1).date()
                end_date = datetime(today.year, 1, 1).date() - timedelta(days=1)
            else:
                start_date = datetime(today.year, today.month - 1, 1).date()
                end_date = datetime(today.year, today.month, 1).date() - timedelta(days=1)
            query = query.filter(Payroll.period_start >= start_date, Payroll.period_end <= end_date)
        elif form.period.data == 'current_year':
            start_date = datetime(today.year, 1, 1).date()
            end_date = datetime(today.year + 1, 1, 1).date() - timedelta(days=1)
            query = query.filter(Payroll.period_start >= start_date, Payroll.period_end <= end_date)
    
    # Filter by date range
    if form.start_date.data:
        query = query.filter(Payroll.period_start >= form.start_date.data)
    if form.end_date.data:
        query = query.filter(Payroll.period_end <= form.end_date.data)
    
    # Filter by status
    if form.status.data:
        query = query.filter_by(status=form.status.data)
    
    # Order by creation date, newest first
    payrolls = query.order_by(Payroll.created_at.desc()).all()
    
    return render_template('payroll/index.html', payrolls=payrolls, form=form)

@payroll_bp.route('/new', methods=['GET', 'POST'])
@login_required
@hr_or_admin_required
def new():
    """Create a new payroll record"""
    form = PayrollForm()
    
    # Fetch employees and set them as choices for the form dropdown
    employees = User.query.all()
    form.employee_id.choices = [(employee.id, employee.get_display_name()) for employee in employees]
    
    if form.validate_on_submit():
        employee_id = form.employee_id.data
        period_start = form.period_start.data
        period_end = form.period_end.data
        
        # Get attendance data for this employee and period
        attendance_data = get_attendance_for_payroll(employee_id, period_start, period_end)
        
        # Get teaching data for this employee and period
        teaching_data = get_teaching_data_for_payroll(employee_id, period_start, period_end)
        
        # Calculate base and unit pay
        base_pay = form.base_pay.data
        unit_pay = teaching_data['total_earnings']
        
        # Calculate deductions from attendance
        attendance_deductions = attendance_data['total_deduction']
        
        # Calculate gross and net pay
        gross_pay = base_pay + unit_pay
        total_deductions = form.deductions.data + attendance_deductions
        net_pay = gross_pay - total_deductions
        
        # Create new payroll record - use Payroll instead of PayrollRecord
        payroll = Payroll(
            employee_id=employee_id,
            period_start=period_start,
            period_end=period_end,
            base_pay=base_pay,
            unit_pay=unit_pay,
            overtime_pay=form.overtime_pay.data,
            bonus=form.bonus.data,
            deductions=total_deductions,
            tax_deduction=form.tax_deduction.data,
            net_pay=net_pay,
            payment_method=form.payment_method.data,
            status=form.status.data,
            notes=form.notes.data,
            created_by=current_user.id
        )
        db.session.add(payroll)
        db.session.commit()
        
        # Add attendance-based deductions - use PayrollDeduction instead of Deduction
        for deduction in attendance_data['deductions']:
            new_deduction = PayrollDeduction(
                payroll_id=payroll.id,
                deduction_type=deduction['type'],
                description=deduction['description'],
                amount=deduction['amount']
            )
            db.session.add(new_deduction)
        
        # Add teaching unit earnings as positive deductions (additions)
        for unit in teaching_data['units']:
            if unit['earnings'] > 0:
                # Create a PayrollUnit record for the teaching earnings
                new_unit = PayrollUnit(
                    payroll_id=payroll.id,
                    unit_id=unit['id'],
                    hours=unit['hours_taught'],
                    rate=unit['rate_per_unit'],
                    amount=unit['earnings'],
                    description=f"Teaching: {unit['title']} ({unit['hours_taught']} hours @ ${unit['rate_per_unit']}/hr)"
                )
                db.session.add(new_unit)
        
        db.session.commit()
        
        flash('Payroll record created successfully!', 'success')
        return redirect(url_for('payroll.view', payroll_id=payroll.id))
        
    return render_template('payroll/new.html', form=form)

@payroll_bp.route('/<int:payroll_id>/view')
@login_required
def view(payroll_id):
    """View a payroll record"""
    # Use Payroll instead of PayrollRecord
    payroll = Payroll.query.get_or_404(payroll_id)
    
    # Check authorization
    if not (current_user.is_hr() or current_user.is_admin() or current_user.id == payroll.employee_id):
        abort(403)
    
    # Get all deductions for this payroll - use PayrollDeduction
    deductions = PayrollDeduction.query.filter_by(payroll_id=payroll_id).all()
    
    # Get all teaching units for this payroll - use PayrollUnit
    teaching_units = PayrollUnit.query.filter_by(payroll_id=payroll_id).all()
    
    # Get attendance data for this payroll period
    attendance_data = get_attendance_for_payroll(
        payroll.employee_id, 
        payroll.period_start, 
        payroll.period_end
    )
    
    return render_template(
        'payroll/view.html', 
        payroll=payroll, 
        deductions=deductions,
        teaching_units=teaching_units,
        attendance_stats=attendance_data['stats']
    )

@payroll_bp.route('/payroll/<int:payroll_id>/edit', methods=['GET', 'POST'])
@login_required
@hr_or_admin_required
def edit(payroll_id):
    """Edit an existing payroll record"""
    payroll = Payroll.query.get_or_404(payroll_id)
    
    # Only allow editing of draft or pending payrolls
    if payroll.status not in ['draft', 'pending']:
        flash('Cannot edit a payroll that has been approved or paid.', 'danger')
        return redirect(url_for('payroll.view', payroll_id=payroll_id))
    
    form = PayrollForm(obj=payroll)
    
    # Add this section to populate the employee choices in the form
    employees = User.query.all()
    form.employee_id.choices = [(employee.id, employee.get_display_name()) for employee in employees]
    
    if form.validate_on_submit():
        form.populate_obj(payroll)
        db.session.commit()
        
        flash('Payroll updated successfully!', 'success')
        return redirect(url_for('payroll.view', payroll_id=payroll.id))
    
    return render_template('payroll/edit.html', payroll=payroll, form=form)

@payroll_bp.route('/payroll/<int:payroll_id>/deductions', methods=['GET', 'POST'])
@login_required
@hr_or_admin_required
def manage_deductions(payroll_id):
    """Manage deductions for a payroll record"""
    payroll = Payroll.query.get_or_404(payroll_id)
    
    deductions = PayrollDeduction.query.filter_by(payroll_id=payroll_id).all()
    deduction_form = PayrollDeductionForm()
    
    return render_template(
        'payroll/deductions.html',
        payroll=payroll,
        deductions=deductions,
        deduction_form=deduction_form
    )

@payroll_bp.route('/payroll/<int:payroll_id>/deductions/add', methods=['POST', 'GET'])
@login_required
@hr_or_admin_required
def add_deduction(payroll_id):
    """Add a deduction to a payroll"""
    payroll = Payroll.query.get_or_404(payroll_id)
    form = PayrollDeductionForm()
    
    if request.method == 'GET':
        flash('Please add deductions from the deductions management page.', 'info')
        return redirect(url_for('payroll.manage_deductions', payroll_id=payroll_id))
    
    if form.validate_on_submit():
        try:
            deduction = PayrollDeduction(
                payroll_id=payroll.id,
                deduction_type=form.deduction_type.data,
                description=form.description.data,
                amount=form.amount.data
            )
            db.session.add(deduction)
            payroll.deductions += form.amount.data
            db.session.commit()
            
            flash('Deduction added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding deduction: {str(e)}', 'danger')
    
    return redirect(url_for('payroll.manage_deductions', payroll_id=payroll_id))

@payroll_bp.route('/payroll/<int:payroll_id>/deductions/<int:deduction_id>/delete', methods=['POST'])
@login_required
@hr_or_admin_required
def delete_deduction(payroll_id, deduction_id):
    """Delete a deduction from a payroll record"""
    deduction = PayrollDeduction.query.get_or_404(deduction_id)
    payroll = Payroll.query.get_or_404(payroll_id)
    
    if deduction.payroll_id != payroll_id:
        abort(404)
    
    db.session.delete(deduction)
    db.session.commit()
    
    payroll.deductions -= deduction.amount
    db.session.commit()
    
    flash('Deduction deleted successfully!', 'success')
    return redirect(url_for('payroll.manage_deductions', payroll_id=payroll_id))

@payroll_bp.route('/payroll/<int:payroll_id>/process', methods=['GET', 'POST'])
@login_required
@hr_or_admin_required
def process(payroll_id):
    """Process a payroll record"""
    payroll = Payroll.query.get_or_404(payroll_id)
    
    if request.method == 'GET':
        return render_template('payroll/process.html', payroll=payroll)
        
    if request.method == 'POST':
        try:
            payment_date = request.form.get('payment_date')
            payment_complete = bool(request.form.get('payment_complete'))
            
            if payment_date:
                payroll.payment_date = datetime.strptime(payment_date, '%Y-%m-%d').date()
            
            if payment_complete:
                payroll.status = 'paid'
            else:
                payroll.status = 'approved'
                
            db.session.commit()
            flash('Payroll has been processed successfully!', 'success')
            return redirect(url_for('payroll.view', payroll_id=payroll.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing payroll: {str(e)}', 'danger')
    
    return render_template('payroll/process.html', payroll=payroll)

@payroll_bp.route('/payroll/<int:payroll_id>/print')
@login_required
def print_payroll(payroll_id):
    """Generate a printable view of the payroll"""
    payroll = Payroll.query.get_or_404(payroll_id)
    
    if not (current_user.id == payroll.employee_id or current_user.is_hr() or current_user.is_admin()):
        flash("You don't have permission to view this payroll record", "danger")
        return redirect(url_for('dashboard.index'))
    
    def now():
        return datetime.utcnow()
    
    return render_template('payroll/print.html', payroll=payroll, now=now)

@payroll_bp.route('/payroll/<int:payroll_id>/attendance')
@login_required
def attendance_details(payroll_id):
    """View detailed attendance for a payroll period"""
    # Get payroll record
    payroll = Payroll.query.get_or_404(payroll_id)
    
    # Check authorization
    if not (current_user.is_hr() or current_user.is_admin() or current_user.id == payroll.employee_id):
        abort(403)
    
    # Get attendance data for this payroll period
    attendance_data = get_attendance_for_payroll(
        payroll.employee_id, 
        payroll.period_start, 
        payroll.period_end
    )
    
    # Handle case where records key might not exist in older versions
    attendance_records = attendance_data.get('records', [])
    
    return render_template(
        'payroll/attendance_details.html',
        payroll=payroll,
        attendance_stats=attendance_data['stats'],
        attendance_records=attendance_records
    )

@payroll_bp.route('/generate-from-unit/<int:unit_id>', methods=['GET'])
@login_required
@hr_or_admin_required
def generate_from_unit(unit_id):
    """Generate a payroll record for a specific teaching unit"""
    from models import TeachingUnit
    
    # Fetch the teaching unit
    unit = TeachingUnit.query.get_or_404(unit_id)
    
    # Set default period to the unit's start and end dates
    period_start = unit.start_date
    period_end = unit.end_date
    
    # Get attendance data for this employee and period
    attendance_data = get_attendance_for_payroll(unit.employee_id, period_start, period_end)
    
    # Calculate payment based on unit's data
    attendance_factor = unit.attendance_rate / 100
    unit_payment = unit.total_payment * attendance_factor
    
    # Create new payroll record
    payroll = Payroll(
        employee_id=unit.employee_id,
        period_start=period_start,
        period_end=period_end,
        base_pay=0,  # No base pay, just unit pay
        unit_pay=unit_payment,
        deductions=0,
        payment_method='direct_deposit',  # Default payment method
        status='draft',
        notes=f"Automatically generated from teaching unit: {unit.title}",
        created_by=current_user.id
    )
    db.session.add(payroll)
    db.session.commit()
    
    # Add the teaching unit to the payroll - include all required fields
    new_unit = PayrollUnit(
        payroll_id=payroll.id,
        teaching_unit_id=unit.id,
        unit_value=unit.unit_value,
        rate_per_unit=unit.rate_per_unit,
        attendance_factor=unit.attendance_rate / 100,
        total_amount=unit_payment
    )
    db.session.add(new_unit)
    
    db.session.commit()
    
    # Redirect to the payroll view with a success message
    flash(f'Payroll record generated successfully for teaching unit "{unit.title}"!', 'success')
    flash(f'Generated payroll amount: ${unit_payment:.2f} based on attendance rate of {unit.attendance_rate:.1f}%', 'info')
    return redirect(url_for('payroll.view', payroll_id=payroll.id))
