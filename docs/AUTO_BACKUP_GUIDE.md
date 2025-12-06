# Automatic Database Backup System

**Feature Added:** December 6, 2025  
**Status:** ✅ Production Ready

## Overview

Automatic daily backup system that protects your investment data with zero configuration required.

## How It Works

### Automatic Execution
- Runs on every server startup
- Checks if backup needed (compares last backup date vs current date)
- Creates backup only if current date > last backup date
- Maintains only the last 5 backups (auto-deletes older ones)

### Backup Logic

```
Server Start → Check Last Backup Date
                    ↓
              Today's Date?
                    ↓
         Yes ← Already backed up today
         No  ← Create new backup
                    ↓
              Save to backups/
                    ↓
         Count backups > 5?
                    ↓
         Yes → Delete oldest backup
         No  → Keep all
```

## Startup Logs

**When backup is created:**
```
[AUTO-BACKUP] Checking backup status...
[AUTO-BACKUP] Last backup: investment_manager_backup_20251129_162819.db (from 2025-11-29)
[AUTO-BACKUP] Last backup is old (today: 2025-12-06)
[AUTO-BACKUP] Creating new backup...
[BACKUP] ✓ Created: investment_manager_backup_20251206_212516.db (152.0 KB)
[AUTO-BACKUP] ✓ Complete! Total backups: 2
[STARTUP] ✓ Backup created! Total: 2
```

**When backup already exists for today:**
```
[AUTO-BACKUP] Checking backup status...
[AUTO-BACKUP] Last backup: investment_manager_backup_20251206_212516.db (from 2025-12-06)
[AUTO-BACKUP] ✓ Backup already exists for today
[STARTUP] ✓ Backup up-to-date (Total: 2 backups)
```

## File Naming Convention

Format: `investment_manager_backup_YYYYMMDD_HHMMSS.db`

Examples:
- `investment_manager_backup_20251206_212516.db` (Dec 6, 2025 at 9:25:16 PM)
- `investment_manager_backup_20251205_083042.db` (Dec 5, 2025 at 8:30:42 AM)

## Storage Location

**Path:** `backend/backups/`

**Retention:** Last 5 backups only

**Example:**
```
backend/backups/
├── investment_manager_backup_20251206_212516.db  ← Latest
├── investment_manager_backup_20251205_163248.db
├── investment_manager_backup_20251204_091532.db
├── investment_manager_backup_20251203_141829.db
└── investment_manager_backup_20251202_084517.db  ← Oldest (5th)
```

When 6th backup is created, oldest (Dec 2) is automatically deleted.

## Manual Restore

If you need to restore from a backup:

### Method 1: Windows Command Line
```powershell
cd backend
copy backups\investment_manager_backup_YYYYMMDD_HHMMSS.db instance\investment_manager.db
```

### Method 2: Python Script
```python
from utils.backup import DatabaseBackup

backup = DatabaseBackup()
backup.restore_backup('investment_manager_backup_20251206_212516.db')
```

## Configuration

### Change Retention Count

Edit `backend/app.py`:

```python
# Keep last 10 backups instead of 5
backup_result = auto_backup_on_startup(db_path, backup_dir, keep_count=10)
```

### Disable Auto-Backup

Comment out the auto-backup section in `backend/app.py`:

```python
# Auto-backup on startup (daily basis, keeps last 5 backups)
# try:
#     from utils.backup import auto_backup_on_startup
#     ...
# except Exception as e:
#     ...
```

## Benefits

✅ **No data loss** - Daily automatic protection  
✅ **Zero configuration** - Works out of the box  
✅ **Space efficient** - Only keeps recent backups  
✅ **Transparent** - See status in startup logs  
✅ **Disaster recovery** - Easy restore process

## Technical Details

### Implementation Files
- `backend/utils/backup.py` - Backup logic
- `backend/app.py` - Auto-backup on startup hook
- `backend/utils/__init__.py` - Export auto_backup_on_startup

### Key Functions

**`auto_backup_on_startup(db_path, backup_dir, keep_count=5)`**
- Main entry point called on server startup
- Returns dict with backup status

**`_get_backup_date(filename)`**
- Extracts date from backup filename
- Returns datetime.date object

**`_cleanup_old_backups()`**
- Removes backups exceeding keep_count
- Keeps most recent based on date

### Date Comparison Logic

```python
today = date.today()
last_backup_date = extract_from_filename()

if last_backup_date < today:
    create_new_backup()
else:
    skip_backup()
```

## Limitations

- **SQLite only** - Auto-backup only works with SQLite databases
- **Startup only** - Backups created on server start, not scheduled hourly
- **No cloud sync** - Backups stored locally only

## Future Enhancements

Potential improvements (not yet implemented):

- [ ] Cloud backup sync (AWS S3, Google Drive)
- [ ] Scheduled backups (hourly, weekly)
- [ ] Backup compression (gzip)
- [ ] Backup verification (checksum)
- [ ] Point-in-time restore UI
- [ ] Backup comparison tool

## Troubleshooting

### Backup not created

**Check:**
1. Database exists at `backend/instance/investment_manager.db`
2. Backup directory writable: `backend/backups/`
3. Check startup logs for error messages

### Old backups not deleted

**Possible causes:**
- File permissions (Windows file locks)
- Files in use by another process

**Solution:**
- Close all database connections
- Restart server

### Restore failed

**Check:**
1. Backup file exists and is not corrupted
2. No active database connections
3. Sufficient disk space

## Related Documentation

- [Features Guide](FEATURES.md) - All application features
- [Deployment Guide](DEPLOYMENT_QUICKSTART.md) - Production setup

---

**Last Updated:** December 6, 2025

