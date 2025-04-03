"""
Vercel serverless function entry point for the HR System.
"""
import sys
import os

# Add the parent directory to path so we can import our app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the application factory
from app import create_app

# Create the app instance
app = create_app()

# This is required for Vercel - the handler for serverless function
def handler(req, res):
    # Forward the request to the Flask app
    return app(req, res)

# Serverless function handler for Vercel
handler.app = app
