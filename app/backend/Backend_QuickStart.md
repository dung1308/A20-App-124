# VinUni Backend Quick Start Guide

This guide helps you set up and run the VinUni Admission Assistant backend.

## 1. Prerequisites
- Python 3.9 or higher
- `pip` (Python package installer)
- PostgreSQL database

## 2. Install PostgreSQL

### On Windows:
1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. Run the installer and follow the setup wizard
3. Note down the password you set for the postgres user
4. Ensure PostgreSQL is running (check Services or pgAdmin)

### On macOS:
```bash
brew install postgresql
brew services start postgresql
createdb vinuni_db
```

### On Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo -u postgres createdb vinuni_db
```

## 3. Environment Setup

Navigate to the backend directory and create a virtual environment:

```bash
cd backend
python -m venv venv

# Activate on Windows:
.\venv\Scripts\activate

# Activate on macOS/Linux:
source venv/bin/activate
```

Install the required dependencies:

```bash
pip install fastapi uvicorn python-dotenv sqlalchemy psycopg2-binary openai pydantic python-multipart
```

## 4. Configuration

Create a `.env` file in the `backend/` directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
USE_MOCK=False
LOG_LEVEL=INFO
DATABASE_URL=postgresql://vinuni_user2:13082001@localhost:5432/vinuni_db
```

Replace `username` and `password` with your PostgreSQL credentials. For local development, username is usually `postgres`.

### Key Setting: `USE_MOCK`
- **`USE_MOCK=True` (Default for Dev)**: No API keys required. Uses local keyword search and deterministic responses. Ideal for frontend development and testing logic.
- **`USE_MOCK=False`**: Connects to OpenAI API and PostgreSQL. Requires valid `OPENAI_API_KEY` and database setup.

## 5. Database Setup

Create the database and tables:

```bash
python create_db.py
```

This will create all necessary tables and insert sample admissions data.

## 6. Running the Server

Start the FastAPI server using Uvicorn:

```bash
uvicorn main:app --reload
```

The backend will be available at `http://localhost:8000`.

## 7. Verification
- **Health Check**: Visit `http://localhost:8000/health` to confirm the service is live.
- **API Docs**: Explore the interactive Swagger UI at `http://localhost:8000/docs`.
- **Test Chat**: Try a POST request to `/api/chat` with `{"user_id": "test", "message": "Chào bạn"}` to see the response with conversation context from database.