"""
Automatic Database Backup Utility
Creates timestamped backups before schema changes or on schedule
"""
import os
import shutil
from datetime import datetime, date
from pathlib import Path
import re
import glob


class DatabaseBackup:
    """Handles automatic database backups"""
    
    def __init__(self, db_path='backend/instance/investment_manager.db', backup_dir='backend/backups'):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.max_backups = 5  # Keep last 5 backups (as requested)
    
    def create_backup(self, backup_type='manual'):
        """
        Create a timestamped backup of the database
        
        Args:
            backup_type: 'manual', 'auto', 'pre_migration', 'daily'
        
        Returns:
            str: Path to backup file or None if failed
        """
        if not os.path.exists(self.db_path):
            print(f"[WARN] Database not found at {self.db_path}")
            return None
        
        # Create backup directory
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"investment_manager_backup_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            # Copy database file
            shutil.copy2(self.db_path, backup_path)
            
            # Get file size
            size_kb = os.path.getsize(backup_path) / 1024
            
            print(f"[BACKUP] ✓ Created: {backup_name} ({size_kb:.1f} KB)")
            
            # Clean old backups
            self._cleanup_old_backups()
            
            return backup_path
        
        except Exception as e:
            print(f"[BACKUP] ✗ Failed: {str(e)}")
            return None
    
    def _get_backup_date(self, filename):
        """Extract date from backup filename"""
        try:
            # Extract date from filename: investment_manager_backup_20251129_162819.db
            match = re.search(r'_backup_(\d{8})_\d{6}\.db', filename)
            if match:
                date_str = match.group(1)
                return datetime.strptime(date_str, '%Y%m%d').date()
        except:
            pass
        return None
    
    def _cleanup_old_backups(self):
        """Remove backups exceeding max_backups limit, keeping only the most recent"""
        if not os.path.exists(self.backup_dir):
            return
        
        # Get all backup files with their dates
        backups = []
        for file in os.listdir(self.backup_dir):
            if file.startswith('investment_manager_backup_') and file.endswith('.db'):
                file_path = os.path.join(self.backup_dir, file)
                backup_date = self._get_backup_date(file)
                if backup_date:
                    backups.append((file_path, backup_date, os.path.getmtime(file_path)))
        
        # Sort by date (newest first), then by time if same date
        backups.sort(key=lambda x: (x[1], x[2]), reverse=True)
        
        # Remove old backups if exceeding limit
        if len(backups) > self.max_backups:
            backups_to_remove = backups[self.max_backups:]
            for old_backup, backup_date, _ in backups_to_remove:
                try:
                    os.remove(old_backup)
                    print(f"[BACKUP] ✓ Deleted old backup: {os.path.basename(old_backup)} (from {backup_date})")
                except Exception as e:
                    print(f"[BACKUP] ✗ Could not delete: {str(e)}")
    
    def list_backups(self):
        """List all available backups with details"""
        if not os.path.exists(self.backup_dir):
            return []
        
        backups = []
        for file in os.listdir(self.backup_dir):
            if file.startswith('investment_manager_backup_') and file.endswith('.db'):
                file_path = os.path.join(self.backup_dir, file)
                size_kb = os.path.getsize(file_path) / 1024
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                backups.append({
                    'filename': file,
                    'path': file_path,
                    'size_kb': round(size_kb, 1),
                    'created': mtime.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x['created'], reverse=True)
        return backups
    
    def restore_backup(self, backup_filename):
        """
        Restore database from a backup
        
        Args:
            backup_filename: Name of backup file to restore
        
        Returns:
            bool: True if successful, False otherwise
        """
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        if not os.path.exists(backup_path):
            print(f"[ERROR] Backup not found: {backup_filename}")
            return False
        
        try:
            # Create safety backup of current database
            if os.path.exists(self.db_path):
                safety_backup = f"{self.db_path}.before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(self.db_path, safety_backup)
                print(f"[INFO] Current database backed up to: {os.path.basename(safety_backup)}")
            
            # Restore from backup
            shutil.copy2(backup_path, self.db_path)
            print(f"[OK] Database restored from: {backup_filename}")
            return True
        
        except Exception as e:
            print(f"[ERROR] Restore failed: {str(e)}")
            return False


def auto_backup_on_startup(db_path=None, backup_dir=None, keep_count=5):
    """
    Auto backup on server startup (daily basis)
    
    Creates backup if:
    - No backups exist, OR
    - Last backup date < current date
    
    Args:
        db_path: Path to database (uses default if None)
        backup_dir: Backup directory (uses default if None)
        keep_count: Number of backups to keep
    
    Returns:
        dict with backup status
    """
    try:
        print("\n[AUTO-BACKUP] Checking backup status...")
        
        # Initialize backup system
        if db_path and backup_dir:
            backup_system = DatabaseBackup(db_path, backup_dir)
        else:
            backup_system = DatabaseBackup()
        
        backup_system.max_backups = keep_count
        
        # Check if database exists
        if not os.path.exists(backup_system.db_path):
            print(f"[AUTO-BACKUP] Database not found: {backup_system.db_path}")
            return {'status': 'skipped', 'reason': 'database_not_found'}
        
        # Get existing backups
        backups = backup_system.list_backups()
        today = date.today()
        should_backup = False
        
        if not backups:
            print("[AUTO-BACKUP] No existing backups found")
            should_backup = True
        else:
            # Get date of most recent backup
            last_backup_filename = backups[0]['filename']
            last_backup_date = backup_system._get_backup_date(last_backup_filename)
            
            if last_backup_date:
                print(f"[AUTO-BACKUP] Last backup: {last_backup_filename} (from {last_backup_date})")
                
                if last_backup_date < today:
                    print(f"[AUTO-BACKUP] Last backup is old (today: {today})")
                    should_backup = True
                else:
                    print(f"[AUTO-BACKUP] ✓ Backup already exists for today")
            else:
                # Couldn't parse date, create backup to be safe
                should_backup = True
        
        result = {
            'status': 'skipped',
            'existing_backups': len(backups),
            'backup_created': False,
            'backups_deleted': 0
        }
        
        if should_backup:
            print("[AUTO-BACKUP] Creating new backup...")
            
            initial_count = len(backups)
            backup_path = backup_system.create_backup('auto')
            
            if backup_path:
                # Get updated backup list
                updated_backups = backup_system.list_backups()
                deleted_count = max(0, initial_count - len(updated_backups) + 1)
                
                result['status'] = 'success'
                result['backup_created'] = True
                result['backup_path'] = backup_path
                result['backups_deleted'] = deleted_count
                result['total_backups'] = len(updated_backups)
                
                print(f"[AUTO-BACKUP] ✓ Complete! Total backups: {len(updated_backups)}")
            else:
                result['status'] = 'failed'
                result['reason'] = 'backup_creation_failed'
        else:
            result['reason'] = 'backup_already_exists_for_today'
            result['total_backups'] = len(backups)
        
        return result
        
    except Exception as e:
        print(f"[AUTO-BACKUP] ✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'error': str(e)}


def create_pre_migration_backup():
    """Create backup before database migrations"""
    backup = DatabaseBackup()
    return backup.create_backup('pre_migration')


if __name__ == '__main__':
    # Test backup system
    backup = DatabaseBackup()
    
    print("\n" + "=" * 60)
    print("DATABASE BACKUP UTILITY")
    print("=" * 60)
    
    # Create test backup
    backup.create_backup('test')
    
    # List backups
    print("\nAvailable Backups:")
    print("-" * 60)
    backups = backup.list_backups()
    if backups:
        for b in backups:
            print(f"{b['filename']}")
            print(f"  Created: {b['created']}")
            print(f"  Size: {b['size_kb']} KB")
            print()
    else:
        print("No backups found")
    
    print("=" * 60)

