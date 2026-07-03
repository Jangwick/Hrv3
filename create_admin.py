#!/usr/bin/env python3
"""
Script to generate an Argon2 password hash for admin account creation.
Run this script to get a hashed password, then use the SQL in Supabase.
"""
from argon2 import PasswordHasher
import getpass

ph = PasswordHasher()

def generate_hash():
    """Generate Argon2 hash for a password"""
    print("Admin Account Password Generator")
    print("=" * 40)
    
    # Get password securely
    password = getpass.getpass("Enter admin password: ")
    confirm = getpass.getpass("Confirm password: ")
    
    if password != confirm:
        print("Passwords do not match!")
        return None
    
    if len(password) < 8:
        print("Password must be at least 8 characters!")
        return None
    
    # Generate hash
    password_hash = ph.hash(password)
    
    print("\n" + "=" * 40)
    print("Password hash generated successfully!")
    print("=" * 40)
    print(f"\nHash: {password_hash}")
    
    # Generate SQL
    print("\n" + "=" * 40)
    print("SQL to run in Supabase:")
    print("=" * 40)
    username = input("Enter admin username (default: admin): ") or "admin"
    email = input("Enter admin email (default: admin@school.edu): ") or "admin@school.edu"
    department = input("Enter department (default: Administration): ") or "Administration"
    
    sql = f"""INSERT INTO "user" (username, email, password_hash, department, role)
VALUES ('{username}', '{email}', '{password_hash}', '{department}', 'admin');"""
    
    print(f"\n{sql}")
    print("\nCopy and paste this SQL into your Supabase SQL Editor.")
    
    return password_hash

if __name__ == "__main__":
    generate_hash()
