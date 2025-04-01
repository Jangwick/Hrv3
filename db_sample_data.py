#!/usr/bin/env python3
"""
Sample data generator for the School HR System database.
This script inserts sample data for users with IDs 1, 2, and 3 into multiple tables.
"""
import sqlite3
import random
from datetime import datetime, timedelta
import os

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance/school_hr.db')

# Connect to the database
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Enable foreign keys
cursor.execute('PRAGMA foreign_keys = ON')

# Helper functions
def random_date(start_date, end_date):
    """Generate a random date between start_date and end_date"""
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    return start_date + timedelta(days=random_days)

def format_date(date):
    """Format date object to string"""
    return date.strftime('%Y-%m-%d')

def now():
    """Get current datetime as string"""
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def delete_existing_data():
    """Delete existing sample data to avoid conflicts"""
    tables = [
        'employee_salary', 'leave_request', 'payroll', 'payroll_deduction', 
        'payroll_unit', 'teaching_unit', 'teaching_unit_relationships', 
        'training_enrollment', 'training_program', 'unit_attendance'
    ]
    
    for table in tables:
        try:
            cursor.execute(f"DELETE FROM {table} WHERE employee_id IN (1, 2, 3) OR created_by IN (1, 2, 3)")
        except sqlite3.Error as e:
            print(f"Error clearing {table}: {e}")
    
    conn.commit()
    print("Cleared existing sample data")

# Define date ranges
today = datetime.now().date()
one_year_ago = today - timedelta(days=365)
one_month_ago = today - timedelta(days=30)
one_week_ago = today - timedelta(days=7)
one_month_ahead = today + timedelta(days=30)
three_months_ahead = today + timedelta(days=90)
six_months_ahead = today + timedelta(days=180)

# Sample data for each table
print("Generating sample data...")

# 1. employee_salary
print("Inserting employee_salary data...")
salary_data = [
    # (employee_id, amount, currency, salary_type, contract_type, effective_date, end_date, is_active, created_by, created_at)
    (1, 75000.00, 'USD', 'annual', 'full_time', format_date(one_year_ago), None, 1, 3, now()),
    (2, 6000.00, 'USD', 'monthly', 'full_time', format_date(one_year_ago), None, 1, 3, now()),
    (3, 25.00, 'USD', 'hourly', 'part_time', format_date(one_year_ago), None, 1, 3, now())
]

