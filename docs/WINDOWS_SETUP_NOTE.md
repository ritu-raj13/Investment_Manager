# Windows Setup Note - psycopg2-binary

## Issue
On Windows, `psycopg2-binary` may fail to install during local development.

## Why This is OK
- **Local development uses SQLite** - No PostgreSQL needed locally
- **Production deployment** (Railway/Heroku/Render) handles PostgreSQL automatically
- psycopg2-binary only needed in production environments

## Solution for Local Development

### Option 1: Skip psycopg2-binary (Recommended)
Just comment it out in `requirements.txt` for local development:

```txt
# Database
SQLAlchemy==2.0.23
# psycopg2-binary==2.9.9  # Only needed for production PostgreSQL
```

### Option 2: Install Other Dependencies Only
```bash
# Install everything except psycopg2
pip install Flask==3.0.0 Flask-CORS==4.0.0 Flask-SQLAlchemy==3.1.1 Flask-Login==0.6.3 Werkzeug==3.0.3 Flask-Limiter==3.5.0 gunicorn==21.2.0 SQLAlchemy==2.0.23 pandas==2.1.3 yfinance==0.2.32 requests==2.31.0 beautifulsoup4==4.12.2 lxml==5.1.0 python-dotenv==1.0.0
```

### Option 3: Use Pre-built Wheel (Advanced)
Download pre-built wheel from: https://www.lfd.uci.edu/~gohlke/pythonlibs/#psycopg

## For Production Deployment
**No action needed!** Railway/Heroku/Render will:
- Automatically install psycopg2-binary
- Provide PostgreSQL database
- Handle all dependencies

## Testing Production Features Locally
You can test the production-ready app (with authentication) using SQLite:

```bash
# Windows
test_production_locally.bat

# This uses SQLite locally (no PostgreSQL needed)
```

## Summary
✅ **Local development:** SQLite (works without psycopg2)  
✅ **Production deployment:** PostgreSQL (auto-installed by platform)  
✅ **Authentication:** Works perfectly with SQLite locally  

No need to fix psycopg2-binary for local development! 🎉

