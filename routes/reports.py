"""
Reports routes for the HR system.
Handles report generation and downloads.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, Response, send_file
from flask_login import login_required, current_user
from models import User, EmployeeSalary, EmployeeProfile, LeaveRequest, db
from forms import SalaryReportForm
from utils.decorators import hr_required
import io, csv, tempfile, calendar
from datetime import datetime, timedelta
import random
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/hr/reports')
@login_required
@hr_required
def index():
    """Display HR reports dashboard"""
    return render_template('reports/index.html')

@reports_bp.route('/hr/reports/salary', methods=['GET', 'POST'])
@login_required
@hr_required
def salary_report():
    """Generate faculty/staff compensation reports"""
    form = SalaryReportForm()
    
    if form.validate_on_submit() or request.args.get('export_format'):
        # For GET requests with export_format, use default parameters
        if request.method == 'GET' and request.args.get('export_format'):
            department = request.args.get('department', '')
            date_range = request.args.get('date_range', 'current')
            group_by = request.args.get('group_by', 'none')
            include_inactive = request.args.get('include_inactive', 'false') == 'true'
            export_format = request.args.get('export_format', 'csv')
        else:
            # Use form data for POST requests
            department = form.department.data
            date_range = form.date_range.data
            group_by = form.group_by.data
            include_inactive = form.include_inactive.data
            export_format = form.export_format.data
        
        # Get employees based on filters
        query = User.query
        
        # Filter by department if specified
        if department:
            query = query.filter_by(department=department)
        
        # Get all employees matching filters
        employees = query.all()
        
        # Get salaries for these employees
        data = []
        total_monthly = 0
        total_annual = 0
        
        for employee in employees:
            # Get the current salary (or most recent if no current)
            salary = EmployeeSalary.query.filter_by(employee_id=employee.id).order_by(EmployeeSalary.effective_date.desc()).first()
            
            if salary:
                # Add salary data to the dataset
                salary_data = {
                    'employee_id': employee.id,
                    'name': employee.get_display_name(),
                    'username': employee.username,
                    'department': employee.department.replace('_', ' ').title(),
                    'position': employee.profile.position if hasattr(employee, 'profile') and employee.profile else 'N/A',
                    'salary_type': salary.salary_type,
                    'amount': salary.formatted_amount,
                    'raw_amount': salary.amount,
                    'currency': salary.currency,
                    'monthly_equivalent': salary.amount if salary.salary_type == 'monthly' else salary.amount / 12,
                    'annual_equivalent': salary.amount if salary.salary_type == 'annual' else salary.amount * 12,
                    'effective_date': salary.effective_date.strftime('%Y-%m-%d'),
                    'is_active': salary.is_active
                }
                
                # Update totals
                total_monthly += salary_data['monthly_equivalent']
                total_annual += salary_data['annual_equivalent']
                
                data.append(salary_data)
        
        # Group by if specified
        grouped_data = {}
        if group_by != 'none':
            for item in data:
                group_key = item[group_by]
                if group_key not in grouped_data:
                    grouped_data[group_key] = []
                grouped_data[group_key].append(item)
        else:
            grouped_data = {'all': data}
        
        # Create summary data
        summary = {
            'total_employees': len(data),
            'total_monthly': total_monthly,
            'total_annual': total_annual,
            'departments': len(set(item['department'] for item in data)),
            'avg_monthly': total_monthly / len(data) if data else 0,
            'avg_annual': total_annual / len(data) if data else 0,
        }
        
        # Export to CSV if requested
        if export_format == 'csv':
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                'employee_id', 'name', 'username', 'department', 'position', 
                'salary_type', 'amount', 'raw_amount', 'currency', 'monthly_equivalent', 
                'annual_equivalent', 'effective_date', 'is_active'
            ])
            writer.writeheader()
            writer.writerows(data)
            
            # Create response
            output.seek(0)
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            filename = f"salary_report_{timestamp}.csv"
            
            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={"Content-disposition": f"attachment; filename={filename}"}
            )
            
        # Export to PDF if requested
        elif export_format == 'pdf':
            # Generate a timestamp for the filename
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            filename = f"salary_report_{timestamp}.pdf"
            
            # Create a temporary file path
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_path = temp_file.name
                
            # Use ReportLab to generate PDF
            doc = SimpleDocTemplate(temp_path, pagesize=A4)
            styles = getSampleStyleSheet()
            elements = []
            
            # Title and header
            title_style = ParagraphStyle(
                'Title', 
                parent=styles['Heading1'],
                alignment=TA_CENTER,
                spaceAfter=20
            )
            
            # Add title
            elements.append(Paragraph(f"Employee Salary Report", title_style))
            elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Add summary section
            elements.append(Paragraph("Report Summary", styles['Heading2']))
            summary_data = [
                ["Total Employees", "Total Departments", "Avg Monthly", "Avg Annual"],
                [
                    str(summary['total_employees']),
                    str(summary['departments']),
                    f"${summary['avg_monthly']:.2f}",
                    f"${summary['avg_annual']:.2f}"
                ]
            ]
            
            summary_table = Table(summary_data, colWidths=[100, 100, 100, 100])
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
            
            # Add each group of data
            for group_name, group_items in grouped_data.items():
                # Add a heading for the group
                heading = f"Group: {group_name.title()}" if group_by != 'none' else "All Employees"
                elements.append(Paragraph(heading, styles['Heading3']))
                
                # Create data table
                table_data = [
                    ["Name", "Department", "Position", "Salary", "Annual Equivalent", "Effective Date"]
                ]
                
                # Add rows for this group
                for item in group_items:
                    table_data.append([
                        item['name'],
                        item['department'],
                        item['position'],
                        item['amount'],
                        f"{item['currency']} {item['annual_equivalent']:,.2f}",
                        item['effective_date']
                    ])
                
                # Create table with appropriate styles
                data_table = Table(table_data, colWidths=[100, 80, 80, 80, 80, 80])
                data_table.setStyle(TableStyle([
                    # Header style
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    
                    # Data rows style
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('ALIGN', (3, 1), (4, -1), 'RIGHT'),  # Right-align salary columns
                    
                    # Grid
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    
                    # Add alternating row colors
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                
                elements.append(data_table)
                elements.append(Spacer(1, 20))
            
            # Add footer
            elements.append(Spacer(1, 20))
            footer_text = "Confidential: This document contains sensitive compensation information and should be handled securely."
            elements.append(Paragraph(footer_text, styles['Italic']))
            
            # Build the PDF document
            doc.build(elements)
            
            # Return the PDF file as a response
            return send_file(
                temp_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
        
        # Default to HTML view
        return render_template(
            'reports/salary_report_results.html',
            data=data,
            grouped_data=grouped_data,
            summary=summary,
            form=form,
            now=datetime.now()
        )
    
    return render_template('reports/salary_report.html', form=form)

@reports_bp.route('/hr/reports/employee-demographics', methods=['GET'])
@login_required
@hr_required
def employee_demographics():
    """Generate employee demographics report"""
    # Get filter parameters
    department = request.args.get('department', '')
    date_range = request.args.get('date_range', 'all_time')
    group_by = request.args.get('group_by', 'department')
    
    # Query employees
    query = User.query
    
    # Apply department filter if specified
    if department:
        query = query.filter_by(department=department)
    
    # Get all employees matching filters
    employees = query.all()
    
    # Prepare employee data
    employee_data = []
    departments = {}
    education_levels = {}
    hire_years = {}
    
    # Loop through employees to gather statistics
    for employee in employees:
        # Get employee profile
        profile = employee.profile if hasattr(employee, 'profile') else None
        
        # Calculate tenure (years)
        hire_date = profile.hire_date if profile and profile.hire_date else None
        tenure = 0
        if hire_date:
            tenure = (datetime.now().date() - hire_date).days / 365.25
            
            # Track hire years for hiring trends
            hire_year = hire_date.year
            if hire_year in hire_years:
                hire_years[hire_year] += 1
            else:
                hire_years[hire_year] = 1
        
        # Track education levels - FIX: Handle None values
        education = profile.education_level if profile and hasattr(profile, 'education_level') and profile.education_level is not None else 'Unknown'
        if education in education_levels:
            education_levels[education]['count'] += 1
        else:
            education_levels[education] = {
                'name': education,
                'count': 1
            }
        
        # Track departments
        dept = employee.department
        if dept in departments:
            departments[dept]['count'] += 1
            if tenure > 0:
                departments[dept]['total_tenure'] += tenure
                departments[dept]['employee_with_tenure'] += 1
        else:
            departments[dept] = {
                'name': dept,
                'count': 1,
                'total_tenure': tenure if tenure > 0 else 0,
                'employee_with_tenure': 1 if tenure > 0 else 0,
                'color': f'rgba({random.randint(50, 200)}, {random.randint(50, 200)}, {random.randint(50, 200)}, 0.7)'
            }
        
        # Add employee to dataset
        employee_data.append({
            'name': employee.get_display_name(),
            'department': employee.department,
            'position': profile.position if profile and hasattr(profile, 'position') else 'N/A',
            'hire_date': hire_date.strftime('%Y-%m-%d') if hire_date else 'N/A',
            'tenure': tenure,
            'education': education
        })
    
    # Calculate department stats
    for dept in departments.values():
        if dept['employee_with_tenure'] > 0:
            dept['avg_tenure'] = dept['total_tenure'] / dept['employee_with_tenure']
        else:
            dept['avg_tenure'] = 0
    
    # Prepare data for tenure distribution chart
    tenure_ranges = ['<1 Year', '1-2 Years', '2-5 Years', '5-10 Years', '10+ Years']
    tenure_counts = [0, 0, 0, 0, 0]
    
    # Count employees in each tenure range
    for emp in employee_data:
        tenure = emp['tenure']
        if isinstance(tenure, (int, float)):
            if tenure < 1:
                tenure_counts[0] += 1
            elif tenure < 2:
                tenure_counts[1] += 1
            elif tenure < 5:
                tenure_counts[2] += 1
            elif tenure < 10:
                tenure_counts[3] += 1
            else:
                tenure_counts[4] += 1
    
    # Prepare data for hiring trends chart
    hire_years_sorted = sorted(hire_years.keys())
    hire_counts = [hire_years.get(year, 0) for year in hire_years_sorted]
    
    # Calculate overall statistics
    employee_count = len(employees)
    active_employee_count = sum(1 for e in employees if e.is_active) if hasattr(User, 'is_active') else employee_count
    department_count = len(departments)
    education_count = len(education_levels)
    
    # Calculate average and max tenure
    tenures = [e['tenure'] for e in employee_data if isinstance(e['tenure'], (int, float)) and e['tenure'] > 0]
    avg_tenure = sum(tenures) / len(tenures) if tenures else 0
    max_tenure = max(tenures) if tenures else 0
    
    # Find employee with longest tenure
    longest_tenured_employee = "None"
    if max_tenure > 0:
        for emp in employee_data:
            if emp['tenure'] == max_tenure:
                longest_tenured_employee = emp['name']
                break
    
    # Find largest department
    largest_department = max(departments.values(), key=lambda x: x['count']) if departments else {'name': 'None', 'count': 0}
    largest_department_name = largest_department['name'].replace('_', ' ').title()
    largest_department_count = largest_department['count']
    
    # Find highest education level - FIX: Handle None values in comparison
    if education_levels:
        # Use string representation for comparison to avoid None issues
        highest_degree = max(education_levels.keys(), key=lambda x: str(x))
        highest_degree_count = education_levels[highest_degree]['count']
    else:
        highest_degree = 'None'
        highest_degree_count = 0
    
    # Handle export if requested
    export_format = request.args.get('export_format')
    if export_format:
        include_charts = request.args.get('include_charts', 'true') == 'true'
        include_table = request.args.get('include_table', 'true') == 'true'
        
        # Generate timestamp for the filename
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        
        # CSV Export
        if export_format == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(['Name', 'Department', 'Position', 'Hire Date', 'Tenure (Years)', 'Education'])
            
            # Write data for each employee
            for emp in employee_data:
                writer.writerow([
                    emp['name'],
                    emp['department'].replace('_', ' ').title(),
                    emp['position'],
                    emp['hire_date'],
                    f"{emp['tenure']:.1f}" if isinstance(emp['tenure'], (int, float)) else "N/A",
                    emp['education']
                ])
            
            # Prepare the CSV response
            output.seek(0)
            filename = f"employee_demographics_{timestamp}.csv"
            
            return Response(
                output.getvalue(),
                mimetype="text/csv",
                headers={"Content-disposition": f"attachment; filename={filename}"}
            )
        
        # Excel Export
        elif export_format == 'excel':
            try:
                import pandas as pd
                from io import BytesIO
                
                # Create DataFrame for employee data
                df = pd.DataFrame(employee_data)
                
                # Prepare Excel file in memory
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    # Write employee data
                    df.to_excel(writer, sheet_name='Employees', index=False)
                    
                    # Add Department Analysis sheet
                    dept_df = pd.DataFrame([{
                        'Department': d['name'].replace('_', ' ').title(),
                        'Employee Count': d['count'],
                        'Avg Tenure (Years)': d['avg_tenure']
                    } for d in departments.values()])
                    dept_df.to_excel(writer, sheet_name='Department Analysis', index=False)
                    
                    # Add Education Analysis sheet
                    education_df = pd.DataFrame([{
                        'Education Level': e['name'],
                        'Count': e['count']
                    } for e in education_levels.values()])
                    education_df.to_excel(writer, sheet_name='Education Analysis', index=False)
                    
                    # Add Tenure Distribution sheet
                    tenure_df = pd.DataFrame({
                        'Tenure Range': tenure_ranges,
                        'Count': tenure_counts
                    })
                    tenure_df.to_excel(writer, sheet_name='Tenure Distribution', index=False)
                    
                    # Add Hiring Trends sheet
                    if hire_years_sorted:
                        hiring_df = pd.DataFrame({
                            'Year': hire_years_sorted,
                            'New Hires': hire_counts
                        })
                        hiring_df.to_excel(writer, sheet_name='Hiring Trends', index=False)
                    
                    # Format workbook
                    workbook = writer.book
                    
                    # Add summary sheet
                    summary_sheet = workbook.add_worksheet('Summary')
                    summary_sheet.write(0, 0, 'Employee Demographics Report')
                    summary_sheet.write(1, 0, f'Generated on {datetime.now().strftime("%B %d, %Y at %H:%M:%S")}')
                    
                    summary_sheet.write(3, 0, 'Total Employees')
                    summary_sheet.write(3, 1, employee_count)
                    
                    summary_sheet.write(4, 0, 'Active Employees')
                    summary_sheet.write(4, 1, active_employee_count)
                    
                    summary_sheet.write(5, 0, 'Departments')
                    summary_sheet.write(5, 1, department_count)
                    
                    summary_sheet.write(6, 0, 'Average Tenure')
                    summary_sheet.write(6, 1, f"{avg_tenure:.1f} years")
                    
                    summary_sheet.write(7, 0, 'Longest Tenured Employee')
                    summary_sheet.write(7, 1, f"{longest_tenured_employee} ({max_tenure:.1f} years)")
                
                # Return the Excel file
                output.seek(0)
                filename = f"employee_demographics_{timestamp}.xlsx"
                
                return Response(
                    output.getvalue(),
                    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-disposition": f"attachment; filename={filename}"}
                )
            except ImportError:
                flash("Excel export requires pandas and xlsxwriter packages. Using CSV instead.", "warning")
                # Fallback to CSV if pandas is not available
                return redirect(url_for('reports.employee_demographics', 
                                       export_format='csv', 
                                       include_table=include_table))
        
        # PDF Export
        elif export_format == 'pdf':
            # Generate a timestamp for the filename
            filename = f"employee_demographics_{timestamp}.pdf"
            
            try:
                # Create a temporary file path
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                    temp_path = temp_file.name
                    
                # Use ReportLab to generate PDF
                doc = SimpleDocTemplate(temp_path, pagesize=landscape(A4))
                styles = getSampleStyleSheet()
                elements = []
                
                # Title and header
                title_style = ParagraphStyle(
                    'Title', 
                    parent=styles['Heading1'],
                    alignment=TA_CENTER,
                    spaceAfter=20
                )
                
                # Add title
                elements.append(Paragraph(f"Employee Demographics Report", title_style))
                elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}", styles['Normal']))
                elements.append(Spacer(1, 20))
                
                # Add summary section
                elements.append(Paragraph("Report Summary", styles['Heading2']))
                summary_data = [
                    ["Total Employees", "Active Employees", "Departments", "Average Tenure", "Longest Tenure"],
                    [
                        str(employee_count),
                        str(active_employee_count),
                        str(department_count),
                        f"{avg_tenure:.1f} years",
                        f"{max_tenure:.1f} years ({longest_tenured_employee})"
                    ]
                ]
                
                summary_table = Table(summary_data, colWidths=[100, 100, 100, 100, 150])
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
                
                # Department Distribution Section
                elements.append(Paragraph("Department Distribution", styles['Heading2']))
                
                dept_data = [["Department", "Employee Count", "Average Tenure"]]
                
                # Add department data rows
                for dept in departments.values():
                    dept_data.append([
                        dept['name'].replace('_', ' ').title(),
                        str(dept['count']),
                        f"{dept['avg_tenure']:.1f} years"
                    ])
                
                # Create department table
                dept_table = Table(dept_data, colWidths=[200, 100, 150])
                dept_table.setStyle(TableStyle([
                    # Header style
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    
                    # Data rows style
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Center align numeric columns
                    
                    # Grid
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    
                    # Add alternating row colors
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                
                elements.append(dept_table)
                elements.append(Spacer(1, 20))
                
                # Education Distribution
                elements.append(Paragraph("Education Distribution", styles['Heading2']))
                
                edu_data = [["Education Level", "Count", "Percentage"]]
                
                # Add education data rows
                for edu in education_levels.values():
                    percentage = (edu['count'] / employee_count * 100) if employee_count > 0 else 0
                    edu_data.append([
                        str(edu['name']),
                        str(edu['count']),
                        f"{percentage:.1f}%"
                    ])
                
                # Create education table
                edu_table = Table(edu_data, colWidths=[200, 100, 100])
                edu_table.setStyle(TableStyle([
                    # Header style
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    
                    # Data rows style
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Center align numeric columns
                    
                    # Grid
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    
                    # Add alternating row colors
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                
                elements.append(edu_table)
                elements.append(Spacer(1, 20))
                
                # Include employee details table if requested
                if include_table:
                    elements.append(Paragraph("Employee Details", styles['Heading2']))
                    
                    # Table header
                    employee_table_data = [
                        ["Name", "Department", "Position", "Hire Date", "Tenure", "Education"]
                    ]
                    
                    # Add employee rows
                    for emp in employee_data:
                        employee_table_data.append([
                            emp['name'],
                            emp['department'].replace('_', ' ').title(),
                            emp['position'],
                            emp['hire_date'],
                            f"{emp['tenure']:.1f} years" if isinstance(emp['tenure'], (int, float)) else "N/A",
                            str(emp['education'])
                        ])
                    
                    # Create the table with column widths
                    employee_table = Table(employee_table_data, colWidths=[100, 80, 80, 80, 60, 80])
                    employee_table.setStyle(TableStyle([
                        # Header style
                        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        
                        # Data rows style
                        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                        ('ALIGN', (3, 1), (4, -1), 'CENTER'),  # Center align dates and numeric values
                        
                        # Grid
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        
                        # Add alternating row colors
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                    ]))
                    
                    elements.append(employee_table)
                    elements.append(Spacer(1, 20))
                
                # Add footer
                elements.append(Spacer(1, 20))
                footer_text = "Confidential: This document contains HR information and should be handled according to company policies."
                elements.append(Paragraph(footer_text, styles['Italic']))
                
                # Build the PDF document
                doc.build(elements)
                
                # Return the PDF file as a response
                return send_file(
                    temp_path,
                    mimetype='application/pdf',
                    as_attachment=True,
                    download_name=filename
                )
            except Exception as e:
                flash(f"Error generating PDF: {str(e)}", "danger")
                return redirect(url_for('reports.employee_demographics'))
    
    # Render the template with all the data
    return render_template(
        'reports/employee_demographics.html',
        employees=employee_data,
        departments=list(departments.values()),
        education_levels=list(education_levels.values()),
        tenure_ranges=tenure_ranges,
        tenure_counts=tenure_counts,
        hire_years=hire_years_sorted,
        hire_counts=hire_counts,
        employee_count=employee_count,
        active_employee_count=active_employee_count,
        department_count=department_count,
        education_count=education_count,
        avg_tenure=avg_tenure,
        max_tenure=max_tenure,
        longest_tenured_employee=longest_tenured_employee,
        largest_department_name=largest_department_name,
        largest_department_count=largest_department_count,
        highest_degree=highest_degree,
        highest_degree_count=highest_degree_count
    )

@reports_bp.route('/hr/reports/time-off-analysis', methods=['GET'])
@login_required
@hr_required
def time_off_analysis():
    """Generate time off analysis report"""
    # Get filter parameters
    department = request.args.get('department', '')
    year = request.args.get('year', str(datetime.now().year))
    leave_type = request.args.get('leave_type', '')
    
    try:
        selected_year = int(year)
    except ValueError:
        selected_year = datetime.now().year
    
    # Build query based on filters
    query = LeaveRequest.query.join(LeaveRequest.employee)
    
    # Apply department filter if specified
    if department:
        query = query.filter(User.department == department)
        
    # Apply leave type filter if specified
    if leave_type:
        query = query.filter(LeaveRequest.leave_type == leave_type)
    
    # Filter leaves for the selected year
    start_date = datetime(selected_year, 1, 1).date()
    end_date = datetime(selected_year, 12, 31).date()
    query = query.filter(
        db.or_(
            db.and_(LeaveRequest.start_date >= start_date, LeaveRequest.start_date <= end_date),
            db.and_(LeaveRequest.end_date >= start_date, LeaveRequest.end_date <= end_date)
        )
    )
    
    # Get all leave requests matching filters
    leave_requests = query.all()
    
    # Prepare calendar data
    calendar_data = {}
    for month in range(1, 13):
        # Get the number of days in this month
        _, days_in_month = calendar.monthrange(selected_year, month)
        month_data = []
        
        # Calculate the weekday (0 = Monday) of the first day of the month
        first_day_weekday = datetime(selected_year, month, 1).weekday()
        # Adjust for Sunday as first day (0 = Sunday)
        first_day_weekday = (first_day_weekday + 1) % 7
        
        # Add empty cells for days before the 1st of the month
        for _ in range(first_day_weekday):
            month_data.append({'empty': True})
            
        # Add days of the month
        for day in range(1, days_in_month + 1):
            current_date = datetime(selected_year, month, day).date()
            # Count leaves that include this date
            leave_count = sum(1 for leave in leave_requests if leave.start_date <= current_date <= leave.end_date)
            
            # Determine heat level (0-5) based on leave count
            if leave_count == 0:
                heat_level = 0
            elif leave_count <= 2:
                heat_level = 1
            elif leave_count <= 5:
                heat_level = 2
            elif leave_count <= 9:
                heat_level = 3
            elif leave_count <= 15:
                heat_level = 4
            else:
                heat_level = 5
                
            month_data.append({
                'empty': False,
                'day': day,
                'count': leave_count,
                'heat_level': heat_level
            })
            
        calendar_data[month] = month_data
    
    # Calculate leave statistics
    leave_types = {}
    departments = {}
    monthly_data = [0] * 12  # Initialize with 0 for each month
    total_leave_days = 0
    approved_count = 0
    pending_count = 0
    denied_count = 0
    
    # Process each leave request
    leaves_data = []
    for leave in leave_requests:
        # Calculate leave duration
        duration = (leave.end_date - leave.start_date).days + 1
        total_leave_days += duration
        
        # Count by status
        if leave.status == 'approved':
            approved_count += 1
        elif leave.status == 'pending':
            pending_count += 1
        elif leave.status == 'denied':
            denied_count += 1
            
        # Aggregate by leave type
        if leave.leave_type in leave_types:
            leave_types[leave.leave_type]['count'] += 1
            leave_types[leave.leave_type]['days'] += duration
        else:
            leave_types[leave.leave_type] = {
                'name': leave.leave_type,
                'count': 1,
                'days': duration
            }
            
        # Aggregate by department
        dept = leave.employee.department
        if dept in departments:
            departments[dept]['count'] += 1
            departments[dept]['days'] += duration
        else:
            departments[dept] = {
                'name': dept,
                'count': 1,
                'days': duration,
                'employees': set()
            }
        departments[dept]['employees'].add(leave.employee_id)
        
        # Add to monthly data
        # Consider spreading the leave across multiple months if it spans months
        start_month = leave.start_date.month - 1  # 0-based index
        end_month = leave.end_date.month - 1  # 0-based index
        
        if start_month == end_month:
            # Leave is within one month
            monthly_data[start_month] += duration
        else:
            # Leave spans multiple months
            for month_idx in range(start_month, end_month + 1):
                # Calculate days in this specific month
                if month_idx == start_month:
                    # First month - days from start to end of month
                    month_end = datetime(selected_year, month_idx + 1, calendar.monthrange(selected_year, month_idx + 1)[1]).date()
                    days_in_this_month = (month_end - leave.start_date).days + 1
                elif month_idx == end_month:
                    # Last month - days from start of month to end
                    month_start = datetime(selected_year, month_idx + 1, 1).date()
                    days_in_this_month = (leave.end_date - month_start).days + 1
                else:
                    # Middle month - all days in month
                    days_in_this_month = calendar.monthrange(selected_year, month_idx + 1)[1]
                    
                monthly_data[month_idx] += days_in_this_month
                
        # Add leave to the detailed list
        leaves_data.append({
            'employee_name': leave.employee.get_display_name(),
            'department': leave.employee.department.replace('_', ' ').title(),
            'leave_type': leave.leave_type.replace('_', ' ').title(),
            'start_date': leave.start_date.strftime('%Y-%m-%d'),
            'end_date': leave.end_date.strftime('%Y-%m-%d'),
            'duration': duration,
            'status': leave.status
        })
        
    # Calculate average leave days per employee for departments
    for dept_data in departments.values():
        employee_count = len(dept_data['employees'])
        dept_data['avg_days'] = dept_data['days'] / employee_count if employee_count > 0 else 0
        dept_data['employee_count'] = employee_count
    
    # Convert to lists for the template
    leave_types_list = list(leave_types.values())
    departments_list = list(departments.values())
    
    # Prepare month names for chart
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Export format handling
    export_format = request.args.get('export_format')
    if export_format:
        include_charts = request.args.get('include_charts', 'true') == 'true'
        include_calendar = request.args.get('include_calendar', 'true') == 'true'
        include_table = request.args.get('include_table', 'true') == 'true'
        
        # Redirect to the export endpoint with the same parameters
        return redirect(url_for('reports.export_time_off_analysis', 
                               year=selected_year,
                               department=department,
                               leave_type=leave_type,
                               export_format=export_format,
                               include_charts=include_charts,
                               include_calendar=include_calendar,
                               include_table=include_table))
    
    # Render the template with all the data
    return render_template(
        'reports/time_off_analysis.html',
        leaves=leaves_data,
        january_days=calendar_data[1],
        february_days=calendar_data[2],
        march_days=calendar_data[3],
        april_days=calendar_data[4],
        may_days=calendar_data[5],
        june_days=calendar_data[6],
        july_days=calendar_data[7],
        august_days=calendar_data[8],
        september_days=calendar_data[9],
        october_days=calendar_data[10],
        november_days=calendar_data[11],
        december_days=calendar_data[12],
        selected_year=selected_year,
        current_year=datetime.now().year,
        leave_types=leave_types_list,
        departments=departments_list,
        monthly_data=monthly_data,
        month_names=month_names,
        approved_leave_count=approved_count,
        pending_leave_count=pending_count,
        denied_leave_count=denied_count,
        total_leave_days=total_leave_days
    )

@reports_bp.route('/hr/reports/time-off-analysis/export', methods=['GET'])
@login_required
@hr_required
def export_time_off_analysis():
    """Export time off analysis report in various formats"""
    # Get filter parameters
    department = request.args.get('department', '')
    year = request.args.get('year', str(datetime.now().year))
    leave_type = request.args.get('leave_type', '')
    export_format = request.args.get('export_format', 'csv')
    include_charts = request.args.get('include_charts', 'true') == 'true'
    include_calendar = request.args.get('include_calendar', 'true') == 'true'
    include_table = request.args.get('include_table', 'true') == 'true'
    
    try:
        selected_year = int(year)
    except ValueError:
        selected_year = datetime.now().year
    
    # Build query based on filters
    query = LeaveRequest.query.join(LeaveRequest.employee)
    
    # Apply department filter if specified
    if department:
        query = query.filter(User.department == department)
        
    # Apply leave type filter if specified
    if leave_type:
        query = query.filter(LeaveRequest.leave_type == leave_type)
    
    # Filter leaves for the selected year
    start_date = datetime(selected_year, 1, 1).date()
    end_date = datetime(selected_year, 12, 31).date()
    query = query.filter(
        db.or_(
            db.and_(LeaveRequest.start_date >= start_date, LeaveRequest.start_date <= end_date),
            db.and_(LeaveRequest.end_date >= start_date, LeaveRequest.end_date <= end_date)
        )
    )
    
    # Get all leave requests matching filters
    leave_requests = query.all()
    
    # Process and aggregate leave data
    leave_types = {}
    departments = {}
    monthly_data = [0] * 12  # Initialize with 0 for each month
    total_leave_days = 0
    approved_count = 0
    pending_count = 0
    denied_count = 0
    
    # Process each leave request
    leaves_data = []
    for leave in leave_requests:
        # Calculate leave duration
        duration = (leave.end_date - leave.start_date).days + 1
        total_leave_days += duration
        
        # Count by status
        if leave.status == 'approved':
            approved_count += 1
        elif leave.status == 'pending':
            pending_count += 1
        elif leave.status == 'denied':
            denied_count += 1
            
        # Aggregate by leave type
        if leave.leave_type in leave_types:
            leave_types[leave.leave_type]['count'] += 1
            leave_types[leave.leave_type]['days'] += duration
        else:
            leave_types[leave.leave_type] = {
                'name': leave.leave_type,
                'count': 1,
                'days': duration
            }
            
        # Aggregate by department
        dept = leave.employee.department
        if dept in departments:
            departments[dept]['count'] += 1
            departments[dept]['days'] += duration
        else:
            departments[dept] = {
                'name': dept,
                'count': 1,
                'days': duration,
                'employees': set()
            }
        departments[dept]['employees'].add(leave.employee_id)
        
        # Add to monthly data
        # Consider spreading the leave across multiple months if it spans months
        start_month = leave.start_date.month - 1  # 0-based index
        end_month = leave.end_date.month - 1  # 0-based index
        
        if start_month == end_month:
            # Leave is within one month
            monthly_data[start_month] += duration
        else:
            # Leave spans multiple months
            for month_idx in range(start_month, end_month + 1):
                # Calculate days in this specific month
                if month_idx == start_month:
                    # First month - days from start to end of month
                    month_end = datetime(selected_year, month_idx + 1, calendar.monthrange(selected_year, month_idx + 1)[1]).date()
                    days_in_this_month = (month_end - leave.start_date).days + 1
                elif month_idx == end_month:
                    # Last month - days from start of month to end
                    month_start = datetime(selected_year, month_idx + 1, 1).date()
                    days_in_this_month = (leave.end_date - month_start).days + 1
                else:
                    # Middle month - all days in month
                    days_in_this_month = calendar.monthrange(selected_year, month_idx + 1)[1]
                    
                monthly_data[month_idx] += days_in_this_month
                
        # Add leave to the detailed list
        leaves_data.append({
            'employee_name': leave.employee.get_display_name(),
            'department': leave.employee.department.replace('_', ' ').title(),
            'leave_type': leave.leave_type.replace('_', ' ').title(),
            'start_date': leave.start_date.strftime('%Y-%m-%d'),
            'end_date': leave.end_date.strftime('%Y-%m-%d'),
            'duration': duration,
            'status': leave.status
        })
        
    # Calculate average leave days per employee for departments
    for dept_data in departments.values():
        employee_count = len(dept_data['employees'])
        dept_data['avg_days'] = dept_data['days'] / employee_count if employee_count > 0 else 0
        dept_data['employee_count'] = employee_count
    
    # CSV Export
    if export_format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Employee', 'Department', 'Leave Type', 'Start Date', 'End Date', 'Duration (Days)', 'Status'])
        
        # Write data for each leave request
        for leave in leaves_data:
            writer.writerow([
                leave['employee_name'],
                leave['department'],
                leave['leave_type'],
                leave['start_date'],
                leave['end_date'],
                leave['duration'],
                leave['status'].capitalize()
            ])
        
        # Prepare CSV response
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        filename = f"time_off_analysis_{selected_year}_{timestamp}.csv"
        
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
    
    # Excel Export
    elif export_format == 'excel':
        try:
            import pandas as pd
            from io import BytesIO
            
            # Create DataFrame for leave data
            df = pd.DataFrame(leaves_data)
            
            # Prepare Excel file in memory
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Write leave data
                df.to_excel(writer, sheet_name='Leave Requests', index=False)
                
                # Add Department Analysis sheet
                dept_df = pd.DataFrame([{
                    'Department': d['name'].replace('_', ' ').title(),
                    'Leave Count': d['count'],
                    'Total Days': d['days'],
                    'Avg Days per Employee': d['avg_days'],
                    'Employee Count': d['employee_count']
                } for d in departments.values()])
                dept_df.to_excel(writer, sheet_name='Department Analysis', index=False)
                
                # Add Leave Type Analysis sheet
                leave_type_df = pd.DataFrame([{
                    'Leave Type': lt['name'].replace('_', ' ').title(),
                    'Count': lt['count'],
                    'Total Days': lt['days']
                } for lt in leave_types.values()])
                leave_type_df.to_excel(writer, sheet_name='Leave Type Analysis', index=False)
                
                # Add Monthly Distribution sheet
                month_names = ['January', 'February', 'March', 'April', 'May', 'June', 
                              'July', 'August', 'September', 'October', 'November', 'December']
                monthly_df = pd.DataFrame({
                    'Month': month_names,
                    'Leave Days': monthly_data
                })
                monthly_df.to_excel(writer, sheet_name='Monthly Distribution', index=False)
                
                # Add Status Summary sheet
                status_df = pd.DataFrame({
                    'Status': ['Approved', 'Pending', 'Denied', 'Total'],
                    'Count': [approved_count, pending_count, denied_count, 
                             approved_count + pending_count + denied_count]
                })
                status_df.to_excel(writer, sheet_name='Status Summary', index=False)
                
                # Format workbook
                workbook = writer.book
                
                # Add summary sheet
                summary_sheet = workbook.add_worksheet('Summary')
                summary_sheet.write(0, 0, 'Time Off Analysis Report')
                summary_sheet.write(1, 0, f'Year: {selected_year}')
                summary_sheet.write(2, 0, f'Generated on {datetime.now().strftime("%B %d, %Y at %H:%M:%S")}')
                
                summary_sheet.write(4, 0, 'Total Leave Requests')
                summary_sheet.write(4, 1, len(leaves_data))
                
                summary_sheet.write(5, 0, 'Total Leave Days')
                summary_sheet.write(5, 1, total_leave_days)
                
                summary_sheet.write(6, 0, 'Approved Leave Requests')
                summary_sheet.write(6, 1, approved_count)
                
                summary_sheet.write(7, 0, 'Pending Leave Requests')
                summary_sheet.write(7, 1, pending_count)
                
                summary_sheet.write(8, 0, 'Denied Leave Requests')
                summary_sheet.write(8, 1, denied_count)
            
            # Return the Excel file
            output.seek(0)
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            filename = f"time_off_analysis_{selected_year}_{timestamp}.xlsx"
            
            return Response(
                output.getvalue(),
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-disposition": f"attachment; filename={filename}"}
            )
        except ImportError:
            flash("Excel export requires pandas and xlsxwriter packages. Using CSV instead.", "warning")
            # Fallback to CSV if pandas is not available
            return redirect(url_for('reports.export_time_off_analysis', 
                                    year=selected_year,
                                    department=department,
                                    leave_type=leave_type,
                                    export_format='csv'))
    
    # PDF Export
    elif export_format == 'pdf':
        # Generate a timestamp for the filename
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        filename = f"time_off_analysis_{selected_year}_{timestamp}.pdf"
        
        try:
            # Create a temporary file path
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_path = temp_file.name
                
            # Use ReportLab to generate PDF
            doc = SimpleDocTemplate(temp_path, pagesize=landscape(A4))
            styles = getSampleStyleSheet()
            elements = []
            
            # Title and header
            title_style = ParagraphStyle(
                'Title', 
                parent=styles['Heading1'],
                alignment=TA_CENTER,
                spaceAfter=20
            )
            
            # Add title
            elements.append(Paragraph(f"Time Off Analysis Report - {selected_year}", title_style))
            elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Add summary section
            elements.append(Paragraph("Report Summary", styles['Heading2']))
            summary_data = [
                ["Total Leave Requests", "Total Leave Days", "Approved", "Pending", "Denied"],
                [
                    str(len(leaves_data)),
                    str(total_leave_days),
                    str(approved_count),
                    str(pending_count),
                    str(denied_count)
                ]
            ]
            
            summary_table = Table(summary_data, colWidths=[120, 100, 100, 100, 100])
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
            
            # Leave Type Distribution Section
            elements.append(Paragraph("Leave Type Distribution", styles['Heading2']))
            
            leave_type_data = [["Leave Type", "Count", "Total Days"]]
            
            # Add leave type data rows
            for lt in leave_types.values():
                leave_type_data.append([
                    lt['name'].replace('_', ' ').title(),
                    str(lt['count']),
                    str(lt['days'])
                ])
            
            # Create leave type table
            leave_type_table = Table(leave_type_data, colWidths=[200, 100, 100])
            leave_type_table.setStyle(TableStyle([
                # Header style
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                
                # Data rows style
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Center align numeric columns
                
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                
                # Add alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            elements.append(leave_type_table)
            elements.append(Spacer(1, 20))
            
            # Department Analysis
            elements.append(Paragraph("Department Analysis", styles['Heading2']))
            
            dept_data = [["Department", "Leave Count", "Total Days", "Avg Days per Employee"]]
            
            # Add department data rows
            for dept in departments.values():
                dept_data.append([
                    dept['name'].replace('_', ' ').title(),
                    str(dept['count']),
                    str(dept['days']),
                    f"{dept['avg_days']:.1f}"
                ])
            
            # Create department table
            dept_table = Table(dept_data, colWidths=[200, 100, 100, 150])
            dept_table.setStyle(TableStyle([
                # Header style
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                
                # Data rows style
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Center align numeric columns
                
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                
                # Add alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            elements.append(dept_table)
            elements.append(Spacer(1, 20))
            
            # Monthly Distribution
            elements.append(Paragraph("Monthly Leave Distribution", styles['Heading2']))
            
            month_names = ['January', 'February', 'March', 'April', 'May', 'June', 
                          'July', 'August', 'September', 'October', 'November', 'December']
            
            month_data = [["Month", "Leave Days"]]
            
            # Add month data rows
            for i, month in enumerate(month_names):
                month_data.append([
                    month,
                    str(monthly_data[i])
                ])
            
            # Create month table
            month_table = Table(month_data, colWidths=[200, 100])
            month_table.setStyle(TableStyle([
                # Header style
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                
                # Data rows style
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Center align numeric columns
                
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                
                # Add alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            elements.append(month_table)
            elements.append(Spacer(1, 20))
            
            # Include detailed leave table if requested
            if include_table:
                elements.append(Paragraph("Leave Request Details", styles['Heading2']))
                
                # Table header
                leave_details_data = [
                    ["Employee", "Department", "Leave Type", "Start Date", "End Date", "Duration", "Status"]
                ]
                
                # Add leave rows
                for leave in leaves_data:
                    leave_details_data.append([
                        leave['employee_name'],
                        leave['department'],
                        leave['leave_type'],
                        leave['start_date'],
                        leave['end_date'],
                        f"{leave['duration']} days",
                        leave['status'].capitalize()
                    ])
                
                # Create the table with column widths
                leave_details_table = Table(leave_details_data, colWidths=[100, 80, 80, 70, 70, 60, 60])
                leave_details_table.setStyle(TableStyle([
                    # Header style
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    
                    # Data rows style
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('ALIGN', (3, 1), (5, -1), 'CENTER'),  # Center align dates and numeric values
                    
                    # Grid
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    
                    # Add alternating row colors
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                
                elements.append(leave_details_table)
                elements.append(Spacer(1, 20))
            
            # Add footer
            elements.append(Spacer(1, 20))
            footer_text = "Confidential: This document contains HR information and should be handled according to company policies."
            elements.append(Paragraph(footer_text, styles['Italic']))
            
            # Build the PDF document
            doc.build(elements)
            
            # Return the PDF file as a response
            return send_file(
                temp_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
        except Exception as e:
            flash(f"Error generating PDF: {str(e)}", "danger")
            return redirect(url_for('reports.time_off_analysis', year=selected_year))
    
    # Default response if no export format is specified
    return redirect(url_for('reports.time_off_analysis', year=selected_year))

@reports_bp.route('/hr/reports/training-analytics', methods=['GET'])
@login_required
@hr_required
def training_analytics():
    """Generate training program analytics report"""
    # Get filter parameters
    department = request.args.get('department', '')
    time_period = request.args.get('time_period', 'all')
    category = request.args.get('category', '')
    
    # Placeholder implementation - this should be expanded with actual data
    from models import TrainingProgram, TrainingEnrollment, User
    
    # Base query for training programs
    training_programs = TrainingProgram.query.all()
    
    # Default empty data structures for template
    total_programs = len(training_programs)
    completed_programs = 0
    active_programs = 0
    upcoming_programs = 0
    
    total_enrollments = 0
    total_completions = 0
    total_capacity = 0
    
    departments = {}
    categories = {}
    rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    monthly_enrollments = [0] * 12  # For tracking enrollments by month
    
    # Basic values for the template
    enrollment_rate = 0
    completion_rate = 0
    avg_rating = 0
    
    # Get available categories for filter dropdown
    available_categories = []
    
    # Handle export if requested
    export_format = request.args.get('export_format')
    if export_format:
        # Export handling code would go here
        pass
    
    # Render the template with placeholders
    return render_template(
        'reports/training_analytics.html',
        training_programs=training_programs,
        total_programs=total_programs,
        completed_programs=completed_programs,
        active_programs=active_programs,
        upcoming_programs=upcoming_programs,
        total_enrollments=total_enrollments,
        total_completions=total_completions,
        total_capacity=total_capacity,
        enrollment_rate=enrollment_rate,
        completion_rate=completion_rate,
        departments=list(departments.values()),
        categories=list(categories.values()),
        rating_distribution=rating_distribution,
        avg_rating=avg_rating,
        monthly_enrollments=monthly_enrollments,
        month_names=['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        available_categories=available_categories
    )

@reports_bp.route('/hr/reports/training-analytics/export', methods=['GET'])
@login_required
@hr_required
def export_training_analytics():
    """Export training analytics report in various formats"""
    # Get filter parameters
    department = request.args.get('department', '')
    time_period = request.args.get('time_period', 'all')
    category = request.args.get('category', '')
    export_format = request.args.get('export_format', 'csv')
    include_charts = request.args.get('include_charts', 'true') == 'true'
    include_details = request.args.get('include_details', 'true') == 'true'
    
    # Placeholder implementation - this should be expanded with actual data
    from models import TrainingProgram, TrainingEnrollment, User
    
    # Base query for training programs
    training_programs = TrainingProgram.query.all()
    
    # Default empty data structures for template
    total_programs = len(training_programs)
    completed_programs = 0
    active_programs = 0
    upcoming_programs = 0
    
    total_enrollments = 0
    total_completions = 0
    total_capacity = 0
    
    departments = {}
    categories = {}
    rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    monthly_enrollments = [0] * 12  # For tracking enrollments by month
    
    # Basic values for the template
    enrollment_rate = 0
    completion_rate = 0
    avg_rating = 0
    
    # CSV Export
    if export_format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Title', 'Category', 'Instructor', 'Status', 'Start Date', 'End Date', 
                         'Enrolled', 'Max Participants', 'Completion Rate', 'Avg Rating'])
        
        # Write data for each training program
        for program in training_programs:
            writer.writerow([
                program.title,
                program.category.replace('_', ' ').title(),
                program.instructor,
                program.status.replace('-', ' ').title(),
                program.start_date.strftime('%Y-%m-%d'),
                program.end_date.strftime('%Y-%m-%d'),
                program.enrolled_count if hasattr(program, 'enrolled_count') else 0,
                program.max_participants,
                f"{program.completion_rate:.1f}%" if hasattr(program, 'completion_rate') else "N/A",
                f"{program.avg_rating:.1f}" if hasattr(program, 'avg_rating') and program.avg_rating else "N/A"
            ])
        
        # Prepare CSV response
        output.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        filename = f"training_analytics_{timestamp}.csv"
        
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename={filename}"}
        )
    
    # Excel Export
    elif export_format == 'excel':
        try:
            import pandas as pd
            from io import BytesIO
            
            # Create DataFrame for training data
            program_data = []
            for program in training_programs:
                program_data.append({
                    'Title': program.title,
                    'Category': program.category.replace('_', ' ').title(),
                    'Instructor': program.instructor,
                    'Status': program.status.replace('-', ' ').title(),
                    'Start Date': program.start_date,
                    'End Date': program.end_date,
                    'Enrolled': program.enrolled_count if hasattr(program, 'enrolled_count') else 0,
                    'Max Participants': program.max_participants,
                    'Completion Rate': f"{program.completion_rate:.1f}%" if hasattr(program, 'completion_rate') else "N/A",
                    'Avg Rating': program.avg_rating if hasattr(program, 'avg_rating') and program.avg_rating else "N/A"
                })
            
            df = pd.DataFrame(program_data)
            
            # Prepare Excel file in memory
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Write program data
                df.to_excel(writer, sheet_name='Training Programs', index=False)
                
                # Add Department Analysis sheet if we have department data
                if departments:
                    dept_df = pd.DataFrame([{
                        'Department': d['name'].replace('_', ' ').title(),
                        'Enrollments': d.get('enrollments', 0),
                        'Completions': d.get('completions', 0),
                        'Completion Rate': f"{(d.get('completions', 0) / d.get('enrollments', 1) * 100):.1f}%" if d.get('enrollments', 0) > 0 else "0%"
                    } for d in departments.values()])
                    dept_df.to_excel(writer, sheet_name='Department Analysis', index=False)
                
                # Add Category Analysis sheet
                if categories:
                    cat_df = pd.DataFrame([{
                        'Category': c['name'].replace('_', ' ').title(),
                        'Count': c.get('count', 0),
                        'Enrollments': c.get('enrollments', 0)
                    } for c in categories.values()])
                    cat_df.to_excel(writer, sheet_name='Category Analysis', index=False)
                
                # Add Ratings Distribution sheet
                if sum(rating_distribution.values()) > 0:
                    rating_df = pd.DataFrame({
                        'Rating': list(rating_distribution.keys()),
                        'Count': list(rating_distribution.values())
                    })
                    rating_df.to_excel(writer, sheet_name='Rating Distribution', index=False)
                
                # Format workbook
                workbook = writer.book
                
                # Add summary sheet
                summary_sheet = workbook.add_worksheet('Summary')
                summary_sheet.write(0, 0, 'Training Analytics Report')
                summary_sheet.write(1, 0, f'Generated on {datetime.now().strftime("%B %d, %Y at %H:%M:%S")}')
                
                summary_sheet.write(3, 0, 'Total Programs')
                summary_sheet.write(3, 1, total_programs)
                
                summary_sheet.write(4, 0, 'Completed Programs')
                summary_sheet.write(4, 1, completed_programs)
                
                summary_sheet.write(5, 0, 'Active Programs')
                summary_sheet.write(5, 1, active_programs)
                
                summary_sheet.write(6, 0, 'Upcoming Programs')
                summary_sheet.write(6, 1, upcoming_programs)
                
                summary_sheet.write(8, 0, 'Total Enrollments')
                summary_sheet.write(8, 1, total_enrollments)
                
                summary_sheet.write(9, 0, 'Average Rating')
                summary_sheet.write(9, 1, f"{avg_rating:.1f}")
            
            # Return the Excel file
            output.seek(0)
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            filename = f"training_analytics_{timestamp}.xlsx"
            
            return Response(
                output.getvalue(),
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-disposition": f"attachment; filename={filename}"}
            )
        except ImportError:
            flash("Excel export requires pandas and xlsxwriter packages. Using CSV instead.", "warning")
            # Fallback to CSV if pandas is not available
            return redirect(url_for('reports.export_training_analytics', 
                                   export_format='csv'))
    
    # PDF Export
    elif export_format == 'pdf':
        # Generate a timestamp for the filename
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        filename = f"training_analytics_{timestamp}.pdf"
        
        try:
            # Create a temporary file path
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
                temp_path = temp_file.name
                
            # Use ReportLab to generate PDF
            doc = SimpleDocTemplate(temp_path, pagesize=landscape(A4))
            styles = getSampleStyleSheet()
            elements = []
            
            # Title and header
            title_style = ParagraphStyle(
                'Title', 
                parent=styles['Heading1'],
                alignment=TA_CENTER,
                spaceAfter=20
            )
            
            # Add title
            elements.append(Paragraph(f"Training Analytics Report", title_style))
            elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}", styles['Normal']))
            elements.append(Spacer(1, 20))
            
            # Add summary section
            elements.append(Paragraph("Report Summary", styles['Heading2']))
            summary_data = [
                ["Total Programs", "Completed", "Active", "Upcoming", "Total Enrollments", "Avg Rating"],
                [
                    str(total_programs),
                    str(completed_programs),
                    str(active_programs),
                    str(upcoming_programs),
                    str(total_enrollments),
                    f"{avg_rating:.1f}"
                ]
            ]
            
            summary_table = Table(summary_data, colWidths=[100, 80, 80, 80, 100, 80])
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
            
            # Include detailed training programs table if requested
            if include_details:
                elements.append(Paragraph("Training Programs", styles['Heading2']))
                
                # Table header
                program_table_data = [
                    ["Title", "Category", "Instructor", "Status", "Start Date", "End Date", "Enrolled", "Completion"]
                ]
                
                # Add program rows
                for program in training_programs:
                    program_table_data.append([
                        program.title,
                        program.category.replace('_', ' ').title(),
                        program.instructor,
                        program.status.replace('-', ' ').title(),
                        program.start_date.strftime('%Y-%m-%d'),
                        program.end_date.strftime('%Y-%m-%d'),
                        f"{program.enrolled_count if hasattr(program, 'enrolled_count') else 0}"
                        + (f"/{program.max_participants}" if program.max_participants > 0 else ""),
                        f"{program.completion_rate:.1f}%" if hasattr(program, 'completion_rate') else "N/A"
                    ])
                
                # Create the table with column widths
                program_table = Table(program_table_data, colWidths=[120, 80, 80, 70, 70, 70, 60, 60])
                program_table.setStyle(TableStyle([
                    # Header style
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    
                    # Data rows style
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('ALIGN', (3, 1), (7, -1), 'CENTER'),  # Center align dates and numeric values
                    
                    # Grid
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    
                    # Add alternating row colors
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
                ]))
                
                elements.append(program_table)
                elements.append(Spacer(1, 20))
            
            # Add footer
            elements.append(Spacer(1, 20))
            footer_text = "Confidential: This document contains HR information and should be handled according to company policies."
            elements.append(Paragraph(footer_text, styles['Italic']))
            
            # Build the PDF document
            doc.build(elements)
            
            # Return the PDF file as a response
            return send_file(
                temp_path,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=filename
            )
        except Exception as e:
            flash(f"Error generating PDF: {str(e)}", "danger")
            return redirect(url_for('reports.training_analytics'))
    
    # Default response if no export format is specified
    return redirect(url_for('reports.training_analytics'))
