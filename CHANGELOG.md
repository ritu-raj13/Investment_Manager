# Changelog

All notable changes to the Personal Finance Manager project.

## [Unreleased]

### Added (December 6, 2025)
- **Automatic Daily Backup System**
  - Auto-backup on server startup (daily basis)
  - Smart date detection (only backs up if current date > last backup date)
  - Auto-cleanup (keeps only last 5 backups)
  - Transparent startup logging
  - See [docs/AUTO_BACKUP_GUIDE.md](docs/AUTO_BACKUP_GUIDE.md)

- **RAG Knowledge Base Feature** (Experimental)
  - PDF upload (single & batch) with progress tracking
  - Text & image extraction from scanned PDFs
  - ChromaDB vector storage for semantic search
  - Local Ollama LLM integration (gpt-oss:20b, nomic-embed-text)
  - RAG chatbot for Q&A from uploaded notes
  - Book organization with chapters and sections
  - Markdown editor for content editing
  - Export to HTML/PDF
  - Auto-approve organization proposals
  - See [KNOWLEDGE_BASE_README.md](KNOWLEDGE_BASE_README.md)

### Updated
- `.gitignore` - Added knowledge base data exclusions
  - `backend/uploads/` (PDFs and extracted images)
  - `backend/chroma_db/` (vector database)
  - `backend/chroma_db_backup*/` (vector DB backups)
  - `backend/backups/*.db` (database backups)

- Documentation updates
  - `README.md` - Added RAG feature link, updated project status
  - `docs/FEATURES.md` - Added auto-backup section, December 2025 updates
  - `KNOWLEDGE_BASE_README.md` - Clarified RAG as separate feature

### Fixed
- Database backup imports and initialization
- ChromaDB collection conflicts on reindex
- PDF batch upload processing (sequential with per-file error handling)
- Multi-file upload UI cursor bug (switched to uncontrolled input)

---

## [Phase 3] - November 29, 2025

### Added - Swing Trading Enhancements
- **Projected Portfolio Planning**
  - Projected Portfolio Amount with target date
  - Rebalancing calculations based on projected vs current amount
  
- **Multi-Step Buy/Sell Strategy**
  - Track up to 3 buy steps per stock
  - Track up to 2 sell steps per stock
  - Automatic average price calculation per step
  
- **Parent Sector Grouping**
  - Group child sectors under parent sectors
  - Enforce stock count limits per parent sector (default: 2)
  - Parent sector management UI in Analytics tab
  
- **Three-Tier Market Cap Limits**
  - Per-stock % limits (Large: 5%, Mid: 3%, Small: 2.5%, Micro: 2%)
  - Stock count limits (Large: 15, Mid: 8, Small: 7, Micro: 3)
  - Portfolio % limits (Large: 50%, Mid: 30%, Small: 25%, Micro: 10%)
  - Max total stocks setting (default: 30)
  
- **Enhanced Recommendations Page**
  - Attention-sorted rebalancing (red → yellow → green)
  - Market cap violation tracking across all three tiers
  - Sector rebalancing with parent sector awareness

### Updated
- `docs/FEATURES.md` - Comprehensive swing trading feature documentation
- Settings page - Added all swing trading configuration options

---

## [Phase 3] - November 2025

### Added - Financial Health & Multi-Asset Portfolio
- **Financial Health Dashboard**
  - Overall financial health score (0-100)
  - Debt-to-income ratio tracking
  - Emergency fund status (months of expenses)
  - Savings rate calculation
  
- **Unified Portfolio XIRR**
  - Cross-asset XIRR calculation (stocks, MF, FD, EPF, NPS, etc.)
  - Breakdown by asset type
  - Visual charts showing contribution
  
- **Global Settings & Allocation Targets**
  - Asset allocation targets (equity/debt/cash %)
  - Budget & emergency fund settings
  - Currency & display preferences
  
- **Multi-Asset Net Worth Tracking**
  - Total net worth across all asset categories
  - Breakdown by asset class with pie chart
  - Trend analysis over time
  
- **Cash Flow Analysis**
  - Monthly income vs expenses visualization
  - Expense categorization
  - Surplus/deficit calculation
  - Trend analysis (3, 6, 12 months)
  
- **Budget Tracking & Alerts**
  - Category-level budgets
  - Real-time spend tracking with progress bars
  - Alerts when approaching/exceeding limits

### Updated
- `docs/FEATURES.md` - Phase 3 feature documentation
- Database schema - Added models for all asset types

---

## [Phase 2] - October 2025

### Added - Core Investment Features
- **FIFO-Based Holding Period Tracking**
  - Automatic lot tracking with FIFO method
  - Weighted average for multiple lots
  - Sortable holding period column
  
- **XIRR Calculation**
  - Annualized portfolio returns
  - Newton-Raphson method for accuracy
  - Comparable to FDs, mutual funds benchmarks
  
- **Portfolio Allocation Color Coding**
  - Market cap-based thresholds
  - Visual indicators (red/green/orange/blue)
  - +0.5% green buffer for breathing room
  
- **Portfolio Health Dashboard**
  - Overall health score (0-100)
  - Concentration risk analysis
  - Diversification metrics (Herfindahl Index)
  
- **Recommendations Engine**
  - Price zone alerts (buy/sell/average)
  - Rebalancing suggestions (stocks to add/reduce)
  - Sector and market cap insights
  
- **User-Configurable Settings**
  - Portfolio allocation thresholds
  - Market cap limits per stock
  - Sector allocation maximums

---

## [Phase 1] - September 2025

### Initial Release
- **Stock Tracking** - Add, edit, delete stocks with buy/sell/average zones
- **Portfolio Management** - Transaction tracking, P/L calculation
- **Analytics Dashboard** - Performance charts, top gainers/losers
- **Authentication** - Login/logout, session management
- **Database** - SQLite (dev), PostgreSQL (prod) support
- **Deployment** - Railway/Heroku/Render ready

---

## Format

This changelog follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

### Categories
- **Added** - New features
- **Changed** - Changes to existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Security improvements

---

**Last Updated:** December 6, 2025

