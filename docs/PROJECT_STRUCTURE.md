# Project Structure

## Overview

This document describes the organized file structure of the Investment Manager application, separating development and production concerns.

## Directory Structure

```
Investment_Manager/
├── backend/                      # Backend Python application
│   ├── app.py                   # Main Flask application
│   ├── config/                  # Environment-specific configurations
│   │   ├── __init__.py
│   │   ├── base.py             # Base configuration (shared)
│   │   ├── development.py      # Development settings (SQLite)
│   │   └── production.py       # Production settings (PostgreSQL)
│   ├── utils/                   # Utility functions (organized)
│   │   ├── __init__.py
│   │   ├── auth.py             # Authentication (Flask-Login)
│   │   ├── validation.py       # Data validation
│   │   ├── zones.py            # Zone calculations
│   │   ├── holdings.py         # Holdings calculations
│   │   └── helpers.py          # General helpers
│   ├── services/                # External services
│   │   ├── __init__.py
│   │   ├── price_scraper.py    # Web scraping service
│   │   └── nse_api.py          # NSE API integration
│   ├── migrations/              # Database migrations
│   │   ├── db_migrator.py      # SQLite schema migrations
│   │   └── migrate_to_postgres.py  # SQLite to PostgreSQL migration
│   ├── instance/                # SQLite database (gitignored)
│   ├── requirements.txt         # Python dependencies
│   ├── .env.example            # Development environment template
│   └── venv/                    # Virtual environment (gitignored)
│
├── frontend/                     # React frontend application
│   ├── src/
│   │   ├── App.js              # Main React component
│   │   ├── components/         # React components
│   │   │   ├── Login.js
│   │   │   ├── Portfolio.js
│   │   │   ├── StockTracking.js
│   │   │   ├── Analytics.js
│   │   │   └── Settings.js
│   │   └── services/
│   │       └── api.js          # Axios API client
│   ├── public/
│   ├── package.json            # Node dependencies
│   └── node_modules/           # Node packages (gitignored)
│
├── docs/                         # Documentation
│   ├── API_REFERENCE.md        # API documentation
│   ├── ARCHITECTURE.md         # System architecture
│   ├── DEPLOYMENT_QUICKSTART.md # Deployment guide
│   ├── SETUP_INSTRUCTIONS.md   # Development setup
│   ├── WINDOWS_SETUP_NOTE.md   # Windows-specific notes
│   ├── FUTURE_FEATURES.md      # Roadmap
│   ├── ENV_TEMPLATE.txt        # Environment variables reference
│   └── PROJECT_STRUCTURE.md    # This file
│
├── scripts/                      # Helper scripts
│   ├── dev/                    # Development scripts (future)
│   └── prod/                   # Production test scripts
│       ├── test_production_locally.bat  # Windows test script
│       └── test_production_locally.sh   # Unix test script
│
├── .env.production.example       # Production environment template
├── .gitignore                    # Git ignore rules
├── LICENSE                       # MIT License
├── Procfile                      # Heroku/Railway deployment
├── railway.json                  # Railway configuration
├── render.yaml                   # Render configuration
├── README.md                     # Main readme
└── START_HERE.md                 # Quick start guide
```

## Key Principles

### 1. **Separation of Concerns**
- **Backend code** organized by function (config, utils, services, migrations)
- **Frontend code** organized by feature (components, services)
- **Documentation** centralized in `docs/`
- **Scripts** organized by environment (dev/prod)

### 2. **Dev vs Prod Separation**
- **Development**: 
  - Uses `backend/config/development.py`
  - SQLite database (`backend/instance/investment_manager.db`)
  - Environment file: `backend/.env.example` → `backend/.env`
  - CORS allows `localhost:3000`
  
- **Production**:
  - Uses `backend/config/production.py`
  - PostgreSQL database (cloud-hosted)
  - Environment variables set in deployment platform
  - CORS configured for production domain
  - Test locally with `scripts/prod/test_production_locally.*`

### 3. **Import Structure**
```python
# In backend/app.py
from config import get_config           # Auto-detects environment
from utils import (                     # All utilities
    init_auth, validate_transaction_data, ...
)
from services import (                  # External services
    get_scraped_price, get_stock_details, ...
)
```

### 4. **Configuration Management**
- **Base config** (`backend/config/base.py`): Shared settings
- **Development config** (`backend/config/development.py`): Local overrides
- **Production config** (`backend/config/production.py`): Cloud overrides
- Automatic selection via `FLASK_ENV` environment variable

### 5. **Clean Workspace**
All working files (databases, node_modules, venv, __pycache__) are gitignored to keep the repository clean.

## Development Workflow

1. **Setup**: Follow `docs/SETUP_INSTRUCTIONS.md`
2. **Run locally**: Use `backend/.env` for configuration
3. **Test production**: Use `scripts/prod/test_production_locally.*`
4. **Deploy**: Follow `docs/DEPLOYMENT_QUICKSTART.md`

## Adding New Code

- **Utility function**: Add to appropriate `backend/utils/*.py` module
- **External service**: Add to `backend/services/`
- **Configuration**: Modify `backend/config/base.py` or env-specific files
- **Migration**: Add script to `backend/migrations/`
- **Frontend component**: Add to `frontend/src/components/`
- **Documentation**: Add to `docs/`

## Benefits

✅ **Easy to navigate**: Clear separation by concern  
✅ **Scalable**: Easy to add new modules  
✅ **Maintainable**: No duplicate code, organized imports  
✅ **Dev/Prod clarity**: Clear distinction between environments  
✅ **Clean repository**: Generated files excluded via .gitignore  

---

**Need help?** See [docs/SETUP_INSTRUCTIONS.md](SETUP_INSTRUCTIONS.md) or [START_HERE.md](../START_HERE.md)