for salary in salary_data:
    cursor.execute('''
    INSERT INTO employee_salary 
    (employee_id, amount, currency, salary_type, contract_type, effective_date, end_date, is_active, created_by, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', salary)

# 2. leave_request
print("Inserting leave_request data...")
leave_statuses = ['pending', 'approved', 'rejected']
leave_types = ['vacation', 'sick', 'personal', 'bereavement', 'professional']

for employee_id in [1, 2, 3]:
    # Create 5 leave requests per employee
    for i in range(5):
        # Create some past leaves and some future leaves
        if i < 3:
            # Past leaves
            start_date = random_date(one_year_ago, one_week_ago)
            end_date = start_date + timedelta(days=random.randint(1, 5))
            status = random.choice(['approved', 'rejected'])
            # For the reason, calculate duration_days but don't include it in the INSERT
            duration_days = (end_date - start_date).days + 1
        else:
            # Future leaves or pending
            start_date = random_date(today, one_month_ahead)
            end_date = start_date + timedelta(days=random.randint(1, 5))
            status = 'pending'
            # For the reason, calculate duration_days but don't include it in the INSERT
            duration_days = (end_date - start_date).days + 1
        
        leave_type = random.choice(leave_types)
        
        # Remove created_by from the tuple
        leave_request = (
            employee_id,                 # employee_id
            leave_type,                  # leave_type
            format_date(start_date),     # start_date
            format_date(end_date),       # end_date
            f"Need {leave_type} leave for {duration_days} days",  # reason
            status,                      # status
            now(),                       # created_at
        )
        
        # Remove created_by from the SQL statement
        cursor.execute('''
        INSERT INTO leave_request
        (employee_id, leave_type, start_date, end_date, reason, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', leave_request)

# 3. payroll records
print("Inserting payroll data...")
# Create past payroll records for each employee
for employee_id in [1, 2, 3]:
    for i in range(6):  # 6 months of payroll history
        period_start = one_year_ago + timedelta(days=i*30)
        period_end = period_start + timedelta(days=29)
        
        # Base pay based on employee type
        if employee_id == 1:  # Annual salary
            base_pay = 75000.00 / 12  # Monthly portion of annual salary
            unit_pay = random.uniform(500, 1500)
        elif employee_id == 2:  # Monthly salary
            base_pay = 6000.00
            unit_pay = random.uniform(300, 800) 
        else:  # Hourly
            base_pay = 25.00 * 80  # 80 hours per month
            unit_pay = random.uniform(200, 600)
        
        deductions = random.uniform(200, 500)
        # Remove tax_deduction calculation and use directly in net_pay
        net_pay = base_pay + unit_pay - deductions
        
        payroll = (
            employee_id,  # employee_id
            format_date(period_start),  # period_start
            format_date(period_end),  # period_end
            base_pay,  # base_pay
            unit_pay,  # unit_pay
            deductions,  # deductions
            # Removed tax_deduction field
            net_pay,  # net_pay
            'direct_deposit',  # payment_method
            'completed',  # status
            f"Monthly payroll for period {format_date(period_start)} - {format_date(period_end)}",  # notes
            3,  # created_by (HR)
            now(),  # created_at
        )
        
        cursor.execute('''
        INSERT INTO payroll
        (employee_id, period_start, period_end, base_pay, unit_pay, deductions, net_pay, payment_method, status, notes, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', payroll)
        
        # Get the inserted payroll ID
        payroll_id = cursor.lastrowid
        
        # 4. payroll_deduction
        # Add 2-3 deductions for each payroll
        for j in range(random.randint(2, 3)):
            deduction_types = ['health_insurance', 'retirement', 'other']
            deduction_type = random.choice(deduction_types)
            amount = random.uniform(50, 200)
            
            deduction = (
                payroll_id,  # payroll_id
                deduction_type,  # deduction_type
                f"{deduction_type.replace('_', ' ').title()} contribution",  # description
                amount,  # amount
                now(),  # created_at
            )
            
            cursor.execute('''
            INSERT INTO payroll_deduction
            (payroll_id, deduction_type, description, amount, created_at)
            VALUES (?, ?, ?, ?, ?)
            ''', deduction)

# 6. teaching_unit
print("Inserting teaching_unit data...")
unit_titles = [
    "Mathematics 101", "Advanced Algebra", "Calculus Fundamentals",
    "World History", "American Literature", "Physics Basics",
    "Chemistry Lab", "Computer Science Principles", "Art History",
    "Music Theory", "Psychology 101", "Environmental Science"
]

unit_codes = [
    "MATH101", "ALG201", "CALC101", 
    "HIST101", "LIT201", "PHYS101",
    "CHEM101", "CS101", "ART101", 
    "MUS101", "PSYC101", "ENV101"
]

academic_terms = ["Fall 2023", "Spring 2024", "Summer 2024", "Fall 2024"]
statuses = ["active", "pending", "completed"]

teaching_unit_data = []
for i, employee_id in enumerate([1, 2, 3]):
    # Create 4 teaching units per employee (one for each academic term)
    for j in range(4):
        index = i * 4 + j
        title = unit_titles[index % len(unit_titles)]
        code = unit_codes[index % len(unit_codes)]
        term = academic_terms[j]
        
        # Different start/end dates based on term
        if term == "Fall 2023":
            start_date = datetime(2023, 9, 1)
            end_date = datetime(2023, 12, 15)
            status = "completed"
        elif term == "Spring 2024":
            start_date = datetime(2024, 1, 15)
            end_date = datetime(2024, 5, 15)
            status = "completed" if today > datetime(2024, 5, 15).date() else "active"
        elif term == "Summer 2024":
            start_date = datetime(2024, 6, 1)
            end_date = datetime(2024, 8, 15)
            status = "active" if today < datetime(2024, 8, 15).date() else "pending"
        else:  # Fall 2024
            start_date = datetime(2024, 9, 1)
            end_date = datetime(2024, 12, 15)
            status = "pending"
        
        hours_per_week = random.randint(3, 6)
        unit_value = random.randint(3, 5)
        rate_per_unit = random.uniform(75, 150)
        
        teaching_unit = (
            employee_id,  # employee_id
            title,  # title 
            code,  # code
            term,  # academic_term
            format_date(start_date),  # start_date
            format_date(end_date),  # end_date
            hours_per_week,  # hours_per_week
            unit_value,  # unit_value
            rate_per_unit,  # rate_per_unit
            status,  # status
            3,  # created_by
            now(),  # created_at
        )
        
        cursor.execute('''
        INSERT INTO teaching_unit
        (employee_id, title, code, academic_term, start_date, end_date, hours_per_week, unit_value, rate_per_unit, status, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', teaching_unit)
        
        teaching_unit_data.append({
            'id': cursor.lastrowid,
            'title': title,
            'employee_id': employee_id,
            'status': status,
            'start_date': start_date,
            'end_date': end_date
        })

# 7. teaching_unit_relationshipss
print("Inserting teaching_unit_relationships data...")
# Create some relationships between teaching units
# Only create relationships between units from the same employee
for employee_id in [1, 2, 3]:
    employee_units = [u for u in teaching_unit_data if u['employee_id'] == employee_id]
    
    # Need at least 2 units to create a relationship
    if len(employee_units) >= 2:
        for i in range(len(employee_units) - 1):
            relationship_type = random.choice(['prerequisite', 'corequisite', 'continuation', 'related'])
            
            relationship = (
                employee_units[i]['id'],  # source_unit_id
                employee_units[i+1]['id'],  # target_unit_id
                relationship_type,  # relationship_type
                now(),  # created_at
            )
            
            cursor.execute('''
            INSERT INTO teaching_unit_relationships
            (source_unit_id, target_unit_id, relationship_type, created_at)
            VALUES (?, ?, ?, ?)
            ''', relationship)

# 9. training_program
print("Inserting training_program data...")
training_titles = [
    "Effective Teaching Methods", "Classroom Management", "Educational Technology",
    "Diversity and Inclusion", "Student Assessment Strategies", "Curriculum Development",
    "Digital Learning Tools", "Crisis Management", "Leadership Skills",
    "Communication Techniques", "Work-Life Balance", "Research Methods"
]

training_categories = ["pedagogy", "technology", "management", "professional_development", "wellness"]

program_data = []
for i in range(len(training_titles)):
    # Decide if it's past, current, or future training
    if i < 4:
        # Past training
        start_date = random_date(one_year_ago, one_month_ago)
        status = "completed"
    elif i < 8:
        # Current training
        start_date = random_date(one_month_ago, today)
        status = "in_progress"
    else:
        # Future training
        start_date = random_date(today, three_months_ahead)
        status = "upcoming"
    
    # Still calculate duration_days for end_date, but don't include it in the INSERT
    duration_days = random.randint(1, 5)
    end_date = start_date + timedelta(days=duration_days)
    max_participants = random.randint(10, 30)
    category = random.choice(training_categories)
    
    program = (
        training_titles[i],  # title
        f"This program focuses on {training_titles[i].lower()} for educational staff.",  # description
        category,  # category
        random.choice(["Dr. Smith", "Prof. Johnson", "Ms. Davis", "Mr. Wilson"]),  # instructor
        format_date(start_date),  # start_date
        format_date(end_date),  # end_date
        random.choice(["Room 101", "Conference Hall", "Online", "Library"]),  # location
        max_participants,  # max_participants
        status,  # status
        3,  # created_by
        now(),  # created_at
    )
    
    cursor.execute('''
    INSERT INTO training_program
    (title, description, category, instructor, start_date, end_date, location, max_participants, status, created_by, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', program)
    
    program_data.append({
        'id': cursor.lastrowid,
        'title': training_titles[i],
        'status': status,
        'max_participants': max_participants
    })

# 8. training_enrollment
print("Inserting training_enrollment data...")
# Enroll employees in training programs
for employee_id in [1, 2, 3]:
    # Enroll in 4-6 programs
    num_enrollments = random.randint(4, 6)
    programs_to_enroll = random.sample(program_data, min(num_enrollments, len(program_data)))
    
    for program in programs_to_enroll:
        # Determine enrollment status based on program status
        if program['status'] == 'completed':
            status = random.choice(['completed', 'no_show'])
        elif program['status'] == 'in_progress':
            status = 'enrolled'
        else:  # upcoming
            status = 'enrolled'
        
        enrollment = (
            employee_id,  # employee_id
            program['id'],  # training_id
            status,  # status
            random.choice([None, "Great program!", "Very informative.", "Helpful for my classes."]) if status == 'completed' else None,  # feedback
        )
        
        cursor.execute('''
        INSERT INTO training_enrollment
        (employee_id, training_id, status, feedback)
        VALUES (?, ?, ?, ?)
        ''', enrollment)

# 5. payroll_unit
print("Inserting payroll_unit data...")
# Get the teaching units and payroll records we've created
cursor.execute("SELECT id, employee_id, rate_per_unit FROM teaching_unit WHERE employee_id IN (1, 2, 3)")
teaching_units = cursor.fetchall()

cursor.execute("SELECT id, employee_id, period_start, period_end FROM payroll WHERE employee_id IN (1, 2, 3)")
payrolls = cursor.fetchall()

# Group by employee
teaching_units_by_employee = {}
for unit in teaching_units:
    if unit[1] not in teaching_units_by_employee:
        teaching_units_by_employee[unit[1]] = []
    teaching_units_by_employee[unit[1]].append(unit)

payrolls_by_employee = {}
for payroll in payrolls:
    if payroll[1] not in payrolls_by_employee:
        payrolls_by_employee[payroll[1]] = []
    payrolls_by_employee[payroll[1]].append(payroll)

# For each employee, add teaching units to their payrolls
for employee_id in [1, 2, 3]:
    if employee_id in teaching_units_by_employee and employee_id in payrolls_by_employee:
        employee_units = teaching_units_by_employee[employee_id]
        employee_payrolls = payrolls_by_employee[employee_id]
        
        for payroll in employee_payrolls:
            # Randomly choose 1-2 units to include in this payroll
            num_units = min(len(employee_units), random.randint(1, 2))
            selected_units = random.sample(employee_units, num_units)
            
            for unit in selected_units:
                # Add unit_value with a random value between 2-5
                unit_value = random.randint(2, 5)
                # Use the rate_per_unit from the teaching unit
                rate_per_unit = unit[2]  # unit[2] contains rate_per_unit from the teaching unit
                # Calculate total amount
                total_amount = unit_value * rate_per_unit
                
                payroll_unit = (
                    payroll[0],           # payroll_id
                    unit[0],              # teaching_unit_id
                    unit_value,           # unit_value
                    rate_per_unit,        # rate_per_unit
                    total_amount,         # total_amount
                )
                
                cursor.execute('''
                INSERT INTO payroll_unit
                (payroll_id, teaching_unit_id, unit_value, rate_per_unit, total_amount)
                VALUES (?, ?, ?, ?, ?)
                ''', payroll_unit)

# 10. unit_attendance
print("Inserting unit_attendance data...")
# Add attendance records for each teaching unit
for unit in teaching_unit_data:
    # Skip units that haven't started yet
    if unit['start_date'].date() > today:
        continue
    
    # Determine how many attendance records to create based on status
    if unit['status'] == 'completed':
        num_records = random.randint(20, 30)
    elif unit['status'] == 'active':
        num_records = random.randint(5, 15)
    else:  # pending or other
        continue
    
    # Generate attendance dates within the unit period
    start_date = max(unit['start_date'].date(), one_year_ago)
    end_date = min(unit['end_date'].date(), today)
    
    if end_date <= start_date:
        continue  # Skip if date range is invalid
    
    # Generate random attendance dates
    attendance_dates = []
    current_date = start_date
    while current_date <= end_date and len(attendance_dates) < num_records:
        if random.random() < 0.2:  # ~20% chance to record attendance on any given day
            attendance_dates.append(current_date)
        current_date += timedelta(days=1)
    
    # Create attendance records
    for date in attendance_dates:
        status = random.choices(['present', 'absent', 'late', 'excused'], 
                              weights=[0.8, 0.1, 0.05, 0.05])[0]
        hours = random.randint(1, 4)
        
        attendance = (
            unit['id'],            # teaching_unit_id
            format_date(date),     # date
            status,                # status
            hours,                 # hours
            random.choice([None, "Productive session", "Student presentations", "Exam day"]),  # notes
            now(),                 # created_at
            unit['employee_id'],   # recorded_by
        )
        
        cursor.execute('''
        INSERT INTO unit_attendance
        (teaching_unit_id, date, status, hours, notes, created_at, recorded_by)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', attendance)

# Commit and close
conn.commit()
conn.close()

print("Sample data has been successfully inserted!")
print("Total records inserted:")
print("- employee_salary: 3")
print("- leave_request: 15")
print("- payroll: 18")
print("- teaching_unit: 12")
print("- training_program: 12")
print("- plus related records in dependent tables")
