from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, DateField, IntegerField, SelectMultipleField, RadioField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, NumberRange
from flask_wtf.file import FileField, FileAllowed
from models import User
from wtforms.fields import FloatField
from wtforms.validators import NumberRange, Optional
from datetime import datetime, timedelta  # Add datetime import here

class LoginForm(FlaskForm):
    # Change from email to username_or_email
    username_or_email = StringField('Username or Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class SignupForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    department = SelectField('Department', choices=[
        ('mathematics', 'Mathematics'),
        ('science', 'Science'),
        ('english', 'English'),
        ('social_studies', 'Social Studies'),
        ('languages', 'Foreign Languages'),
        ('arts', 'Arts & Music'),
        ('physical_education', 'Physical Education'),
        ('special_education', 'Special Education'),
        ('administration', 'Administration'),
        ('counseling', 'Student Counseling'),
        ('library', 'Library')
    ], validators=[DataRequired()])
    role = SelectField('Account Type', choices=[
        ('employee', 'Faculty/Staff'),
        ('hr', 'Department Head'),
        ('admin', 'Administrator')
    ], validators=[DataRequired()])
    submit = SubmitField('Sign Up')

class RequestResetForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('There is no account with that email. You must register first.')

class ResetPasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm New Password', 
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Reset Password')

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    phone_number = StringField('Phone Number', validators=[Length(max=20)])
    address = StringField('Address', validators=[Length(max=200)])
    city = StringField('City', validators=[Length(max=50)])
    country = StringField('Country', validators=[Length(max=50)])
    bio = TextAreaField('Bio')
    position = StringField('Position', validators=[Length(max=100)])
    hire_date = DateField('Hire Date', format='%Y-%m-%d', validators=[DataRequired()])
    birth_date = DateField('Birth Date', format='%Y-%m-%d')
    education_level = SelectField('Education Level', choices=[
        ('bachelor', 'Bachelor\'s Degree'),
        ('master', 'Master\'s Degree'),
        ('doctorate', 'Doctorate/PhD'),
        ('other', 'Other Certification')
    ])
    teaching_subjects = StringField('Teaching Subjects')
    profile_image = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')
    ])
    submit = SubmitField('Update Profile')

class EmployeeSearchForm(FlaskForm):
    search = StringField('Search', validators=[Length(max=100)])
    department = SelectField('Department', choices=[
        ('', 'All Departments'),
        ('mathematics', 'Mathematics'),
        ('science', 'Science'),
        ('english', 'English'),
        ('social_studies', 'Social Studies'),
        ('languages', 'Foreign Languages'),
        ('arts', 'Arts & Music'),
        ('physical_education', 'Physical Education'),
        ('special_education', 'Special Education'),
        ('administration', 'Administration'),
        ('counseling', 'Student Counseling'),
        ('library', 'Library')
    ], validators=[])
    submit = SubmitField('Search')

class LeaveRequestForm(FlaskForm):
    leave_type = SelectField('Leave Type', choices=[
        ('vacation', 'Vacation Leave'),
        ('sick', 'Sick Leave'),
        ('personal', 'Personal Leave'),
        ('bereavement', 'Bereavement Leave'),
        ('maternity', 'Maternity Leave'),
        ('paternity', 'Paternity Leave'),
        ('professional', 'Professional Development'),
        ('sabbatical', 'Sabbatical'),
        ('unpaid', 'Unpaid Leave')
    ], validators=[DataRequired()])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    reason = TextAreaField('Reason for Leave', validators=[DataRequired(), Length(max=500)])
    submit = SubmitField('Submit Request')
    
    def validate_end_date(self, field):
        """Ensure end_date is not before start_date"""
        if field.data < self.start_date.data:
            raise ValidationError('End date cannot be before start date.')

class LeaveApprovalForm(FlaskForm):
    status = SelectField('Status', choices=[
        ('approved', 'Approve'),
        ('denied', 'Deny')
    ], validators=[DataRequired()])
    comment = TextAreaField('Comment', validators=[Length(max=500)])
    submit = SubmitField('Submit Decision')

class TrainingProgramForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    instructor = StringField('Instructor', validators=[DataRequired(), Length(max=100)])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    max_participants = IntegerField('Maximum Participants (0 for unlimited)', default=0, validators=[NumberRange(min=0)])
    category = SelectField('Category', choices=[
        ('technical', 'Technical Skills'),
        ('curriculum', 'Curriculum Development'),
        ('classroom_management', 'Classroom Management'),
        ('professional', 'Professional Development'),
        ('compliance', 'Compliance & Safety'),
        ('technology', 'Educational Technology'),
        ('special_ed', 'Special Education')
    ], validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('upcoming', 'Upcoming'),
        ('in-progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], validators=[DataRequired()])
    submit = SubmitField('Save Training Program')
    
    def validate_end_date(self, field):
        """Ensure end_date is not before start_date"""
        if field.data < self.start_date.data:
            raise ValidationError('End date cannot be before start date.')

class EnrollmentForm(FlaskForm):
    employees = SelectMultipleField('Select Employees', coerce=int)
    submit = SubmitField('Enroll Selected Employees')

class TrainingFeedbackForm(FlaskForm):
    rating = RadioField('Rating', choices=[
        ('1', '1 - Very Poor'),
        ('2', '2 - Poor'),
        ('3', '3 - Average'),
        ('4', '4 - Good'),
        ('5', '5 - Excellent')
    ], validators=[DataRequired()], coerce=int)
    feedback = TextAreaField('Feedback', validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField('Submit Feedback')

class SalaryForm(FlaskForm):
    amount = FloatField('Salary Amount', validators=[DataRequired(), NumberRange(min=0)])
    currency = SelectField('Currency', choices=[
        ('USD', 'USD - US Dollar'),
        ('EUR', 'EUR - Euro'),
        ('GBP', 'GBP - British Pound'),
        ('JPY', 'JPY - Japanese Yen'),
        ('CAD', 'CAD - Canadian Dollar'),
        ('AUD', 'AUD - Australian Dollar')
    ])
    salary_type = SelectField('Salary Type', choices=[
        ('annual', 'Annual'),
        ('monthly', 'Monthly'),
        ('hourly', 'Hourly'),
        ('contract', 'Contract'),
        ('stipend', 'Stipend')
    ])
    contract_type = SelectField('Contract Type', choices=[
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('adjunct', 'Adjunct'),
        ('temporary', 'Temporary')
    ])
    effective_date = DateField('Effective Date', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Save Compensation')

class SalaryReportForm(FlaskForm):
    department = SelectField('Department', choices=[
        ('', 'All Departments'),
        ('mathematics', 'Mathematics'),
        ('science', 'Science'),
        ('english', 'English'),
        ('social_studies', 'Social Studies'),
        ('languages', 'Foreign Languages'),
        ('arts', 'Arts & Music'),
        ('physical_education', 'Physical Education'),
        ('special_education', 'Special Education'),
        ('administration', 'Administration'),
        ('counseling', 'Student Counseling'),
        ('library', 'Library')
    ])
    date_range = SelectField('Date Range', choices=[
        ('current', 'Current Salaries'),
        ('year', 'Current Academic Year'),
        ('last_year', 'Previous Academic Year'),
        ('custom', 'Custom Range')
    ])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[Optional()])
    group_by = SelectField('Group By', choices=[
        ('none', 'No Grouping'),
        ('department', 'Department'),
        ('salary_type', 'Salary Type'),
        ('contract_type', 'Contract Type')
    ])
    include_inactive = BooleanField('Include Inactive Employees')
    export_format = SelectField('Export Format', choices=[
        ('html', 'Web View'),
        ('csv', 'CSV File'),
        ('pdf', 'PDF File')
    ])
    submit = SubmitField('Generate Report')

class TeachingUnitForm(FlaskForm):
    title = StringField('Course/Unit Title', validators=[DataRequired(), Length(max=100)])
    code = StringField('Course/Unit Code', validators=[Length(max=20)])
    hours_per_week = FloatField('Teaching Hours per Week', validators=[DataRequired(), NumberRange(min=0.5)])
    unit_value = FloatField('Academic Units', validators=[DataRequired(), NumberRange(min=0.5)])
    rate_per_unit = FloatField('Rate per Unit', validators=[DataRequired(), NumberRange(min=0)])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[DataRequired()])
    academic_term = SelectField('Academic Term', choices=[
        ('Fall 2023', 'Fall 2023'),
        ('Spring 2024', 'Spring 2024'),
        ('Summer 2024', 'Summer 2024'),
        ('Fall 2024', 'Fall 2024')
    ])
    status = SelectField('Status', choices=[
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ])
    submit = SubmitField('Save Teaching Unit')
    
    def validate_end_date(self, field):
        """Ensure end_date is not before start_date"""
        if field.data < self.start_date.data:
            raise ValidationError('End date cannot be before start date.')

class UnitAttendanceForm(FlaskForm):
    date = DateField('Date', format='%Y-%m-%d', validators=[DataRequired()])
    hours = FloatField('Hours', validators=[DataRequired(), NumberRange(min=0.5, max=12)])
    status = SelectField('Status', choices=[
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('excused', 'Excused Absence'),
        ('late', 'Late Arrival')
    ])
    notes = TextAreaField('Notes', validators=[Length(max=500)])
    submit = SubmitField('Record Attendance')

class PayrollForm(FlaskForm):
    period_start = DateField('Period Start', format='%Y-%m-%d', validators=[DataRequired()])
    period_end = DateField('Period End', format='%Y-%m-%d', validators=[DataRequired()])
    base_pay = FloatField('Base Pay (Fixed Salary)', validators=[NumberRange(min=0)])
    payment_date = DateField('Payment Date', format='%Y-%m-%d')
    payment_method = SelectField('Payment Method', choices=[
        ('bank_transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('cash', 'Cash')
    ])
    reference_number = StringField('Reference Number', validators=[Length(max=50)])
    notes = TextAreaField('Notes', validators=[Length(max=500)])
    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('paid', 'Paid')
    ])
    submit = SubmitField('Generate Payroll')
    
    def validate_period_end(self, field):
        """Ensure period_end is not before period_start"""
        if field.data < self.period_start.data:
            raise ValidationError('End date cannot be before period_start.')

class PayrollDeductionForm(FlaskForm):
    """Form for adding deductions to a payroll record"""
    deduction_type = SelectField('Type', choices=[
        ('tax', 'Tax'),
        ('insurance', 'Insurance'),
        ('retirement', 'Retirement'),
        ('other', 'Other')
    ], validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired(), Length(max=100)])
    amount = FloatField('Amount ($)', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Add Deduction')

class PayrollSearchForm(FlaskForm):
    """Form for searching and filtering payroll records"""
    # Use coerce=str instead of the default int to handle empty strings properly
    employee = SelectField('Employee', choices=[], validators=[Optional()], coerce=str)
    period = SelectField('Pay Period', choices=[
        ('', 'All Periods'),
        ('current_month', 'Current Month'),
        ('previous_month', 'Previous Month'),
        ('current_year', 'Current Year'),
    ], validators=[Optional()])
    status = SelectField('Status', choices=[
        ('', 'All Status'),
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], validators=[Optional()])
    start_date = DateField('From Date', validators=[Optional()])
    end_date = DateField('To Date', validators=[Optional()])
    
    def __init__(self, *args, **kwargs):
        super(PayrollSearchForm, self).__init__(*args, **kwargs)
        # Employee choices will be set in the route

class AttendanceReportForm(FlaskForm):
    employee = SelectField('Faculty/Staff', coerce=int, choices=[])
    unit = SelectField('Teaching Unit', coerce=int, choices=[])
    date_range = SelectField('Date Range', choices=[
        ('current_month', 'Current Month'),
        ('previous_month', 'Previous Month'),
        ('current_term', 'Current Academic Term'),
        ('custom', 'Custom Date Range')
    ])
    start_date = DateField('Start Date', format='%Y-%m-%d', validators=[Optional()])
    end_date = DateField('End Date', format='%Y-%m-%d', validators=[Optional()])
    format = SelectField('Report Format', choices=[
        ('html', 'Web View'),
        ('csv', 'CSV File'),
        ('pdf', 'PDF File')
    ])
    submit = SubmitField('Generate Report')
    
    def validate(self):
        if not super().validate():
            return False
            
        # Custom validation
        if self.date_range.data == 'custom':
            if not self.start_date.data or not self.end_date.data:
                self.start_date.errors.append('Start and end dates are required for custom date range')
                return False
                
            if self.start_date.data > self.end_date.data:
                self.start_date.errors.append('Start date cannot be after end date')
                return False
                
        return True

# Add Attendance-related forms
class AttendanceForm(FlaskForm):
    """Form for recording attendance"""
    date = DateField('Date', validators=[DataRequired()], default=datetime.now().date())
    status = RadioField('Attendance Status', 
                        choices=[
                            ('present', 'Present'), 
                            ('late', 'Late'), 
                            ('excused', 'Excused'), 
                            ('absent', 'Absent')
                        ],
                        default='present',
                        validators=[DataRequired()])
    hours = FloatField('Hours', validators=[DataRequired(), NumberRange(min=0.5, max=12)], default=2.0)
    notes = TextAreaField('Notes')
    submit = SubmitField('Record Attendance')

class AttendanceReportForm(FlaskForm):
    """Form for generating attendance reports"""
    employee = SelectField('Faculty/Staff', coerce=int, validators=[DataRequired()])
    unit = SelectField('Teaching Unit', coerce=int, validators=[DataRequired()])
    date_range = SelectField('Date Range',
                            choices=[
                                ('current_month', 'Current Month'),
                                ('previous_month', 'Previous Month'),
                                ('current_term', 'Current Term'),
                                ('last_term', 'Last Term'),
                                ('custom', 'Custom Range')
                            ],
                            default='current_month')
    start_date = DateField('Start Date', validators=[], default=datetime.now().date() - timedelta(days=30))
    end_date = DateField('End Date', validators=[], default=datetime.now().date())
    format = SelectField('Report Format',
                        choices=[
                            ('html', 'View in Browser'),
                            ('csv', 'Export as CSV'),
                            ('pdf', 'Export as PDF')
                        ],
                        default='html')
    submit = SubmitField('Generate Report')

class TeachingUnitForm(FlaskForm):
    """Form for creating/editing teaching units"""
    title = StringField('Course Title', validators=[DataRequired(), Length(min=3, max=100)])
    code = StringField('Course Code', validators=[Optional(), Length(max=20)])
    employee_id = SelectField('Assigned Faculty', coerce=int, validators=[DataRequired()])
    academic_term = SelectField('Academic Term', 
                              choices=[
                                  ('Fall 2023', 'Fall 2023'),
                                  ('Spring 2024', 'Spring 2024'),
                                  ('Summer 2024', 'Summer 2024'),
                                  ('Fall 2024', 'Fall 2024')
                              ],
                              validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    hours_per_week = FloatField('Teaching Hours/Week', validators=[DataRequired(), NumberRange(min=0.5, max=40)])
    unit_value = FloatField('Academic Units/Credits', validators=[DataRequired(), NumberRange(min=0.5, max=10)])
    rate_per_unit = FloatField('Rate per Unit ($)', validators=[DataRequired(), NumberRange(min=0)])
    status = SelectField('Status',
                        choices=[
                            ('pending', 'Pending'),
                            ('active', 'Active'),
                            ('completed', 'Completed'),
                            ('cancelled', 'Cancelled')
                        ],
                        default='active')
    submit = SubmitField('Save Teaching Unit')
    
    def __init__(self, *args, **kwargs):
        super(TeachingUnitForm, self).__init__(*args, **kwargs)
        # If choices are set elsewhere (like in the route), 
        # this ensures we have default empty choices to prevent the TypeError
        if self.employee_id.choices is None:
            self.employee_id.choices = []

class PayrollForm(FlaskForm):
    """Form for creating and editing payroll records"""
    employee_id = SelectField('Employee', coerce=int, validators=[DataRequired()])
    period_start = DateField('Period Start Date', validators=[DataRequired()])
    period_end = DateField('Period End Date', validators=[DataRequired()])
    payment_date = DateField('Payment Date', validators=[Optional()])
    base_pay = FloatField('Base Pay ($)', default=0.0, validators=[Optional(), NumberRange(min=0)])
    payment_method = SelectField('Payment Method', choices=[
        ('direct_deposit', 'Direct Deposit'),
        ('check', 'Check'),
        ('cash', 'Cash'),
        ('bank_transfer', 'Bank Transfer'),
    ], validators=[Optional()])
    reference_number = StringField('Reference Number', validators=[Optional(), Length(max=50)])
    status = SelectField('Status', choices=[
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], default='draft', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional(), Length(max=1000)])
    submit = SubmitField('Save Payroll')
    
    def validate_period_end(form, field):
        """Validate that end date is after start date"""
        if form.period_start.data and field.data and field.data < form.period_start.data:
            raise ValidationError('End date must be after start date')
            
    def validate_payment_date(form, field):
        """Validate that payment date is not before period end"""
        if form.period_end.data and field.data and field.data < form.period_end.data:
            raise ValidationError('Payment date should be on or after the period end date')
