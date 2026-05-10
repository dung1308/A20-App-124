#!/bin/bash
# ============================================================================
# PostgreSQL Database Setup for VinUni Backend
# ============================================================================
# Run this script to set up PostgreSQL database for production
#
# Usage:
#   bash setup_postgres.sh
#
# Prerequisites:
#   - PostgreSQL installed and running
#   - psql command available
#   - Run as user with PostgreSQL superuser privileges
# ============================================================================

set -e  # Exit on error

# Configuration
DB_NAME="vinuni_backend"
DB_USER="vinuni_user"
DB_PASSWORD="${DB_PASSWORD:-vinuni_secure_password_123}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "=========================================="
echo "VinUni Backend PostgreSQL Setup"
echo "=========================================="
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Host: $DB_HOST:$DB_PORT"
echo ""

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "Error: psql command not found. Please install PostgreSQL client."
    exit 1
fi

# Create database and user
echo "Creating PostgreSQL database and user..."

psql -h "$DB_HOST" -U postgres -c "
CREATE DATABASE $DB_NAME
    WITH
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;
"

psql -h "$DB_HOST" -U postgres -c "
CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
"

# Configure user permissions
echo "Configuring user permissions..."

psql -h "$DB_HOST" -U postgres -c "
ALTER ROLE $DB_USER SET client_encoding TO 'utf8';
ALTER ROLE $DB_USER SET default_transaction_isolation TO 'read committed';
ALTER ROLE $DB_USER SET default_transaction_deferrable TO on;
ALTER ROLE $DB_USER SET default_transaction_read_only TO off;
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
"

# Create extensions
echo "Creating PostgreSQL extensions..."

psql -h "$DB_HOST" -U postgres -d "$DB_NAME" -c "
CREATE EXTENSION IF NOT EXISTS uuid-ossp;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
"

echo ""
echo "=========================================="
echo "✓ PostgreSQL setup completed successfully!"
echo "=========================================="
echo ""
echo "Connection string:"
echo "  postgresql://$DB_USER:PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "Add to .env file:"
echo "  DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo ""
echo "Next steps:"
echo "  1. Update .env file with the connection string"
echo "  2. Run: python db_init.py"
echo "  3. Start the backend: uvicorn main:app --reload"
echo ""
