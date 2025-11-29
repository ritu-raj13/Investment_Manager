# Database Migrations

This folder contains the generic database migration utility for SQLite.

## Files

- `db_migrator.py` - Generic SQLite migration script with migration functions
- `__init__.py` - Python package initializer

## Usage

### Running Migrations

```bash
# From backend directory
cd backend
python migrations/db_migrator.py [path_to_db]

# If no path provided, uses default: instance/investment_manager.db
python migrations/db_migrator.py
```

### Adding New Migrations

1. Open `db_migrator.py`
2. Add a new migration function following the pattern:
   ```python
   def migrate_your_feature():
       """Description of what this migration does"""
       # Your migration logic here
       pass
   ```
3. Add your migration to the `main()` function's migration list
4. Run the migrator

### Backup Policy

- Automatic backups are created before each migration run
- Backups are stored in `backend/backups/` with timestamp
- Keep recent backups, delete old ones manually as needed

## Notes

- All migrations are SQLite-specific
- Supports both CREATE-RECREATE and ALTER TABLE approaches
- Always test migrations on a backup first

