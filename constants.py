"""
Constants used throughout the HR application
"""

# SSS (Social Security System) constants - effective January 1, 2025
SSS_CONTRIBUTION_RATE = 0.15  # 15% of Monthly Salary Credit (MSC)
SSS_EMPLOYER_SHARE = 0.10     # Employer contributes 10% of MSC
SSS_EMPLOYEE_SHARE = 0.05     # Employee contributes 5% of MSC
SSS_MAX_MSC = 35000.00        # Maximum Monthly Salary Credit

# PAG-IBIG constants
PAGIBIG_EMPLOYEE_RATE_LOW = 0.01   # 1% for monthly income ≤ P1,500
PAGIBIG_EMPLOYEE_RATE_STD = 0.02   # 2% for monthly income > P1,500
PAGIBIG_EMPLOYER_RATE = 0.02       # Employer contributes 2% regardless of income
PAGIBIG_LOW_INCOME_THRESHOLD = 1500.00

# PHILHEALTH constants (Example rates for 2024 - Verify with official sources)
PHILHEALTH_RATE = 0.05  # 5.0% premium rate (effective Jan 2025)
PHILHEALTH_MIN_INCOME_BASE = 10000.00 # Salary Floor
PHILHEALTH_MAX_INCOME_CEILING = 100000.00 # Salary Ceiling
# Employee and Employer share the premium 50/50
PHILHEALTH_EMPLOYEE_SHARE_RATE = 0.50
PHILHEALTH_EMPLOYER_SHARE_RATE = 0.50

# COMMON DEDUCTION DEFAULTS (Examples - Adjust as needed)
DEFAULT_INCOME_TAX_RATE = 0.12  # Example: 12% withholding tax rate
DEFAULT_RETIREMENT_RATE = 0.05  # Example: 5% retirement contribution rate
DEFAULT_HEALTH_INSURANCE_PREMIUM = 125.00 # Example: Fixed monthly premium
DEFAULT_PROFESSIONAL_DUES = 45.00       # Example: Fixed monthly dues
