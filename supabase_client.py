import os
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Try to import supabase - optional if using Railway's built-in PostgreSQL
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None

# Get Supabase credentials from environment variables (optional)
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY") or os.environ.get("NEXT_PUBLIC_SUPABASE_ANON_KEY")

# Create Supabase client if credentials are available
supabase = None
if SUPABASE_AVAILABLE and url and key:
    try:
        supabase = create_client(url, key)
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {e}")
        supabase = None

# Function to get PostgreSQL connection string for SQLAlchemy
def get_db_url():
    """
    Generates a PostgreSQL connection string for SQLAlchemy.
    Works with Railway (DATABASE_URL), Supabase, or individual env vars.
    """
    # Try DATABASE_URL first (Railway, Render, Heroku, etc.)
    db_url = os.environ.get("DATABASE_URL")
    
    # Try Supabase connection strings next
    if not db_url:
        db_url = os.environ.get("POSTGRES_URL_NON_POOLING") or os.environ.get("POSTGRES_URL")
    
    if db_url:
        # Replace 'postgres://' with 'postgresql://' as SQLAlchemy requires 'postgresql'
        if db_url.startswith('postgres://'):
            db_url = 'postgresql://' + db_url[len('postgres://'):]
        return db_url
    
    # Otherwise, construct from individual components
    db_host = os.environ.get("POSTGRES_HOST") or os.environ.get("DB_HOST")
    # Use the default port 5432 if not specified or invalid
    try:
        db_port = int(os.environ.get("SUPABASE_DB_PORT") or os.environ.get("DB_PORT") or "5432")
    except (ValueError, TypeError):
        db_port = 5432
    
    db_name = os.environ.get("POSTGRES_DATABASE") or os.environ.get("DB_NAME") or "postgres"
    db_user = os.environ.get("POSTGRES_USER") or os.environ.get("DB_USER")
    db_password = os.environ.get("POSTGRES_PASSWORD") or os.environ.get("DB_PASSWORD")
    
    if not db_host:
        raise ValueError("Database connection is required. Set DATABASE_URL or POSTGRES_HOST environment variable.")
    
    # Construct connection string with the correct 'postgresql://' prefix
    return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
