-- Database Schema for School HR System (Railway PostgreSQL)
-- Run this to create all tables, indexes, and relationships

-- ============================================
-- USER TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS "user" (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    department VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'employee',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_user_username ON "user"(username);
CREATE INDEX IF NOT EXISTS idx_user_email ON "user"(email);
CREATE INDEX IF NOT EXISTS idx_user_role ON "user"(role);
CREATE INDEX IF NOT EXISTS idx_user_department ON "user"(department);

-- ============================================
-- LOGIN_ATTEMPT TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS login_attempt (
    id SERIAL PRIMARY KEY,
    ip_address VARCHAR(45) NOT NULL,
    username_or_email VARCHAR(120),
    success BOOLEAN DEFAULT FALSE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_agent VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_login_attempt_ip ON login_attempt(ip_address);
CREATE INDEX IF NOT EXISTS idx_login_attempt_timestamp ON login_attempt(timestamp);
CREATE INDEX IF NOT EXISTS idx_login_attempt_success ON login_attempt(success);

-- ============================================
-- EMPLOYEE_PROFILE TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS employee_profile (
    id SERIAL PRIMARY KEY,
    user_id INTEGER UNIQUE NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    phone_number VARCHAR(20),
    address VARCHAR(200),
    city VARCHAR(50),
    country VARCHAR(50),
    bio TEXT,
    position VARCHAR(100),
    hire_date DATE,
    birth_date DATE,
    education_level VARCHAR(50),
    teaching_subjects VARCHAR(200),
    cloudinary_folder VARCHAR(50) DEFAULT 'hr_profile_pictures',
    cloudinary_public_id VARCHAR(255) DEFAULT 'default-profile',
    cloudinary_version VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_employee_profile_user_id ON employee_profile(user_id);
CREATE INDEX IF NOT EXISTS idx_employee_profile_position ON employee_profile(position);

-- ============================================
-- LEAVE_REQUEST TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS leave_request (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    approver_id INTEGER REFERENCES "user"(id) ON DELETE SET NULL,
    leave_type VARCHAR(50) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    reason TEXT,
    approval_comment TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_leave_request_employee_id ON leave_request(employee_id);
CREATE INDEX IF NOT EXISTS idx_leave_request_approver_id ON leave_request(approver_id);
CREATE INDEX IF NOT EXISTS idx_leave_request_status ON leave_request(status);
CREATE INDEX IF NOT EXISTS idx_leave_request_dates ON leave_request(start_date, end_date);

-- ============================================
-- TRAINING_PROGRAM TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS training_program (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    instructor VARCHAR(100),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    location VARCHAR(100),
    max_participants INTEGER DEFAULT 0,
    category VARCHAR(50) NOT NULL,
    status VARCHAR(20) DEFAULT 'upcoming',
    created_by INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_training_program_category ON training_program(category);
CREATE INDEX IF NOT EXISTS idx_training_program_status ON training_program(status);
CREATE INDEX IF NOT EXISTS idx_training_program_dates ON training_program(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_training_program_created_by ON training_program(created_by);

-- ============================================
-- TRAINING_ENROLLMENT TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS training_enrollment (
    id SERIAL PRIMARY KEY,
    training_id INTEGER NOT NULL REFERENCES training_program(id) ON DELETE CASCADE,
    employee_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'enrolled',
    enrollment_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completion_date TIMESTAMP WITH TIME ZONE,
    feedback TEXT,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT unique_enrollment UNIQUE (training_id, employee_id)
);

CREATE INDEX IF NOT EXISTS idx_training_enrollment_training_id ON training_enrollment(training_id);
CREATE INDEX IF NOT EXISTS idx_training_enrollment_employee_id ON training_enrollment(employee_id);
CREATE INDEX IF NOT EXISTS idx_training_enrollment_status ON training_enrollment(status);

-- ============================================
-- EMPLOYEE_SALARY TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS employee_salary (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    amount NUMERIC(12, 2) NOT NULL,
    currency VARCHAR(10) NOT NULL DEFAULT 'PHP',
    effective_date DATE NOT NULL,
    end_date DATE,
    salary_type VARCHAR(20) NOT NULL DEFAULT 'annual',
    contract_type VARCHAR(20) DEFAULT 'full_time',
    academic_year VARCHAR(9),
    created_by INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_employee_salary_employee_id ON employee_salary(employee_id);
CREATE INDEX IF NOT EXISTS idx_employee_salary_effective_date ON employee_salary(effective_date);
CREATE INDEX IF NOT EXISTS idx_employee_salary_academic_year ON employee_salary(academic_year);

-- ============================================
-- TEACHING_UNIT TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS teaching_unit (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    code VARCHAR(20),
    academic_term VARCHAR(50) NOT NULL,
    employee_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    hours_per_week NUMERIC(5, 2) DEFAULT 0,
    unit_value NUMERIC(5, 2) DEFAULT 0,
    rate_per_unit NUMERIC(10, 2) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    created_by INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_teaching_unit_employee_id ON teaching_unit(employee_id);
CREATE INDEX IF NOT EXISTS idx_teaching_unit_academic_term ON teaching_unit(academic_term);
CREATE INDEX IF NOT EXISTS idx_teaching_unit_status ON teaching_unit(status);
CREATE INDEX IF NOT EXISTS idx_teaching_unit_dates ON teaching_unit(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_teaching_unit_code ON teaching_unit(code);

-- ============================================
-- TEACHING_UNIT_RELATIONSHIPS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS teaching_unit_relationships (
    source_unit_id INTEGER NOT NULL REFERENCES teaching_unit(id) ON DELETE CASCADE,
    target_unit_id INTEGER NOT NULL REFERENCES teaching_unit(id) ON DELETE CASCADE,
    relationship_type VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (source_unit_id, target_unit_id)
);

CREATE INDEX IF NOT EXISTS idx_teaching_unit_relationships_type ON teaching_unit_relationships(relationship_type);

-- ============================================
-- UNIT_ATTENDANCE TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS unit_attendance (
    id SERIAL PRIMARY KEY,
    teaching_unit_id INTEGER NOT NULL REFERENCES teaching_unit(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'present',
    hours NUMERIC(5, 2) DEFAULT 0,
    notes TEXT,
    recorded_by INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_unit_attendance_teaching_unit_id ON unit_attendance(teaching_unit_id);
CREATE INDEX IF NOT EXISTS idx_unit_attendance_date ON unit_attendance(date);
CREATE INDEX IF NOT EXISTS idx_unit_attendance_status ON unit_attendance(status);

-- ============================================
-- PAYROLL TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS payroll (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    base_pay NUMERIC(12, 2) DEFAULT 0.0,
    unit_pay NUMERIC(12, 2) DEFAULT 0.0,
    deductions NUMERIC(12, 2) DEFAULT 0.0,
    payment_date DATE,
    status VARCHAR(20) DEFAULT 'draft',
    payment_method VARCHAR(20),
    reference_number VARCHAR(50),
    notes TEXT,
    created_by INTEGER NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payroll_employee_id ON payroll(employee_id);
CREATE INDEX IF NOT EXISTS idx_payroll_period ON payroll(period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_payroll_status ON payroll(status);
CREATE INDEX IF NOT EXISTS idx_payroll_created_by ON payroll(created_by);

-- ============================================
-- PAYROLL_DEDUCTION TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS payroll_deduction (
    id SERIAL PRIMARY KEY,
    payroll_id INTEGER NOT NULL REFERENCES payroll(id) ON DELETE CASCADE,
    deduction_type VARCHAR(20) DEFAULT 'other',
    description VARCHAR(100) NOT NULL,
    amount NUMERIC(12, 2) NOT NULL DEFAULT 0.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_payroll_deduction_payroll_id ON payroll_deduction(payroll_id);
CREATE INDEX IF NOT EXISTS idx_payroll_deduction_type ON payroll_deduction(deduction_type);

-- ============================================
-- PAYROLL_UNIT TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS payroll_unit (
    id SERIAL PRIMARY KEY,
    payroll_id INTEGER NOT NULL REFERENCES payroll(id) ON DELETE CASCADE,
    teaching_unit_id INTEGER NOT NULL REFERENCES teaching_unit(id) ON DELETE CASCADE,
    unit_value NUMERIC(5, 2) NOT NULL,
    rate_per_unit NUMERIC(10, 2) NOT NULL,
    attendance_factor NUMERIC(3, 2) DEFAULT 1.0,
    total_amount NUMERIC(12, 2) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_payroll_unit_payroll_id ON payroll_unit(payroll_id);
CREATE INDEX IF NOT EXISTS idx_payroll_unit_teaching_unit_id ON payroll_unit(teaching_unit_id);

-- ============================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_user_updated_at ON "user";
CREATE TRIGGER update_user_updated_at BEFORE UPDATE ON "user"
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_employee_profile_updated_at ON employee_profile;
CREATE TRIGGER update_employee_profile_updated_at BEFORE UPDATE ON employee_profile
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_leave_request_updated_at ON leave_request;
CREATE TRIGGER update_leave_request_updated_at BEFORE UPDATE ON leave_request
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_training_program_updated_at ON training_program;
CREATE TRIGGER update_training_program_updated_at BEFORE UPDATE ON training_program
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_employee_salary_updated_at ON employee_salary;
CREATE TRIGGER update_employee_salary_updated_at BEFORE UPDATE ON employee_salary
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_teaching_unit_updated_at ON teaching_unit;
CREATE TRIGGER update_teaching_unit_updated_at BEFORE UPDATE ON teaching_unit
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_payroll_updated_at ON payroll;
CREATE TRIGGER update_payroll_updated_at BEFORE UPDATE ON payroll
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
