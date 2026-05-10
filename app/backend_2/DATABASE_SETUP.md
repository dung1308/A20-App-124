# VinUni Backend Database Setup Guide

This guide explains how to set up and manage the database for the VinUni Admission Assistant backend.

## Overview

The backend uses **SQLAlchemy ORM** with support for both:
- **SQLite** (development - recommended for local testing)
- **PostgreSQL** (production)

## 1. Database Models

The database includes the following tables:

### Core Tables
- **users**: Student accounts and basic profile info
- **chat_sessions**: Groups related chat messages
- **chat_messages**: Individual conversation turns

### CRM & Profiling
- **students**: Extended student profiles (GPA, test scores, preferences)

### Compliance & Security
- **audit_logs**: Records all API operations for compliance
- **security_events**: Logs guardrail violations and suspicious activity

## 2. Quick Start (Development with SQLite)

### 2.1 Environment Configuration

Create a `.env` file in the `backend/` directory:

```env
# Use SQLite for local development
DATABASE_URL=sqlite:///./vinuni_match.db
USE_MOCK=True
LOG_LEVEL=INFO
```

### 2.2 Initialize Database

Run the initialization script:

```bash
cd backend
python db_init.py
```

Expected output:
```
2026-05-05 10:30:45 - __main__ - INFO - Database initialized successfully: sqlite:///./vinuni_match.db
2026-05-05 10:30:45 - __main__ - INFO - Tables created: users, chat_messages, chat_sessions, students, audit_logs, security_events
```

### 2.3 Start the Server

The database will be automatically initialized when you start the server:

```bash
uvicorn main:app --reload
```

## 3. Production Setup (PostgreSQL)

### 3.1 Create PostgreSQL Database

```bash
# Connect to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE vinuni_db;
CREATE USER vinuni_user2 WITH PASSWORD 'your pass';
ALTER ROLE vinuni_user2 SET client_encoding TO 'utf8';
ALTER ROLE vinuni_user2 SET default_transaction_isolation TO 'read committed';
ALTER ROLE vinuni_user2 SET default_transaction_deferrable TO on;
ALTER ROLE vinuni_user2 SET default_transaction_read_only TO off;
GRANT ALL PRIVILEGES ON DATABASE vinuni_db TO vinuni_user2;
\q
```

### 3.2 Update Environment

Create `.env` in `backend/`:

```env
DATABASE_URL=postgresql://vinuni_user2:13082001@localhost:5432/vinuni_db
USE_MOCK=False
OPENAI_API_KEY=your_api_key_here
LOG_LEVEL=INFO
```

### 3.3 Initialize Database

```bash
python db_init.py
```

## 4. Database Operations

### Check Current Status

```bash
# View schema
sqlite3 vinuni_match.db ".schema"

# Or for PostgreSQL
psql -U vinuni_user -d vinuni_db -c "\d"
```

### Recreate Database (Development Only)

```bash
python db_init.py --recreate
```

This will:
1. Drop all existing tables
2. Recreate them with fresh schema

⚠️ **WARNING**: This deletes all data!

### Backup SQLite Database

```bash
cp vinuni_match.db vinuni_match.db.backup
```

### Backup PostgreSQL Database

```bash
pg_dump -U vinuni_user -d vinuni_backend > backup.sql
```

### Restore PostgreSQL Database

```bash
psql -U vinuni_user -d vinuni_backend < backup.sql
```

## 5. Accessing Database in Code

### Using Dependency Injection (Recommended)

```python
from fastapi import Depends
from database import get_db_session
from sqlalchemy.orm import Session

@app.get("/api/endpoint")
def my_endpoint(db: Session = Depends(get_db_session)):
    # Query database
    from models.schemas import User
    users = db.query(User).all()
    return users
```

### Direct Service Access

```python
from services.db_service import DBService

db_service = DBService()
db_service.save_message("user123", "assistant", "Hello!")
history = db_service.get_history("user123")
```

## 6. Database Monitoring

### View Logs

```bash
# Check initialization logs
tail -f logs/app.log | grep "database"
```

### Query Examples

#### SQLite
```bash
sqlite3 vinuni_match.db
sqlite> SELECT * FROM users;
sqlite> SELECT COUNT(*) FROM chat_messages;
sqlite> .quit
```

#### PostgreSQL
```bash
psql -U vinuni_user -d vinuni_backend

# View all users
SELECT * FROM users;

# Get chat history for user
SELECT * FROM chat_messages WHERE user_id = 'user123' ORDER BY timestamp DESC;

# Check audit logs
SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 10;
```

## 7. Migration Strategy (Advanced)

For production database schema updates, consider using **Alembic**:

```bash
pip install alembic

# Initialize Alembic
alembic init alembic

# Create a migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head
```

## 8. Troubleshooting

### Issue: "FileNotFoundError: vinuni_match.db"

**Solution**: Run `python db_init.py` first

### Issue: "Connection refused" (PostgreSQL)

**Solution**: 
- Check PostgreSQL is running: `sudo systemctl status postgresql`
- Verify `DATABASE_URL` in `.env`

### Issue: "Table already exists"

**Solution**: 
```bash
python db_init.py --recreate
```

### Issue: Database locked (SQLite)

**Solution**: Close other connections or restart the server

## 9. Connection Pooling

### SQLite
- Uses `StaticPool` for development (single-threaded)
- Suitable for local development only

### PostgreSQL
- Uses `QueuePool` by default
- Configurable pool size in `database.py`:
  ```python
  engine = create_engine(
      DATABASE_URL,
      pool_size=10,
      max_overflow=20
  )
  ```

## 10. Performance Tips

1. **Add Indexes** for frequently queried fields:
   ```python
   user_id = Column(String, index=True, ...)
   timestamp = Column(DateTime, index=True, ...)
   ```

2. **Pagination** for large result sets:
   ```python
   messages = db.query(ChatMessage).offset(0).limit(20).all()
   ```

3. **Monitor Query Performance**:
   ```python
   from sqlalchemy import event
   
   @event.listens_for(Engine, "before_cursor_execute")
   def receive_before_cursor_execute(conn, cursor, statement, params, context, executemany):
       logger.info(f"Executing: {statement}")
   ```

## References

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [FastAPI Database](https://fastapi.tiangolo.com/advanced/sql-databases/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
