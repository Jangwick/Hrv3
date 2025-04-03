import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Get Supabase credentials from environment variables
url: str = os.environ.get("SUPABASE_URL")
# Try to get SUPABASE_KEY first, fall back to NEXT_PUBLIC_SUPABASE_ANON_KEY if not found
key: str = os.environ.get("SUPABASE_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")

# Validate credentials
if not url:
    raise ValueError("SUPABASE_URL environment variable is required")
if not key:
    raise ValueError("Either SUPABASE_KEY or NEXT_PUBLIC_SUPABASE_ANON_KEY environment variable is required")

# Create Supabase client
supabase: Client = create_client(url, key)

# Function to get PostgreSQL connection string for SQLAlchemy
def get_db_url():
    """
    Generates a PostgreSQL connection string for SQLAlchemy using Supabase credentials
    """
    db_url = os.environ.get("POSTGRES_URL_NON_POOLING")
    
    # If DATABASE_URL is provided directly, use it
    if db_url:
        return db_url
    
    # Otherwise, construct from individual components
    db_host = os.environ.get("SUPABASE_DB_HOST")
    # Use the default port 5432 if not specified or invalid
    try:
        db_port = int(os.environ.get("SUPABASE_DB_PORT", "5432"))
    except (ValueError, TypeError):
        db_port = 5432
    
    db_name = os.environ.get("SUPABASE_DB_NAME", "postgres")
    db_user = os.environ.get("SUPABASE_DB_USER", "postgres")
    db_password = os.environ.get("SUPABASE_DB_PASSWORD", "")
    
    if not db_host:
        raise ValueError("Database host is required. Set SUPABASE_DB_HOST environment variable.")
    
    # Construct connection string
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
