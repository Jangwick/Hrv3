-- Supabase Database Schema for School HR System
-- This file creates all tables, indexes, and relationships for the HR system
-- Run this in the Supabase SQL Editor

-- Enable UUID extension if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

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

-- Indexes for user table
CREATE INDEX idx_user_username ON "user"(username);
CREATE INDEX idx_user_email ON "user"(email);
CREATE INDEX idx_user_role ON "user"(role);
CREATE INDEX idx_user_department ON "user"(department);

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

-- Indexes for login_attempt
CREATE INDEX idx_login_attempt_ip ON login_attempt(ip_address);
CREATE INDEX idx_login_attempt_timestamp ON login_attempt(timestamp);
CREATE INDEX idx_login_attempt_success ON login_attempt(success);

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

-- Indexes for employee_profile
CREATE INDEX idx_employee_profile_user_id ON employee_profile(user_id);
CREATE INDEX idx_employee_profile_position ON employee_profile(position);
CREATE INDEX idx_employee_profile_department ON employee_profile(user_id);

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

-- Indexes for leave_request
CREATE INDEX idx_leave_request_employee_id ON leave_request(employee_id);
CREATE INDEX idx_leave_request_approver_id ON leave_request(approver_id);
CREATE INDEX idx_leave_request_status ON leave_request(status);
CREATE INDEX idx_leave_request_dates ON leave_request(start_date, end_date);

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

-- Indexes for training_program
CREATE INDEX idx_training_program_category ON training_program(category);
CREATE INDEX idx_training_program_status ON training_program(status);
CREATE INDEX idx_training_program_dates ON training_program(start_date, end_date);
CREATE INDEX idx_training_program_created_by ON training_program(created_by);

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

-- Indexes for training_enrollment
CREATE INDEX idx_training_enrollment_training_id ON training_enrollment(training_id);
CREATE INDEX idx_training_enrollment_employee_id ON training_enrollment(employee_id);
CREATE INDEX idx_training_enrollment_status ON training_enrollment(status);

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

-- Indexes for employee_salary
CREATE INDEX idx_employee_salary_employee_id ON employee_salary(employee_id);
CREATE INDEX idx_employee_salary_effective_date ON employee_salary(effective_date);
CREATE INDEX idx_employee_salary_academic_year ON employee_salary(academic_year);

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

-- Indexes for teaching_unit
CREATE INDEX idx_teaching_unit_employee_id ON teaching_unit(employee_id);
CREATE INDEX idx_teaching_unit_academic_term ON teaching_unit(academic_term);
CREATE INDEX idx_teaching_unit_status ON teaching_unit(status);
CREATE INDEX idx_teaching_unit_dates ON teaching_unit(start_date, end_date);
CREATE INDEX idx_teaching_unit_code ON teaching_unit(code);

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

-- Indexes for teaching_unit_relationships
CREATE INDEX idx_teaching_unit_relationships_type ON teaching_unit_relationships(relationship_type);

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

-- Indexes for unit_attendance
CREATE INDEX idx_unit_attendance_teaching_unit_id ON unit_attendance(teaching_unit_id);
CREATE INDEX idx_unit_attendance_date ON unit_attendance(date);
CREATE INDEX idx_unit_attendance_status ON unit_attendance(status);

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

-- Indexes for payroll
CREATE INDEX idx_payroll_employee_id ON payroll(employee_id);
CREATE INDEX idx_payroll_period ON payroll(period_start, period_end);
CREATE INDEX idx_payroll_status ON payroll(status);
CREATE INDEX idx_payroll_created_by ON payroll(created_by);

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

-- Indexes for payroll_deduction
CREATE INDEX idx_payroll_deduction_payroll_id ON payroll_deduction(payroll_id);
CREATE INDEX idx_payroll_deduction_type ON payroll_deduction(deduction_type);

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

-- Indexes for payroll_unit
CREATE INDEX idx_payroll_unit_payroll_id ON payroll_unit(payroll_id);
CREATE INDEX idx_payroll_unit_teaching_unit_id ON payroll_unit(teaching_unit_id);

-- ============================================
-- TRIGGERS FOR UPDATED_AT
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to all tables with updated_at
CREATE TRIGGER update_user_updated_at BEFORE UPDATE ON "user"
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_employee_profile_updated_at BEFORE UPDATE ON employee_profile
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_leave_request_updated_at BEFORE UPDATE ON leave_request
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_training_program_updated_at BEFORE UPDATE ON training_program
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_employee_salary_updated_at BEFORE UPDATE ON employee_salary
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_teaching_unit_updated_at BEFORE UPDATE ON teaching_unit
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payroll_updated_at BEFORE UPDATE ON payroll
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================

-- Enable RLS on all tables
ALTER TABLE "user" ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_profile ENABLE ROW LEVEL SECURITY;
ALTER TABLE leave_request ENABLE ROW LEVEL SECURITY;
ALTER TABLE training_program ENABLE ROW LEVEL SECURITY;
ALTER TABLE training_enrollment ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_salary ENABLE ROW LEVEL SECURITY;
ALTER TABLE teaching_unit ENABLE ROW LEVEL SECURITY;
ALTER TABLE teaching_unit_relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE unit_attendance ENABLE ROW LEVEL SECURITY;
ALTER TABLE payroll ENABLE ROW LEVEL SECURITY;
ALTER TABLE payroll_deduction ENABLE ROW LEVEL SECURITY;
ALTER TABLE payroll_unit ENABLE ROW LEVEL SECURITY;

-- Basic RLS policies (adjust based on your authentication requirements)
-- These are permissive policies - you may want to restrict them further

-- User table policies
CREATE POLICY "Allow read access to authenticated users" ON "user"
    FOR SELECT USING (auth.uid()::text IS NOT NULL);

CREATE POLICY "Allow insert for service role" ON "user"
    FOR INSERT WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Allow update for own record" ON "user"
    FOR UPDATE USING (auth.uid()::text = id::text);

-- Employee profile policies
CREATE POLICY "Allow read access to authenticated users" ON employee_profile
    FOR SELECT USING (auth.uid()::text IS NOT NULL);

CREATE POLICY "Allow insert for service role" ON employee_profile
    FOR INSERT WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Allow update for own profile" ON employee_profile
    FOR UPDATE USING (auth.uid()::text = user_id::text);

-- Leave request policies
CREATE POLICY "Allow read access to authenticated users" ON leave_request
    FOR SELECT USING (auth.uid()::text IS NOT NULL);

CREATE POLICY "Allow insert for authenticated users" ON leave_request
    FOR INSERT WITH CHECK (auth.uid()::text IS NOT NULL);

CREATE POLICY "Allow update for own requests or HR" ON leave_request
    FOR UPDATE USING (auth.uid()::text = employee_id::text OR auth.role() = 'service_role');

-- Similar policies can be added for other tables based on your requirements

-- ============================================
-- INSERT DEFAULT ADMIN USER (OPTIONAL)
-- ============================================
-- Uncomment and modify to create a default admin user
-- Note: You'll need to hash the password using Argon2 in your application first

-- INSERT INTO "user" (username, email, password_hash, department, role)
-- VALUES ('admin', 'admin@school.edu', 'YOUR_HASHED_PASSWORD_HERE', 'Administration', 'admin');

-- ============================================
-- GRANT PERMISSIONS
-- ============================================

-- Grant necessary permissions to the database user
-- Adjust the role name based on your Supabase setup
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO postgres;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO postgres;
