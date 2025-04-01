"""
Attendance routes for the HR system.
Handles attendance tracking, reporting, and analytics.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, Response, send_file, current_app, abort, jsonify
from flask_login import login_required, current_user
from models import TeachingUnit, UnitAttendance, User, db, EmployeeProfile
from forms import AttendanceReportForm, AttendanceForm
from utils.decorators import hr_required, hr_or_admin_required
import io, csv, tempfile, os
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from sqlalchemy import func, and_, or_

attendance_bp = Blueprint('attendance', __name__)

@attendance_bp.route('/attendance')
@login_required
def index():
    """Display attendance dashboard - overview of all attendance records"""
    # Different views for different user roles
    if current_user.is_admin() or current_user.is_hr():
        # Get all units that are active or completed in the last 90 days
        cutoff_date = datetime.now().date() - timedelta(days=90)
        
        units = TeachingUnit.query.filter(
            db.or_(
                TeachingUnit.status == 'active',
                db.and_(
                    TeachingUnit.status == 'completed',
                    TeachingUnit.end_date >= cutoff_date
                )
            )
        ).order_by(TeachingUnit.start_date.desc()).all()
        
        # Get attendance statistics for all units
        unit_stats = {}
        for unit in units:
            total_records = UnitAttendance.query.filter_by(teaching_unit_id=unit.id).count()
            present_records = UnitAttendance.query.filter_by(
                teaching_unit_id=unit.id,
                status='present'
            ).count()
            
            # Calculate attendance rate
            rate = (present_records / total_records * 100) if total_records > 0 else 0
            
            unit_stats[unit.id] = {
                'total': total_records,
                'present': present_records,
                'rate': rate
            }
        
        return render_template(
            'attendance/dashboard.html',
            units=units,
            unit_stats=unit_stats
        )
    else:
        # Regular faculty/staff see their own units
        units = TeachingUnit.query.filter_by(
            employee_id=current_user.id
        ).filter(
            db.or_(
                TeachingUnit.status == 'active',
                TeachingUnit.status == 'completed'
            )
        ).order_by(TeachingUnit.start_date.desc()).all()
        
        # Get recent attendance records
        recent_attendance = UnitAttendance.query.join(
            TeachingUnit, UnitAttendance.teaching_unit_id == TeachingUnit.id
        ).filter(
            TeachingUnit.employee_id == current_user.id
        ).order_by(UnitAttendance.date.desc()).limit(10).all()
        
        return render_template(
            'attendance/dashboard.html',
            units=units,
            recent_attendance=recent_attendance
        )

@attendance_bp.route('/attendance/analytics')
@login_required
@hr_required
def analytics():
    """Display attendance analytics and visualizations"""
    return render_template('attendance/analytics.html')

@attendance_bp.route('/attendance/report', methods=['GET', 'POST'])
@login_required
@hr_required
def report():
    """Generate attendance reports"""
    form = AttendanceReportForm()
    
    # Populate employee and unit dropdowns
    form.employee.choices = [(0, 'All Employees')] + [(u.id, u.get_display_name()) for u in User.query.all()]
    form.unit.choices = [(0, 'All Units')] + [(u.id, f"{u.title} ({u.code or 'No code'})") for u in TeachingUnit.query.all()]
    
    if form.validate_on_submit() or request.args.get('format'):
        # Process form data and generate report
        if request.method == 'GET' and request.args.get('format'):
            # For export requests, use query parameters
            employee_id = int(request.args.get('employee', 0))
            unit_id = int(request.args.get('unit', 0))
            date_range = request.args.get('date_range', 'current_month')
            report_format = request.args.get('format', 'csv')
            # Additional parameters
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        else:
            # Use form data for POST requests
            employee_id = form.employee.data
            unit_id = form.unit.data
            date_range = form.date_range.data
            report_format = form.format.data
            start_date = form.start_date.data
            end_date = form.end_date.data
        
        # Build the query for attendance records
        query = UnitAttendance.query.join(TeachingUnit)
        
        # Apply date range filter
        if date_range == "custom" and start_date and end_date:
            query = query.filter(UnitAttendance.date >= start_date, UnitAttendance.date <= end_date)
        elif date_range == "current_month":
            today = datetime.today()
            start_date = datetime(today.year, today.month, 1).date()
            # Compute the last day of the current month
            if today.month == 12:
                end_date = datetime(today.year + 1, 1, 1).date() - timedelta(days=1)
            else:
                end_date = datetime(today.year, today.month + 1, 1).date() - timedelta(days=1)
            query = query.filter(UnitAttendance.date >= start_date, UnitAttendance.date <= end_date)
        
        # Apply employee filter if specified
        if employee_id > 0:
            query = query.filter(TeachingUnit.employee_id == employee_id)
        
        # Apply teaching unit filter if specified
        if unit_id > 0:
            query = query.filter(UnitAttendance.teaching_unit_id == unit_id)
            
        # Get results
        attendances = query.order_by(UnitAttendance.date.desc()).all()
        
        # Prepare report data
        report_data = []
        for attendance in attendances:
            teacher = attendance.teaching_unit.employee
            report_data.append({
                'date': attendance.date.strftime('%Y-%m-%d'),
                'employee': teacher.get_display_name(),
                'unit_title': attendance.teaching_unit.title,
                'unit_code': attendance.teaching_unit.code or 'N/A',
                'status': attendance.status.capitalize(),
                'hours': attendance.hours,
                'attendance_factor': '100%' if attendance.status == 'present' else 
                                    '75%' if attendance.status == 'late' else
                                    '50%' if attendance.status == 'excused' else '0%',
                'notes': attendance.notes or ''
            })
            
        # Calculate summary statistics
        total_records = len(report_data)
        present_hours = sum(a.hours for a in attendances if a.status == 'present')
        late_hours = sum(a.hours * 0.75 for a in attendances if a.status == 'late')
        excused_hours = sum(a.hours * 0.5 for a in attendances if a.status == 'excused')
        absent_hours = sum(a.hours for a in attendances if a.status == 'absent')
        total_hours = sum(a.hours for a in attendances)
        attendance_rate = ((present_hours + late_hours + excused_hours) / total_hours * 100) if total_hours > 0 else 0
        
        # Faculty breakdown - group attendance by faculty
        faculty_breakdown = {}
        for attendance in attendances:
            teacher = attendance.teaching_unit.employee
            teacher_id = teacher.id
            teacher_name = teacher.get_display_name()
            
            if teacher_id not in faculty_breakdown:
                faculty_breakdown[teacher_id] = {
                    'name': teacher_name,
                    'total_hours': 0,
                    'present_hours': 0,
                    'late_hours': 0,
                    'excused_hours': 0,
                    'absent_hours': 0,
                    'rate': 0
                }
            
            # Add hours to faculty totals
            faculty_breakdown[teacher_id]['total_hours'] += attendance.hours
            
            if attendance.status == 'present':
                faculty_breakdown[teacher_id]['present_hours'] += attendance.hours
            elif attendance.status == 'late':
                faculty_breakdown[teacher_id]['late_hours'] += attendance.hours
            elif attendance.status == 'excused':
                faculty_breakdown[teacher_id]['excused_hours'] += attendance.hours
            elif attendance.status == 'absent':
                faculty_breakdown[teacher_id]['absent_hours'] += attendance.hours
        
        # Calculate attendance rate for each faculty
        for faculty_id in faculty_breakdown:
            faculty = faculty_breakdown[faculty_id]
            faculty_total = faculty['total_hours']
            if faculty_total > 0:
                weighted_hours = (faculty['present_hours'] + 
                                  faculty['late_hours'] * 0.75 + 
                                  faculty['excused_hours'] * 0.5)
                faculty['rate'] = (weighted_hours / faculty_total) * 100
            else:
                faculty['rate'] = 0
        
        summary = {
            'total_records': total_records,
            'date_range': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'present_hours': present_hours,
            'late_hours': late_hours, 
            'excused_hours': excused_hours,
            'absent_hours': absent_hours,
            'total_hours': total_hours,
            'attendance_rate': attendance_rate,
            'faculty_breakdown': faculty_breakdown
        }
        
        # Handle report format
        if report_format == 'csv':
            # Generate CSV
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                'date', 'employee', 'unit_title', 'unit_code', 'status', 'hours', 'attendance_factor', 'notes'
            ])
            writer.writeheader()
            writer.writerows(report_data)
            
            # Return CSV download
            today = datetime.today()
            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={"Content-disposition": f"attachment; filename=attendance_report_{today.strftime('%Y%m%d')}.csv"}
            )
            
        elif report_format == 'pdf':
            # Generate PDF report
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            filename = f"attendance_report_{timestamp}.pdf"
            
            # Create a temporary file path
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_path = temp_file.name
                
            # Use ReportLab to generate PDF
            doc = SimpleDocTemplate(temp_path, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            
            # Title and header
            elements.append(Paragraph("Attendance Report", styles['Title']))
            elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Summary section
            elements.append(Paragraph("Summary", styles['Heading2']))
            summary_data = [
                ["Date Range", "Total Records", "Attendance Rate"],
                [summary['date_range'], str(summary['total_records']), f"{summary['attendance_rate']:.1f}%"]
            ]
            
            summary_table = Table(summary_data, colWidths=[200, 100, 100])
            summary_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(summary_table)
            elements.append(Spacer(1, 20))
            
            # Detailed records table
            elements.append(Paragraph("Attendance Records", styles['Heading2']))
            
            if report_data:
                # Table header
                table_data = [["Date", "Employee", "Unit", "Status", "Hours", "Factor"]]
                
                # Add data rows
                for record in report_data:
                    table_data.append([
                        record['date'],
                        record['employee'],
                        record['unit_title'],
                        record['status'],
                        str(record['hours']),
                        record['attendance_factor']
                    ])
                
                # Create table with column widths
                detail_table = Table(table_data, colWidths=[80, 100, 120, 70, 50, 60])
                detail_table.setStyle(TableStyle([
                    # Header formatting
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    # Body formatting
                    ('ALIGN', (3, 1), (5, -1), 'CENTER'),  # Center status, hours, factor
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    # Row colors
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                
                elements.append(detail_table)
            else:
                elements.append(Paragraph("No attendance records found matching the criteria.", styles['Normal']))
            
            # Build the PDF
            doc.build(elements)
            
            # Return the PDF file
            return send_file(
                temp_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
        
        # Return HTML view of the report
        return render_template(
            'attendance/report_results.html',
            report_data=report_data,
            summary=summary,
            form=form
        )
    
    return render_template('attendance/report_form.html', form=form)

@attendance_bp.route('/employee/<int:employee_id>/report', methods=['GET'])
@login_required
@hr_or_admin_required
def generate_employee_report(employee_id):
    """Generate a comprehensive attendance report for an employee"""
    employee = User.query.get_or_404(employee_id)
    
    # Get date range (default to current month)
    today = datetime.now().date()
    start_date = request.args.get('start_date', datetime(today.year, today.month, 1).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', today.strftime('%Y-%m-%d'))
    
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get teaching units for this employee
    teaching_units = TeachingUnit.query.filter_by(employee_id=employee_id).all()
    
    # Get attendance for these units in the date range
    attendance_records = UnitAttendance.query.filter(
        UnitAttendance.teaching_unit_id.in_([unit.id for unit in teaching_units]),
        UnitAttendance.date.between(start_date, end_date)
    ).order_by(UnitAttendance.date.desc()).all()
    
    # Calculate attendance statistics
    stats = calculate_attendance_stats(employee_id, start_date, end_date)
    
    # Format for export
    report_format = request.args.get('format', 'html')
    if report_format == 'pdf':
        return generate_pdf_report(employee, attendance_records, stats, start_date, end_date)
    elif report_format == 'csv':
        return generate_csv_report(employee, attendance_records, stats, start_date, end_date)
    
    # Default: return HTML template
    return render_template(
        'attendance/employee_report.html',
        employee=employee,
        attendance_records=attendance_records,
        stats=stats,
        start_date=start_date,
        end_date=end_date
    )

def calculate_attendance_stats(employee_id, start_date, end_date):
    """Calculate detailed attendance statistics for payroll and reports"""
    teaching_units = TeachingUnit.query.filter_by(employee_id=employee_id).all()
    
    stats = {
        'total_days': 0,
        'present_days': 0,
        'absent_days': 0,
        'late_days': 0,
        'excused_days': 0,
        'attendance_rate': 0,
        'units': {}
    }
    
    for unit in teaching_units:
        # Calculate working days for this unit between dates
        unit_stats = {
            'total': 0,
            'present': 0,
            'absent': 0,
            'late': 0,
            'excused': 0,
            'rate': 0
        }
        
        # Get attendance records for this unit
        records = UnitAttendance.query.filter(
            UnitAttendance.teaching_unit_id == unit.id,
            UnitAttendance.date.between(start_date, end_date)
        ).all()
        
        unit_stats['total'] = len(records)
        
        # Count status types
        for record in records:
            if record.status == 'present':
                unit_stats['present'] += 1
                stats['present_days'] += 1
            elif record.status == 'absent':
                unit_stats['absent'] += 1
                stats['absent_days'] += 1
            elif record.status == 'late':
                unit_stats['late'] += 1
                stats['late_days'] += 1
            elif record.status == 'excused':
                unit_stats['excused'] += 1
                stats['excused_days'] += 1
        
        # Calculate attendance rate for this unit
        unit_stats['rate'] = (unit_stats['present'] / unit_stats['total'] * 100) if unit_stats['total'] > 0 else 0
        
        # Add to overall stats
        stats['total_days'] += unit_stats['total']
        stats['units'][unit.id] = unit_stats
    
    # Calculate overall attendance rate
    stats['attendance_rate'] = (stats['present_days'] / stats['total_days'] * 100) if stats['total_days'] > 0 else 0
    
    return stats

def generate_pdf_report(employee, attendance_records, stats, start_date, end_date):
    """Generate a PDF attendance report"""
    # Create a PDF in memory
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title = Paragraph(f"Attendance Report - {employee.get_display_name()}", styles["Title"])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Date range
    date_info = Paragraph(f"Period: {start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}", styles["Normal"])
    elements.append(date_info)
    elements.append(Spacer(1, 12))
    
    # Summary Statistics
    elements.append(Paragraph("Attendance Summary", styles["Heading2"]))
    summary_data = [
        ["Total Days", "Present", "Absent", "Late", "Excused", "Attendance Rate"],
        [
            str(stats['total_days']),
            str(stats['present_days']),
            str(stats['absent_days']),
            str(stats['late_days']),
            str(stats['excused_days']),
            f"{stats['attendance_rate']:.1f}%"
        ]
    ]
    summary_table = Table(summary_data, colWidths=[doc.width/6.0]*6)
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 20))
    
    # Detailed Records
    elements.append(Paragraph("Attendance Records", styles["Heading2"]))
    
    if attendance_records:
        record_data = [["Date", "Teaching Unit", "Status", "Hours", "Notes"]]
        for record in attendance_records:
            record_data.append([
                record.date.strftime('%Y-%m-%d'),
                record.teaching_unit.title,
                record.status.title(),
                str(record.hours),
                record.notes or ''
            ])
        
        record_table = Table(record_data, colWidths=[doc.width/5.0]*5)
        record_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(record_table)
    else:
        elements.append(Paragraph("No attendance records found for this period.", styles["Normal"]))
    
    # Build the PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Create response
    from flask import send_file
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"attendance_report_{employee.username}_{start_date.strftime('%Y%m%d')}.pdf",
        mimetype='application/pdf'
    )

def generate_csv_report(employee, attendance_records, stats, start_date, end_date):
    """Generate a CSV attendance report"""
    # Create a CSV in memory
    temp = tempfile.NamedTemporaryFile(delete=False)
    
    with open(temp.name, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header info
        writer.writerow(['Attendance Report'])
        writer.writerow([f'Employee: {employee.get_display_name()}'])
        writer.writerow([f'Period: {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}'])
        writer.writerow([])
        
        # Summary statistics
        writer.writerow(['SUMMARY STATISTICS'])
        writer.writerow(['Total Days', 'Present', 'Absent', 'Late', 'Excused', 'Attendance Rate'])
        writer.writerow([
            stats['total_days'],
            stats['present_days'],
            stats['absent_days'],
            stats['late_days'],
            stats['excused_days'],
            f"{stats['attendance_rate']:.1f}%"
        ])
        writer.writerow([])
        
        # Detailed records
        writer.writerow(['ATTENDANCE RECORDS'])
        writer.writerow(['Date', 'Teaching Unit', 'Status', 'Hours', 'Notes'])
        
        for record in attendance_records:
            writer.writerow([
                record.date.strftime('%Y-%m-%d'),
                record.teaching_unit.title,
                record.status.title(),
                record.hours,
                record.notes or ''
            ])
    
    # Send file
    from flask import send_file
    return_data = send_file(
        temp.name,
        as_attachment=True,
        download_name=f"attendance_report_{employee.username}_{start_date.strftime('%Y%m%d')}.csv",
        mimetype='text/csv'
    )
    
    # Clean up the temp file
    os.unlink(temp.name)
    
    return return_data

# Add a utility function to get attendance data for payroll
def get_attendance_for_payroll(employee_id, start_date, end_date):
    """
    Get attendance data formatted for payroll calculations
    Returns attendance statistics and potential deductions
    """
    stats = calculate_attendance_stats(employee_id, start_date, end_date)
    
    # Get actual attendance records for the period
    teaching_units = TeachingUnit.query.filter_by(employee_id=employee_id).all()
    
    attendance_records = UnitAttendance.query.filter(
        UnitAttendance.teaching_unit_id.in_([unit.id for unit in teaching_units]),
        UnitAttendance.date.between(start_date, end_date)
    ).order_by(UnitAttendance.date.desc()).all()
    
    # Calculate deductions based on attendance
    deductions = []
    
    # Absence deduction
    if stats['absent_days'] > 0:
        deduction_amount = stats['absent_days'] * 100  # Example: $100 per absence
        deductions.append({
            'type': 'absence',
            'description': f'Absence deduction ({stats["absent_days"]} days)',
            'amount': deduction_amount
        })
    
    # Late arrival deduction (if applicable)
    if stats['late_days'] > 2:  # Example: Allow 2 late arrivals per period
        excess_late = stats['late_days'] - 2
        deduction_amount = excess_late * 25  # Example: $25 per excess late arrival
        deductions.append({
            'type': 'late',
            'description': f'Late arrival deduction ({excess_late} excess days)',
            'amount': deduction_amount
        })
    
    return {
        'stats': stats,
        'deductions': deductions,
        'total_deduction': sum(d['amount'] for d in deductions),
        'records': attendance_records  # Add records to the returned data
    }
