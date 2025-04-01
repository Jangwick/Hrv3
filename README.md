# HR Management System v2

A comprehensive human resources management platform built with Python, Flask, and modern web technologies.

## 📋 Table of Contents

- [HR Management System v2](#hr-management-system-v2)
  - [📋 Table of Contents](#-table-of-contents)
  - [🔍 Overview](#-overview)
  - [✨ Features](#-features)
  - [💻 Technology Stack](#-technology-stack)
  - [📁 Project Structure](#-project-structure)
  - [🚀 Installation](#-installation)
  - [🔐 Environment Variables](#-environment-variables)
  - [🖥️ Usage](#️-usage)
  - [👥 User Roles](#-user-roles)
  - [📊 Modules](#-modules)
    - [Employee Management](#employee-management)
    - [Attendance Tracking](#attendance-tracking)
    - [Leave Management](#leave-management)
    - [Training Programs](#training-programs)
    - [Teaching Units](#teaching-units)
    - [Payroll Processing](#payroll-processing)
  - [📈 Reports](#-reports)
  - [🔄 API Integration](#-api-integration)
  - [🎨 Theme Support](#-theme-support)
  - [🛢️ Database Schema](#️-database-schema)
  - [🔒 Security Features](#-security-features)
  - [⚠️ Troubleshooting](#️-troubleshooting)
  - [👨‍💻 Development Workflow](#-development-workflow)
  - [🤝 Contributing](#-contributing)
  - [📄 License](#-license)

## 🔍 Overview

HR Management System v2 is a comprehensive solution for managing all aspects of human resources operations. The platform integrates employee management, attendance tracking, leave management, training administration, and payroll processing into a single cohesive system with an intuitive user interface.

## ✨ Features

- **Employee Management**: Comprehensive employee profiles, department organization, and role management
- **Attendance Tracking**: Record and analyze employee attendance with detailed analytics
- **Leave Management**: Request, approve, and track various types of leave with automated balance calculations
- **Training Programs**: Create, manage, and track training programs with feedback collection
- **Teaching Units**: Track academic units, attendance, and calculate compensation
- **Payroll Processing**: Generate and manage employee payroll with customizable components
- **Dynamic Reporting**: Generate detailed reports with data visualization and export capabilities
- **AI-Powered Chatbot**: Integrated Google Gemini chatbot for answering HR queries
- **Theme Support**: Light and dark mode with system preference detection
- **Role-Based Access Control**: Different views and permissions for employees, HR staff, and administrators
- **Responsive Design**: Works seamlessly across desktop and mobile devices

## 💻 Technology Stack

- **Backend**: Python with Flask web framework
- **Database**: SQLite for data storage and retrieval
- **Frontend**:
  - HTML/CSS/JavaScript
  - Bootstrap 5.3 for UI components
  - Chart.js for data visualization
- **File Storage**: Cloudinary for document and image storage
- **Authentication**: JWT-based authentication
- **AI Integration**: Google Gemini for chatbot functionality
- **Other Libraries**:
  - Flatpickr for date picking
  - ReportLab for PDF generation
  - Font Awesome for icons

## 📁 Project Structure

```
HRv2/
├── routes/                     # Route handlers for different modules
│   ├── admin.py                # Admin panel routes and actions
│   ├── attendance.py           # Attendance tracking functionality
│   ├── dashboard.py            # Dashboard views
│   ├── employees.py            # Employee management
│   ├── hr.py                   # HR staff specific functions
│   ├── leaves.py               # Leave management
│   ├── payroll.py              # Payroll processing
│   ├── reports.py              # Report generation
│   ├── teaching.py             # Teaching unit management
│   └── training.py             # Training program management
│
├── static/                     # Static assets
│   ├── css/                    # Stylesheets
│   │   ├── navigation.css      # Navigation styling
│   │   ├── theme-toggle.css    # Theme toggle components
│   │   └── ui-kit.css          # Core UI components
│   │
│   ├── js/                     # JavaScript files
│   │   ├── attendance-charts.js # Chart functions for attendance
│   │   ├── dashboard-enhancements.js # Dashboard interactivity
│   │   ├── navigation.js        # Navigation behavior
│   │   ├── theme.js             # Complete theme implementation
│   │   ├── theme-manager.js     # Theme switching logic
│   │   └── theme-preload.js     # Initial theme setup
│   │
│   └── img/                    # Images and icons
│
├── templates/                  # HTML templates
│   ├── admin/                  # Admin panel templates
│   │   └── index.html          # Admin dashboard
│   │
│   ├── attendance/             # Attendance-related templates
│   │   ├── analytics.html      # Attendance analytics
│   │   ├── index.html          # Attendance main page
│   │   └── report.html         # Attendance reporting
│   │
│   ├── components/             # Reusable UI components
│   │   └── back_button.html    # Back navigation component
│   │
│   ├── employees/              # Employee management templates
│   │   └── employee_list_pdf.html # PDF export template
│   │
│   ├── leaves/                 # Leave management templates
│   │   ├── index.html          # Leave requests list
│   │   ├── new.html            # Create new leave request
│   │   ├── process.html        # Process leave requests
│   │   └── view.html           # View leave request details
│   │
│   ├── payroll/                # Payroll templates
│   │   ├── new.html            # Create new payroll
│   │   └── process.html        # Process payroll
│   │
│   ├── teaching/               # Teaching unit templates
│   │   ├── edit.html           # Edit teaching unit
│   │   ├── index.html          # Teaching units list
│   │   ├── new.html            # Create new teaching unit
│   │   └── view.html           # View teaching unit details
│   │
│   ├── base.html               # Base template with layout
│   ├── dashboard.html          # Main dashboard
│   └── index.html              # Landing page
│
├── models.py                   # Database models and schemas
├── forms.py                    # WTForms definitions for all modules
├── chatbot.py                  # Google Gemini chatbot integration
├── cloud_config.py             # Cloudinary storage configuration
│
├── instance/                   # SQLite database file location
│   └── hr_system.db            # SQLite database
│
├── migrations/                 # Database migration scripts
├── .env                        # Environment variables
├── .gitignore                  # Git ignore file
├── app.py                      # Application entry point
├── notes.md                    # Development notes
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

## 🚀 Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd HRv2
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables (see [Environment Variables](#environment-variables))

5. Initialize the database:
   ```bash
   flask db upgrade
   ```

6. Run the application:
   ```bash
   python app.py
   ```

## 🔐 Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Cloudinary Configuration
CLOUDINARY_URL=cloudinary://your_api_key:your_api_secret@your_cloud_name
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key

# Flask Configuration
FLASK_SECRET_KEY=your_secret_key
FLASK_ENV=development # or production
DATABASE_URL=sqlite:///instance/hr_system.db
```

## 🖥️ Usage

After installation, access the application at `http://localhost:5000` (or the configured port).

1. Log in with your credentials
2. Navigate through the various modules using the sidebar navigation
3. Use the dashboard for quick access to key information and actions

## 👥 User Roles

The system supports three main user roles:

1. **Employee**:
   - Access to personal profile
   - Submit leave requests
   - View attendance records
   - Participate in training programs
   - Access payslips

2. **HR Staff**:
   - All employee permissions
   - Manage employee records
   - Process leave requests
   - Generate reports
   - Manage training programs
   - Process payroll

3. **Administrator**:
   - All HR staff permissions
   - System configuration
   - User management
   - Role assignments
   - Database maintenance

## 📊 Modules

### Employee Management
Maintain comprehensive employee records including personal details, employment history, documents, and department assignments.

### Attendance Tracking
Track employee attendance with check-in/check-out functionality, analytics dashboard, and reporting capabilities.

### Leave Management
Process leave requests with configurable approval workflows, leave balances, and calendar visualization.

### Training Programs
Create and manage training programs with enrollment tracking, feedback collection, and effectiveness analysis.

### Teaching Units
Track teaching assignments, calculate academic units, record attendance, and process related payments.

### Payroll Processing
Generate payroll with salary components, deductions, unit-based payments, and automated calculations.

## 📈 Reports

The system offers several built-in reports:

1. **Salary Report**: Analyze employee compensation with filtering options
2. **Employee Demographics**: Visualize employee distribution across departments, roles, etc.
3. **Time Off Analysis**: Track leave patterns and department-wise utilization
4. **Training Analytics**: Measure training program effectiveness and participation
5. **Attendance Reports**: Analyze attendance patterns and compliance

All reports include data visualization, filtering options, and export capabilities (PDF, CSV, Excel).

## 🔄 API Integration

The system integrates with:

1. **Cloudinary**: For file storage and management
2. **Google Gemini**: For AI-powered chatbot functionality

## 🎨 Theme Support

The system supports:
- Light mode
- Dark mode
- System preference detection
- Theme persistence using localStorage

## 🛢️ Database Schema

The system uses SQLite for data storage with the following key tables:

1. **users**: User accounts and authentication details
   - id, username, email, password_hash, role, is_active, created_at, updated_at

2. **employees**: Employee profile information
   - id, user_id, first_name, last_name, department_id, position, hire_date, birthdate, address, phone, emergency_contact

3. **departments**: Organization structure
   - id, name, description, manager_id

4. **attendance_records**: Employee attendance tracking
   - id, employee_id, date, time_in, time_out, status, teaching_unit_id

5. **leave_requests**: Employee time off tracking
   - id, employee_id, leave_type, start_date, end_date, duration, reason, status, approver_id, approval_date, approval_comment

6. **leave_balances**: Employee leave allowances
   - id, employee_id, leave_type, year, allocated, used, remaining

7. **training_programs**: Training course details
   - id, title, description, category, instructor, start_date, end_date, location, max_participants, status

8. **training_enrollments**: Employee training participation
   - id, employee_id, program_id, enrollment_date, completion_date, status, feedback_id

9. **teaching_units**: Academic teaching assignments
   - id, title, employee_id, description, unit_value, rate_per_unit, start_date, end_date, status, total_hours

10. **payroll_records**: Employee compensation
    - id, employee_id, period_start, period_end, base_salary, teaching_pay, deductions, net_pay, status, payment_date

Database migrations are managed using Flask-Migrate to facilitate schema evolution over time.

## 🔒 Security Features

The system implements several security measures:

1. **Authentication**:
   - Password hashing using bcrypt
   - JSON Web Token (JWT) for API authentication
   - Role-based access control
   - Session timeout and management

2. **Data Protection**:
   - CSRF protection using Flask-WTF
   - Input validation and sanitization
   - Parameterized SQL queries to prevent injection attacks

3. **Frontend Security**:
   - Content Security Policy (CSP) headers
   - HTTPS enforcement
   - XSS protection via proper output escaping

4. **Sensitive Data Handling**:
   - Salary information visible only to HR and administrators
   - Personal information access restricted to authorized personnel
   - Audit logging for sensitive operations

## ⚠️ Troubleshooting

Common issues and their solutions:

1. **Database Connection Issues**:
   - Ensure the SQLite database file exists in the instance folder
   - Check file permissions on the database file
   - Run database migrations using `flask db upgrade`

2. **File Upload Problems**:
   - Verify Cloudinary credentials in the .env file
   - Check internet connectivity
   - Ensure file size is within limits (max 10MB)

3. **Theme Switching Not Working**:
   - Clear browser cache and local storage
   - Ensure JavaScript is enabled
   - Check browser console for errors

4. **Report Generation Errors**:
   - Install required dependencies for ReportLab
   - Ensure data exists for the selected report parameters
   - Check log files for specific error messages

5. **Chatbot Functionality Issues**:
   - Verify Google Gemini API key is correct
   - Check internet connectivity
   - Review rate limit status if queries are failing

## 👨‍💻 Development Workflow

Guidelines for developers working on the project:

1. **Code Style**:
   - Follow PEP 8 for Python code
   - Use camelCase for JavaScript functions and variables
   - Maintain consistent indentation (4 spaces for Python, 2 spaces for HTML/JS/CSS)

2. **Git Workflow**:
   - Create feature branches from `development`
   - Use descriptive commit messages
   - Squash commits before merging to main branches
   - Tag releases with semantic versioning

3. **Testing**:
   - Write unit tests for all new features
   - Run tests before submitting pull requests
   - Maintain minimum 80% code coverage

4. **Documentation**:
   - Update README.md for major changes
   - Document all functions and classes with docstrings
   - Keep API documentation current

5. **Database Changes**:
   - Create migration scripts for all schema changes
   - Test migrations in development before applying to production
   - Backup database before applying migrations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

© 2025 HR Management System. All rights reserved.
