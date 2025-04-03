"""
Vercel serverless entry point for the HR System.
"""
from app import create_app

# Create Flask application
app = create_app()

# Add a simple health check route
@app.route('/health')
def health_check():
    return {"status": "ok", "message": "Service is running"}

# Required for Vercel - don't use handler function
# Export the Flask app directly

# For local development
if __name__ == "__main__":
    app.run(debug=True)
