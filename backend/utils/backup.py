"""
Automatic Database Backup Utility
Creates timestamped backups before schema changes or on schedule
"""
import os
import shutil
from datetime import datetime
from pathlib import Path


class DatabaseBackup:
    """Handles automatic database backups"""
    
    def __init__(self, db_path='backend/instance/investment_manager.db', backup_dir='backend/backups'):
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.max_backups = 30  # Keep last 30 backups
    
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
        backup_name = f"investment_manager_backup_{backup_type}_{timestamp}.db"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        try:
            # Copy database file
            shutil.copy2(self.db_path, backup_path)
            
            # Get file size
            size_kb = os.path.getsize(backup_path) / 1024
            
            print(f"[OK] Backup created: {backup_name} ({size_kb:.1f} KB)")
            
            # Clean old backups
            self._cleanup_old_backups()
            
            return backup_path
        
        except Exception as e:
            print(f"[ERROR] Backup failed: {str(e)}")
            return None
    
    def _cleanup_old_backups(self):
        """Remove backups exceeding max_backups limit"""
        if not os.path.exists(self.backup_dir):
            return
        
        # Get all backup files
        backups = []
        for file in os.listdir(self.backup_dir):
            if file.startswith('investment_manager_backup_') and file.endswith('.db'):
                file_path = os.path.join(self.backup_dir, file)
                backups.append((file_path, os.path.getmtime(file_path)))
        
        # Sort by modification time (oldest first)
        backups.sort(key=lambda x: x[1])
        
        # Remove old backups if exceeding limit
        while len(backups) > self.max_backups:
            old_backup = backups.pop(0)[0]
            try:
                os.remove(old_backup)
                print(f"[INFO] Removed old backup: {os.path.basename(old_backup)}")
            except Exception as e:
                print(f"[WARN] Could not remove old backup: {str(e)}")
    
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


def create_startup_backup():
    """Create backup on server startup"""
    backup = DatabaseBackup()
    backup.create_backup('startup')


def create_daily_backup():
    """Create daily scheduled backup"""
    backup = DatabaseBackup()
    backup.create_backup('daily')


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

