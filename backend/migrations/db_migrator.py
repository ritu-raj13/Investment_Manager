"""
Universal Database Migrator for Investment Manager
Handles all schema updates and migrations
Run this script whenever you update the codebase to ensure database schema is current
"""
import sqlite3
import os
from datetime import datetime


class DatabaseMigrator:
    """Universal database migrator with version tracking"""
    
    def __init__(self, db_path='investment_manager.db'):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Connect to the database"""
        if not os.path.exists(self.db_path):
            print(f"[INFO] No existing database found at {self.db_path}")
            print("[INFO] Database will be created automatically when app starts")
            return False
        
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        return True
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
    
    def get_table_columns(self, table_name):
        """Get list of column names for a table"""
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            return [column[1] for column in self.cursor.fetchall()]
        except sqlite3.Error:
            return []
    
    def table_exists(self, table_name):
        """Check if a table exists"""
        self.cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,)
        )
        return self.cursor.fetchone() is not None
    
    def add_column_if_missing(self, table_name, column_name, column_type, default_value=None):
        """Add a column to a table if it doesn't exist"""
        columns = self.get_table_columns(table_name)
        
        if column_name in columns:
            print(f"  [-] Column '{column_name}' already exists in '{table_name}'")
            return False
        
        try:
            sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            if default_value is not None:
                sql += f" DEFAULT {default_value}"
            
            self.cursor.execute(sql)
            print(f"  [✓] Added column '{column_name}' to '{table_name}'")
            return True
        except sqlite3.Error as e:
            print(f"  [✗] Failed to add column '{column_name}': {e}")
            return False
    
    def migrate_stocks_table(self):
        """Migrate stocks table to latest schema"""
        print("\n[STOCKS TABLE MIGRATION]")
        
        if not self.table_exists('stocks'):
            print("  [INFO] 'stocks' table doesn't exist yet - will be created on first run")
            return
        
        changes_made = False
        
        # Add sector column (if missing)
        if self.add_column_if_missing('stocks', 'sector', 'VARCHAR(100)'):
            changes_made = True
        
        # Add market_cap column (if missing)
        if self.add_column_if_missing('stocks', 'market_cap', 'VARCHAR(20)'):
            changes_made = True
        
        # Add day_change_pct column (if missing)
        if self.add_column_if_missing('stocks', 'day_change_pct', 'FLOAT'):
            changes_made = True
        
        # Check zone columns are correct type (VARCHAR to support ranges)
        columns = self.get_table_columns('stocks')
        if 'buy_zone_price' in columns:
            # Check column type
            self.cursor.execute("PRAGMA table_info(stocks)")
            col_info = {col[1]: col[2] for col in self.cursor.fetchall()}
            
            # If any zone columns are not VARCHAR/TEXT, we need to recreate table
            zone_cols = ['buy_zone_price', 'sell_zone_price', 'average_zone_price']
            needs_recreation = any(
                col in col_info and 'VARCHAR' not in col_info[col].upper() and 'TEXT' not in col_info[col].upper()
                for col in zone_cols
            )
            
            if needs_recreation:
                print("  [INFO] Zone columns need type conversion to support ranges...")
                if self.convert_zone_columns_to_varchar():
                    changes_made = True
        
        if not changes_made:
            print("  [✓] Stocks table is up to date")
    
    def convert_zone_columns_to_varchar(self):
        """Convert zone price columns from numeric to VARCHAR to support ranges"""
        try:
            # Create new table with correct schema
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS stocks_new (
                    id INTEGER PRIMARY KEY,
                    symbol VARCHAR(20) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    group_name VARCHAR(50),
                    sector VARCHAR(100),
                    market_cap VARCHAR(20),
                    buy_zone_price VARCHAR(50),
                    sell_zone_price VARCHAR(50),
                    average_zone_price VARCHAR(50),
                    status VARCHAR(20),
                    current_price FLOAT,
                    day_change_pct FLOAT,
                    last_updated DATETIME,
                    notes TEXT
                )
            ''')
            
            # Copy data, converting numeric zones to text
            self.cursor.execute('''
                INSERT INTO stocks_new 
                SELECT 
                    id, symbol, name, group_name, sector, market_cap,
                    CAST(buy_zone_price AS TEXT),
                    CAST(sell_zone_price AS TEXT),
                    CAST(average_zone_price AS TEXT),
                    status, current_price, day_change_pct, last_updated, notes
                FROM stocks
            ''')
            
            # Drop old table and rename new one
            self.cursor.execute('DROP TABLE stocks')
            self.cursor.execute('ALTER TABLE stocks_new RENAME TO stocks')
            
            print("  [✓] Zone columns converted to support ranges (e.g., '250-300')")
            return True
        
        except sqlite3.Error as e:
            print(f"  [✗] Failed to convert zone columns: {e}")
            return False
    
    def migrate_portfolio_settings_table(self):
        """Ensure portfolio_settings table exists"""
        print("\n[PORTFOLIO SETTINGS TABLE MIGRATION]")
        
        if self.table_exists('portfolio_settings'):
            print("  [✓] Portfolio settings table exists")
            return
        
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS portfolio_settings (
                    id INTEGER PRIMARY KEY,
                    total_amount FLOAT DEFAULT 0.0,
                    updated_at DATETIME
                )
            ''')
            print("  [✓] Created portfolio_settings table")
        except sqlite3.Error as e:
            print(f"  [✗] Failed to create portfolio_settings table: {e}")
    
    def migrate_all(self):
        """Run all migrations"""
        print("=" * 70)
        print("DATABASE MIGRATION - Investment Manager")
        print("=" * 70)
        
        if not self.connect():
            print("\n[INFO] No database to migrate. App will create fresh database.")
            print("=" * 70)
            return
        
        try:
            # Run all table migrations
            self.migrate_stocks_table()
            self.migrate_portfolio_settings_table()
            
            # Commit all changes
            self.conn.commit()
            
            print("\n" + "=" * 70)
            print("[SUCCESS] Database migration completed!")
            print("=" * 70)
        
        except Exception as e:
            print(f"\n[ERROR] Migration failed: {e}")
            self.conn.rollback()
        
        finally:
            self.close()
    
    def backup_database(self, backup_dir='backups'):
        """Create a backup before migration"""
        if not os.path.exists(self.db_path):
            return None
        
        os.makedirs(backup_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f'pre_migration_backup_{timestamp}.db')
        
        try:
            import shutil
            shutil.copy2(self.db_path, backup_path)
            print(f"[BACKUP] Database backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            print(f"[WARN] Could not create backup: {e}")
            return None


def main():
    """Main migration entry point"""
    print("\n⚠️  IMPORTANT: Close the Flask app before running migrations!\n")
    
    migrator = DatabaseMigrator()
    
    # Create backup before migration
    migrator.backup_database()
    
    # Run migrations
    migrator.migrate_all()
    
    print("\nYou can now restart the Flask app.")
    print("=" * 70)


if __name__ == '__main__':
    main()

