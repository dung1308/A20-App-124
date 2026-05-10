"""
setup_postgres_windows.py
=========================
PostgreSQL database setup script for Windows users.

Usage:
    python setup_postgres_windows.py [--password YOUR_PASSWORD]

Options:
    --password: Set custom database password (default: generated automatically)
"""

import subprocess
import sys
import os
from pathlib import Path

# Configuration
DB_NAME = "vinuni_backend"
DB_USER = "vinuni_user"
DB_HOST = "localhost"
DB_PORT = "5432"

def generate_password():
    """Generate a secure random password."""
    import secrets
    import string
    chars = string.ascii_letters + string.digits + "!@#$%"
    return "".join(secrets.choice(chars) for _ in range(16))

def check_postgres_installed():
    """Check if PostgreSQL is installed and psql is available."""
    try:
        result = subprocess.run(
            ["psql", "--version"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except FileNotFoundError:
        return False

def run_sql_command(sql, db=None):
    """Execute SQL command via psql."""
    try:
        cmd = ["psql", "-U", "postgres", "-h", DB_HOST, "-p", DB_PORT]
        if db:
            cmd.extend(["-d", db])
        cmd.extend(["-c", sql])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Failed to execute SQL: {e}")
        return False

def main():
    """Main setup function."""
    
    print("=" * 50)
    print("VinUni Backend PostgreSQL Setup (Windows)")
    print("=" * 50)
    print()
    
    # Parse command line arguments
    db_password = None
    if "--password" in sys.argv:
        idx = sys.argv.index("--password")
        if idx + 1 < len(sys.argv):
            db_password = sys.argv[idx + 1]
    
    if not db_password:
        db_password = generate_password()
        print(f"Generated secure password: {db_password}")
    
    print(f"Database: {DB_NAME}")
    print(f"User: {DB_USER}")
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print()
    
    # Check PostgreSQL installation
    print("Checking PostgreSQL installation...")
    if not check_postgres_installed():
        print("✗ PostgreSQL is not installed or psql is not in PATH")
        print("Please install PostgreSQL from https://www.postgresql.org/download/windows/")
        sys.exit(1)
    print("✓ PostgreSQL found")
    print()
    
    # Create database
    print(f"Creating database '{DB_NAME}'...")
    sql = f"""
    CREATE DATABASE {DB_NAME}
        WITH
        ENCODING = 'UTF8'
        TEMPLATE = template0;
    """
    if not run_sql_command(sql):
        print("✗ Failed to create database")
        sys.exit(1)
    print("✓ Database created")
    
    # Create user
    print(f"Creating user '{DB_USER}'...")
    sql = f"CREATE USER {DB_USER} WITH PASSWORD '{db_password}';"
    if not run_sql_command(sql):
        print("✗ Failed to create user")
        sys.exit(1)
    print("✓ User created")
    
    # Grant privileges
    print("Granting privileges...")
    sql = f"GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};"
    if not run_sql_command(sql, DB_NAME):
        print("✗ Failed to grant privileges")
        sys.exit(1)
    print("✓ Privileges granted")
    
    # Create extensions
    print("Creating PostgreSQL extensions...")
    extensions = ["uuid-ossp", "pg_trgm"]
    for ext in extensions:
        sql = f"CREATE EXTENSION IF NOT EXISTS {ext};"
        if not run_sql_command(sql, DB_NAME):
            print(f"⚠ Could not create extension {ext} (may already exist)")
    print("✓ Extensions created")
    
    # Success
    print()
    print("=" * 50)
    print("✓ PostgreSQL setup completed successfully!")
    print("=" * 50)
    print()
    print(f"Connection string:")
    print(f"  postgresql://{DB_USER}:{db_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print()
    print(f"Add to .env file:")
    print(f"  DATABASE_URL=postgresql://{DB_USER}:{db_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
    print()
    print("Next steps:")
    print("  1. Save the connection string above")
    print("  2. Update .env file with DATABASE_URL")
    print("  3. Run: python db_init.py")
    print("  4. Start the backend: uvicorn main:app --reload")
    print()

if __name__ == "__main__":
    main()
