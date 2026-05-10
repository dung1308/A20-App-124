# Quick Database Setup for VinUni Backend

## Development (SQLite) - 2 Minutes

### 1. Set environment variables in `.env`:
```env
DATABASE_URL=sqlite:///./vinuni_match.db
USE_MOCK=True
```

### 2. Initialize database:
```bash
cd app/backend
python db_init.py
```

### 3. Start server:
```bash
uvicorn main:app --reload
```

**That's it!** SQLite will create `vinuni_match.db` automatically.

---

## Production (PostgreSQL) - 5 Minutes

### Windows Users:
```bash
# Run setup script
python scripts/setup_postgres_windows.py --password mySecurePass123
```

### Mac/Linux Users:
```bash
# Run setup script
bash scripts/setup_postgres.sh
```

### Manual Setup:
```bash
# Connect to PostgreSQL
psql -U postgres

# Run these commands:
CREATE DATABASE vinuni_backend;
CREATE USER vinuni_user WITH PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE vinuni_backend TO vinuni_user;
\q
```

### Then configure backend:
```env
DATABASE_URL=postgresql://vinuni_user:your_password_here@localhost:5432/vinuni_backend
USE_MOCK=False
GEMINI_API_KEY=your_api_key
```

### Initialize:
```bash
python db_init.py
```

---

## Database Tables Created

| Table | Purpose |
|-------|---------|
| `users` | Student accounts |
| `chat_sessions` | Conversation groups |
| `chat_messages` | Individual messages |
| `students` | Extended profiles (GPA, scores) |
| `audit_logs` | Compliance trail |
| `security_events` | Guardrail logs |

---

## Verify Setup

```bash
# Check SQLite
sqlite3 app/backend/vinuni_match.db ".tables"

# Check PostgreSQL  
psql -U vinuni_user -d vinuni_backend -c "\dt"
```

---

## Common Commands

```bash
# Recreate database (dev only)
python app/backend/db_init.py --recreate

# Backup SQLite
cp app/backend/vinuni_match.db vinuni_match.db.backup

# Backup PostgreSQL
pg_dump -U vinuni_user -d vinuni_backend > backup.sql

# Query users
psql -U vinuni_user -d vinuni_backend -c "SELECT * FROM users;"
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `FileNotFoundError: vinuni_match.db` | Run `python db_init.py` |
| `Connection refused` (PostgreSQL) | Check PostgreSQL is running and DATABASE_URL is correct |
| `psql: command not found` | Add PostgreSQL bin folder to PATH |
| `Table already exists` | Run `python db_init.py --recreate` |

---

## Full Documentation

See [DATABASE_SETUP.md](app/backend/DATABASE_SETUP.md) for detailed information about:
- Advanced PostgreSQL configuration
- Database monitoring
- Query examples
- Performance optimization
- Migration strategies
