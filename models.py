from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from itsdangerous import URLSafeTimedSerializer
from flask import current_app as app
from datetime import datetime, timedelta

db = SQLAlchemy()
ph = PasswordHasher()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='employee')  # 'employee' (faculty/staff), 'hr' (dept head), 'admin'
    
    @property
    def has_complete_profile(self):
        """Check if user has completed their profile"""
        return hasattr(self, 'profile') and self.profile is not None and \
               self.profile.first_name is not None and \
               self.profile.last_name is not None
    
    def get_display_name(self):
        """Return user's full name if profile is complete, otherwise username"""
        if self.has_complete_profile:
            return self.profile.get_full_name()
        return self.username
    
    def set_password(self, password):
        self.password_hash = ph.hash(password)
        
    def verify_password(self, password):
        try:
            ph.verify(self.password_hash, password)
            return True
        except VerifyMismatchError:
            return False
            
    def is_admin(self):
        return self.role == 'admin'
        
    def is_hr(self):
        return self.role == 'hr'
        
    @classmethod
    def authenticate(cls, username_or_email, password):
        """Authenticate a user by either username or email and password."""
        # Try email first
        user = cls.query.filter_by(email=username_or_email).first()
        
        # If not found by email, try username
        if user is None:
            user = cls.query.filter_by(username=username_or_email).first()
        
        # Return user if found and password matches
        if user and user.verify_password(password):
            return user
        
        return None
    
    def get_reset_token(self, expires_sec=1800):
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        return serializer.dumps(self.id, salt='reset-password')

    @staticmethod
    def verify_reset_token(token, expires_sec=1800):
        serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        try:
            user_id = serializer.loads(token, salt='reset-password', max_age=expires_sec)
        except:
            return None
        return User.query.get(user_id)
        
    def __repr__(self):
        return f'<User {self.username}>'

class LoginAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)  # IPv6 can be up to 45 chars
    username_or_email = db.Column(db.String(120), nullable=True)
    success = db.Column(db.Boolean, default=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_agent = db.Column(db.String(255), nullable=True)
    
    @classmethod
    def is_rate_limited(cls, ip_address, window_minutes=15, max_attempts=5):
        """
        Check if the IP address is rate limited
        
        Args:
            ip_address: The IP address to check
            window_minutes: Time window in minutes to consider (default: 15)
            max_attempts: Maximum number of failed attempts allowed in the window (default: 5)
            
        Returns:
            tuple: (is_limited, message, remaining_attempts)
        """
        # Calculate the timestamp for the window
        window_start = datetime.utcnow() - timedelta(minutes=window_minutes)
        
        # Count failed attempts in the window
        failed_attempts = cls.query.filter(
            cls.ip_address == ip_address,
            cls.success == False,
            cls.timestamp >= window_start
        ).count()
        
        if failed_attempts >= max_attempts:
            # Find the most recent attempt to calculate unlock time
            latest_attempt = cls.query.filter(
                cls.ip_address == ip_address,
                cls.success == False
            ).order_by(cls.timestamp.desc()).first()
            
            if latest_attempt:
                unlock_time = latest_attempt.timestamp + timedelta(minutes=window_minutes)
                now = datetime.utcnow()
                
                if now < unlock_time:
                    time_remaining = unlock_time - now
                    minutes = time_remaining.seconds // 60
                    seconds = time_remaining.seconds % 60
                    message = f"Too many failed login attempts. Please try again in {minutes}m {seconds}s."
                    return True, message, 0
        
        # IP is not rate limited
        remaining = max_attempts - failed_attempts
        return False, None, remaining
    
    @classmethod
    def log_attempt(cls, ip_address, username_or_email=None, success=False, user_agent=None):
        """Log a login attempt in the database"""
        attempt = cls(
            ip_address=ip_address,
            username_or_email=username_or_email,
            success=success,
            user_agent=user_agent
        )
        db.session.add(attempt)
        db.session.commit()
        
    @classmethod
    def reset_for_ip(cls, ip_address):
        """Reset failed attempts for an IP after successful login"""
        # This could either delete the attempts or mark them as handled
        # Here we'll leave the record for auditing but add successful login
        cls.log_attempt(ip_address, success=True)

class EmployeeProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone_number = db.Column(db.String(20))
    address = db.Column(db.String(200))
    city = db.Column(db.String(50))
    country = db.Column(db.String(50))
    bio = db.Column(db.Text)
    position = db.Column(db.String(100))
    hire_date = db.Column(db.Date)
    birth_date = db.Column(db.Date)
    education_level = db.Column(db.String(50))  # bachelor, master, doctorate, other
    teaching_subjects = db.Column(db.String(200))  # Subjects the staff member teaches
    
    # Updated fields for better Cloudinary management
    cloudinary_folder = db.Column(db.String(50), default='hr_profile_pictures')  # Store folder name
    cloudinary_public_id = db.Column(db.String(255), default='default-profile')  # Store actual public_id without folder
    cloudinary_version = db.Column(db.String(20))  # Store version for cache busting
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('profile', lazy=True, uselist=False))
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return None
    
    def set_profile_image(self, cloudinary_result):
        """Update profile image with Cloudinary upload result data"""
        if cloudinary_result and 'public_id' in cloudinary_result:
            # Parse the public_id to extract folder and actual ID
            full_public_id = cloudinary_result['public_id']
            
            if '/' in full_public_id:
                parts = full_public_id.split('/')
                self.cloudinary_folder = parts[0]
                self.cloudinary_public_id = '/'.join(parts[1:])  # In case there are multiple slashes
            else:
                self.cloudinary_folder = 'hr_profile_pictures'  # Default folder
                self.cloudinary_public_id = full_public_id
            
            # Store the version for cache busting
            self.cloudinary_version = str(cloudinary_result.get('version', ''))
            return True
        return False
    
    def has_profile_image(self):
        """Check if user has a custom profile image"""
        return self.cloudinary_public_id and self.cloudinary_public_id != 'default-profile'
    
    @property
    def profile_image(self):
        """Compatibility property for existing code"""
        if not self.has_profile_image():
            return 'default-profile'
        return self.cloudinary_public_id
    
    @profile_image.setter
    def profile_image(self, value):
        """Setter for profile_image property - handles form population"""
        # This is just a compatibility setter
        # The actual image setting is handled via set_profile_image() with the Cloudinary result
        # We don't actually set anything here since this is called from form.populate_obj()
        pass
    
    @property
    def full_cloudinary_id(self):
        """Get the full Cloudinary public_id including folder"""
        if not self.has_profile_image():
            return None
        return f"{self.cloudinary_folder}/{self.cloudinary_public_id}"
    
    def get_cloudinary_url(self, width=300, height=300, crop='fill', format='auto', quality='auto'):
        """Generate a Cloudinary URL with the specified parameters"""
        if not self.has_profile_image():
            return None
        
        # This would ideally use cloudinary.utils.cloudinary_url but returns a formatted string
        # for simplicity in case the Cloudinary SDK is not available in templates
        base_url = f"https://res.cloudinary.com/demeqfksa/image/upload"
        transform = f"c_{crop},f_{format},h_{height},q_{quality},w_{width}"
        version = f"v{self.cloudinary_version}" if self.cloudinary_version else ""
        public_id = f"{self.cloudinary_folder}/{self.cloudinary_public_id}"
        
        # Build the URL with proper path segments
        if version:
            return f"{base_url}/{transform}/{version}/{public_id}"
        else:
            return f"{base_url}/{transform}/{public_id}"

class LeaveRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    approver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    leave_type = db.Column(db.String(50), nullable=False)  # vacation, sick, personal, professional, sabbatical etc.
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, denied
    reason = db.Column(db.Text)
    approval_comment = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = db.relationship('User', foreign_keys=[employee_id], backref=db.backref('leave_requests', lazy='dynamic'))
    approver = db.relationship('User', foreign_keys=[approver_id], backref=db.backref('approved_leaves', lazy='dynamic'))
    
    @property
    def duration_days(self):
        """Calculate the duration of leave in days"""
        if self.start_date and self.end_date:
            # +1 to include both start and end dates
            return (self.end_date - self.start_date).days + 1
        return 0
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_denied(self):
        return self.status == 'denied'
    
    @property
    def status_badge_color(self):
        """Return Bootstrap color class based on status"""
        if self.status == 'approved':
            return 'bg-success'
        elif self.status == 'denied':
            return 'bg-danger'
        else:  # pending
            return 'bg-warning'

class TrainingProgram(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    instructor = db.Column(db.String(100))
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(100))
    max_participants = db.Column(db.Integer, default=0)  # 0 means unlimited
    category = db.Column(db.String(50), nullable=False)  # technical, curriculum, classroom_management, etc.
    status = db.Column(db.String(20), default='upcoming')  # upcoming, in-progress, completed, cancelled
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = db.relationship('User', foreign_keys=[created_by], backref=db.backref('created_trainings', lazy='dynamic'))
    enrollments = db.relationship('TrainingEnrollment', back_populates='training', cascade='all, delete-orphan')
    
    @property
    def duration_days(self):
        """Calculate the duration in days"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0
    
    @property
    def enrolled_count(self):
        """Get the number of enrolled participants"""
        return TrainingEnrollment.query.filter_by(training_id=self.id).count()
    
    @property
    def is_full(self):
        """Check if the training has reached max participants"""
        if self.max_participants == 0:  # Unlimited participants
            return False
        return self.enrolled_count >= self.max_participants
    
    @property
    def status_badge_color(self):
        """Return Bootstrap color class based on status"""
        if self.status == 'upcoming':
            return 'bg-primary'
        elif self.status == 'in-progress':
            return 'bg-warning'
        elif self.status == 'completed':
            return 'bg-success'
        else:  # cancelled
            return 'bg-danger'
    
    @property
    def is_upcoming(self):
        today = datetime.now().date()
        return self.start_date > today
    
    @property
    def is_in_progress(self):
        today = datetime.now().date()
        return self.start_date <= today <= self.end_date
    
    @property
    def is_completed(self):
        today = datetime.now().date()
        return self.end_date < today
    
    def update_status(self):
        """Update status based on dates"""
        today = datetime.now().date()
        
        if self.status == 'cancelled':
            return  # Don't change status if it's cancelled
            
        if self.start_date > today:
            self.status = 'upcoming'
        elif self.start_date <= today <= self.end_date:
            self.status = 'in-progress'
        elif self.end_date < today:
            self.status = 'completed'

class TrainingEnrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    training_id = db.Column(db.Integer, db.ForeignKey('training_program.id'), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(20), default='enrolled')  # enrolled, completed, dropped, failed
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    completion_date = db.Column(db.DateTime)
    feedback = db.Column(db.Text)
    rating = db.Column(db.Integer)  # 1-5 stars
    
    # Define unique constraint to prevent duplicate enrollments
    __table_args__ = (
        db.UniqueConstraint('training_id', 'employee_id', name='unique_enrollment'),
    )
    
    training = db.relationship('TrainingProgram', back_populates='enrollments')
    employee = db.relationship('User', backref=db.backref('training_enrollments', lazy='dynamic'))
    
    @property
    def status_badge_color(self):
        """Return Bootstrap color class based on status"""
        if self.status == 'enrolled':
            return 'bg-primary'
        elif self.status == 'completed':
            return 'bg-success'
        elif self.status == 'dropped':
            return 'bg-warning'
        else:  # failed
            return 'bg-danger'

class EmployeeSalary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='USD', nullable=False)
    effective_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)  # Null if it's the current salary
    salary_type = db.Column(db.String(20), default='annual', nullable=False)  # annual, monthly, hourly, contract, stipend
    contract_type = db.Column(db.String(20), default='full_time')  # full_time, part_time, adjunct, temporary
    academic_year = db.Column(db.String(9))  # e.g., "2023-2024"
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = db.relationship('User', foreign_keys=[employee_id], backref=db.backref('salaries', lazy='dynamic'))
    creator = db.relationship('User', foreign_keys=[created_by])
    
    @property
    def is_active(self):
        """Check if this is the current active salary"""
        return self.end_date is None or self.end_date >= datetime.now().date()
    
    @property
    def formatted_amount(self):
        """Format the amount with currency"""
        return f"{self.currency} {self.amount:,.2f}"
    
    @property
    def annualized_amount(self):
        """Calculate the annual equivalent of the salary"""
        if self.salary_type == 'hourly':
            # For educational setting - assume 1440 hours for full academic year (36 weeks × 40 hours)
            teaching_hours_factor = 1440 if self.contract_type == 'full_time' else 720
            return self.amount * teaching_hours_factor
        elif self.salary_type == 'monthly':
            # Academic year is typically 10 months for faculty
            if self.contract_type == 'full_time':
                return self.amount * 12  # 12 months for full-time
            else:
                return self.amount * 10  # 10 months for others
        elif self.salary_type == 'stipend':
            # Stipends are typically one-time or per-semester payments
            return self.amount * 2  # Assume two semesters per year
        else:  # annual or contract
            return self.amount

# Add this new association table for teaching unit relationships
teaching_unit_relationships = db.Table('teaching_unit_relationships',
    db.Column('source_unit_id', db.Integer, db.ForeignKey('teaching_unit.id'), primary_key=True),
    db.Column('target_unit_id', db.Integer, db.ForeignKey('teaching_unit.id'), primary_key=True),
    db.Column('relationship_type', db.String(20), nullable=False),  # 'prerequisite', 'corequisite', 'related', etc.
    db.Column('created_at', db.DateTime, default=datetime.utcnow)
)

class TeachingUnit(db.Model):
    """Teaching Unit model for managing faculty teaching assignments"""
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20))
    academic_term = db.Column(db.String(50), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    hours_per_week = db.Column(db.Float, default=0)
    unit_value = db.Column(db.Float, default=0)  # Academic units/credits
    rate_per_unit = db.Column(db.Float, default=0)  # Payment rate per unit
    status = db.Column(db.String(20), default='pending')  # pending, active, completed, cancelled
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = db.relationship('User', foreign_keys=[employee_id], backref=db.backref('teaching_units', lazy=True))
    creator = db.relationship('User', foreign_keys=[created_by], backref=db.backref('created_units', lazy=True))
    
    # Explicitly define unit relationship to UnitAttendance without a backref to avoid conflicts
    attendances = db.relationship('UnitAttendance', lazy=True, cascade="all, delete-orphan")
    
    # Add these relationship properties to the TeachingUnit class
    related_to = db.relationship(
        'TeachingUnit', 
        secondary=teaching_unit_relationships,
        primaryjoin=(teaching_unit_relationships.c.source_unit_id == id),
        secondaryjoin=(teaching_unit_relationships.c.target_unit_id == id),
        backref=db.backref('related_from', lazy='dynamic'),
        lazy='dynamic'
    )
    
    def link_unit(self, unit, relationship_type='related'):
        """Link this teaching unit to another unit with specified relationship type"""
        if unit.id == self.id:
            return False  # Cannot link to self
        
        # Check if relationship already exists
        existing = db.session.query(teaching_unit_relationships).filter_by(
            source_unit_id=self.id, 
            target_unit_id=unit.id
        ).first()
        
        if not existing:
            # Create new relationship
            self.related_to.append(unit)
            # Set relationship type
            db.session.execute(teaching_unit_relationships.update().where(
                (teaching_unit_relationships.c.source_unit_id == self.id) & 
                (teaching_unit_relationships.c.target_unit_id == unit.id)
            ).values(relationship_type=relationship_type))
            return True
        return False
        
    def unlink_unit(self, unit):
        """Remove link between this teaching unit and another unit"""
        if unit.id == self.id:
            return False
            
        self.related_to.remove(unit)
        return True
        
    def get_related_units(self, relationship_type=None):
        """Get units related to this unit, optionally filtered by relationship type"""
        query = self.related_to
        if relationship_type:
            query = query.join(teaching_unit_relationships, 
                (teaching_unit_relationships.c.target_unit_id == TeachingUnit.id) &
                (teaching_unit_relationships.c.source_unit_id == self.id) &
                (teaching_unit_relationships.c.relationship_type == relationship_type)
            )
        return query.all()
    
    @property
    def duration_weeks(self):
        """Calculate the duration in weeks"""
        if not self.start_date or not self.end_date:
            return 0
        delta = self.end_date - self.start_date
        return max(1, round(delta.days / 7))
    
    @property
    def total_hours(self):
        """Calculate total hours for this teaching unit"""
        return self.duration_weeks * self.hours_per_week
    
    @property
    def total_payment(self):
        """Calculate the total payment amount"""
        return self.unit_value * self.rate_per_unit
    
    @property
    def attendance_rate(self):
        """Calculate attendance rate as percentage"""
        if not self.attendances:
            return 0
        
        total_records = len(self.attendances)
        if total_records == 0:
            return 0
        
        # Weight different attendance statuses
        present_weight = 1.0
        late_weight = 0.75
        excused_weight = 0.5
        absent_weight = 0.0
        
        attendance_sum = sum(
            present_weight if a.status == 'present' else
            late_weight if a.status == 'late' else
            excused_weight if a.status == 'excused' else
            absent_weight
            for a in self.attendances
        )
        
        return (attendance_sum / total_records) * 100

    def update_status(self):
        """Update the status based on dates"""
        today = datetime.now().date()
        if today < self.start_date:
            self.status = 'pending'
        elif today <= self.end_date:
            self.status = 'active'
        else:
            self.status = 'completed'
        return self.status


class UnitAttendance(db.Model):
    """Attendance records for teaching units"""
    
    id = db.Column(db.Integer, primary_key=True)
    teaching_unit_id = db.Column(db.Integer, db.ForeignKey('teaching_unit.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='present')  # present, absent, late, excused
    hours = db.Column(db.Float, default=0)  # Hours attended/taught
    notes = db.Column(db.Text)
    recorded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    recorder = db.relationship('User', foreign_keys=[recorded_by])
    teaching_unit = db.relationship('TeachingUnit', foreign_keys=[teaching_unit_id])
    
    # For backward compatibility with any code that might be using unit
    @property
    def unit(self):
        """Return the teaching unit for this attendance record"""
        return self.teaching_unit

    @property
    def attendance_factor(self):
        """Return attendance factor based on status"""
        if self.status == 'present':
            return 1.0
        elif self.status == 'late':
            return 0.75
        elif self.status == 'excused':
            return 0.5
        else:  # absent
            return 0.0

class Payroll(db.Model):
    """Payroll model for employee payments"""
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    base_pay = db.Column(db.Float, default=0.0)
    unit_pay = db.Column(db.Float, default=0.0)
    deductions = db.Column(db.Float, default=0.0)
    payment_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='draft')
    payment_method = db.Column(db.String(20))
    reference_number = db.Column(db.String(50))
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = db.relationship('User', foreign_keys=[employee_id], backref='payrolls_received')
    creator = db.relationship('User', foreign_keys=[created_by], backref='payrolls_created')
    
    # Remove both backrefs to avoid conflicts with explicit relationships in the related models
    unit_items = db.relationship('PayrollUnit', lazy=True, cascade="all, delete-orphan")
    deduction_items = db.relationship('PayrollDeduction', lazy=True, cascade="all, delete-orphan")
    
    @property
    def total_pay(self):
        """Calculate total pay (base pay + unit pay)"""
        return self.base_pay + self.unit_pay
    
    @property
    def net_pay(self):
        """Calculate net pay (total pay - deductions)"""
        return self.total_pay - self.deductions
    
    @property
    def status_badge_color(self):
        """Return the appropriate Bootstrap badge color based on status"""
        colors = {
            'draft': 'bg-secondary',
            'pending': 'bg-warning',
            'approved': 'bg-success',
            'paid': 'bg-info',
            'cancelled': 'bg-danger'
        }
        return colors.get(self.status, 'bg-secondary')
    
    def update_totals(self):
        """Recalculate and update the unit pay and deductions totals"""
        # Calculate unit pay
        unit_items = PayrollUnit.query.filter_by(payroll_id=self.id).all()
        self.unit_pay = sum(item.total_amount for item in unit_items)
        
        # Calculate deductions
        deduction_items = PayrollDeduction.query.filter_by(payroll_id=self.id).all()
        self.deductions = sum(item.amount for item in deduction_items)
        
        return self

    @property
    def safe_deduction_items(self):
        """Get deduction items without requiring created_at column"""
        try:
            # Try to get the normal relationship first
            items = self.deduction_items
            return items
        except Exception:
            # If there's an error (missing column), use a direct query that doesn't include created_at
            from sqlalchemy import text
            sql = text("""
                SELECT id, payroll_id, deduction_type, description, amount 
                FROM payroll_deduction 
                WHERE payroll_id = :payroll_id
            """)
            result = db.session.execute(sql, {"payroll_id": self.id})
            
            # Convert the result to PayrollDeduction objects
            deductions = []
            for row in result:
                deduction = PayrollDeduction(
                    id=row.id,
                    payroll_id=row.payroll_id,
                    deduction_type=row.deduction_type,
                    description=row.description,
                    amount=row.amount
                )
                deductions.append(deduction)
            
            return deductions

# We need a helper function to create deductions without created_at column
def add_deduction_safe(payroll_id, deduction_type, description, amount):
    """Add a deduction record without using created_at column"""
    from sqlalchemy import text
    
    # Use direct SQL to insert without the created_at column
    sql = text("""
        INSERT INTO payroll_deduction (payroll_id, deduction_type, description, amount)
        VALUES (:payroll_id, :deduction_type, :description, :amount)
    """)
    
    # Execute with parameters
    db.session.execute(sql, {
        "payroll_id": payroll_id,
        "deduction_type": deduction_type,
        "description": description,
        "amount": float(amount)
    })
    
    # Get the inserted record's ID
    result = db.session.execute(text("""
        SELECT id FROM payroll_deduction 
        WHERE payroll_id = :payroll_id 
        ORDER BY id DESC LIMIT 1
    """), {"payroll_id": payroll_id})
    
    return result.scalar()

class PayrollDeduction(db.Model):
    """Model for payroll deductions"""
    id = db.Column(db.Integer, primary_key=True)
    payroll_id = db.Column(db.Integer, db.ForeignKey('payroll.id'), nullable=False)
    deduction_type = db.Column(db.String(20), default='other')  # tax, insurance, retirement, other
    description = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    
    # Make created_at optional to avoid errors when the column doesn't exist
    # Using Declarative Hybrid Pattern to handle missing column
    try:
        created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    except:
        created_at = None
    
    # Relationship with Payroll - explicitly defined
    payroll = db.relationship('Payroll')
    
    def __repr__(self):
        return f'<PayrollDeduction {self.id}: {self.description} ${self.amount}>'

class PayrollUnit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payroll_id = db.Column(db.Integer, db.ForeignKey('payroll.id'), nullable=False)
    teaching_unit_id = db.Column(db.Integer, db.ForeignKey('teaching_unit.id'), nullable=False)
    unit_value = db.Column(db.Float, nullable=False)  # Number of units
    rate_per_unit = db.Column(db.Float, nullable=False)  # Rate per unit
    attendance_factor = db.Column(db.Float, default=1.0)  # Attendance-based adjustment (0.0-1.0)
    total_amount = db.Column(db.Float, nullable=False)  # Total payment for this unit
    
    # Relationships
    payroll = db.relationship('Payroll')
    teaching_unit = db.relationship('TeachingUnit', foreign_keys=[teaching_unit_id])
