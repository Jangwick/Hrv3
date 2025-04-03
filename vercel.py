"""
Vercel handler file - specifically for Vercel's serverless function support
"""
from app import create_app

# Create and expose the Flask application for Vercel
app = create_app()

# Vercel serverless function handler
def handler(request, response):
    return app(request, response)
