"""
Main entry point for Vercel serverless deployment of the HR System.
"""
from app import create_app

# Create the Flask application
app = create_app()

# Vercel will look for either an 'app' variable or a 'handler' function
# For Flask applications, exposing the 'app' variable is the recommended approach

# This enables local development as well
if __name__ == '__main__':
    app.run(debug=True)
