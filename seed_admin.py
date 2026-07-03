import psycopg2
from argon2 import PasswordHasher

ph = PasswordHasher()
password_hash = ph.hash('admin123')

conn = psycopg2.connect('postgresql://postgres:HlVzejqkKeZEeXcONCPvINgqNrtOtZob@shinkansen.proxy.rlwy.net:53580/railway')
cur = conn.cursor()

cur.execute(
    'INSERT INTO "user" (username, email, password_hash, department, role) VALUES (%s, %s, %s, %s, %s)',
    ('admin', 'admin@school.edu', password_hash, 'Administration', 'admin')
)

conn.commit()
print("Admin account created successfully!")
print("Username: admin")
print("Password: admin123")
print("Email: admin@school.edu")
conn.close()
