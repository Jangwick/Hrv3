"""
WSGI entry point for the application.
This file is used by Gunicorn and other WSGI servers.
"""
from app import create_app

# Create the Flask application
application = create_app()

# For compatibility with some platforms
app = application

if __name__ == "__main__":
    application.run()
