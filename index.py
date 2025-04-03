"""
Main entry point for Vercel serverless deployment of the HR System.
"""
from app import create_app

# Create the Flask application
app = create_app()

# This handler is required for Vercel - it maps HTTP requests to your Flask app
def handler(request, response):
    return app(request, response)

# This enables local development as well
if __name__ == '__main__':
    app.run(debug=True)
