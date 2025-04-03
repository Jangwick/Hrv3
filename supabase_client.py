import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Get Supabase credentials from environment variables
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

# Create Supabase client
supabase: Client = create_client(url, key)

# Function to get PostgreSQL connection string for SQLAlchemy
def get_db_url():
    """
    Generates a PostgreSQL connection string for SQLAlchemy using Supabase credentials
    """
    db_url = os.environ.get("DATABASE_URL")
    
    # If DATABASE_URL is provided directly, use it
    if db_url:
        return db_url
    
    # Otherwise, construct from individual components
    db_host = os.environ.get("SUPABASE_DB_HOST")
    db_port = os.environ.get("SUPABASE_DB_PORT")
    db_name = os.environ.get("SUPABASE_DB_NAME")
    db_user = os.environ.get("SUPABASE_DB_USER")
    db_password = os.environ.get("SUPABASE_DB_PASSWORD")
    
    # Construct connection string
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
