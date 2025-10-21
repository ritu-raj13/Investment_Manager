"""
Migrate data from SQLite to PostgreSQL
Preserves all stocks, transactions, and settings
"""
import json
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy.orm import sessionmaker

# Add parent directory to path to import models
sys.path.insert(0, os.path.dirname(__file__))


def export_sqlite_to_json(sqlite_db='investment_manager.db'):
    """Export all data from SQLite to JSON files"""
    print("=" * 60)
    print("EXPORTING DATA FROM SQLITE")
    print("=" * 60)
    
    if not os.path.exists(sqlite_db):
        print(f"[ERROR] SQLite database not found: {sqlite_db}")
        return False
    
    # Connect to SQLite
    engine = create_engine(f'sqlite:///{sqlite_db}')
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        metadata = MetaData()
        metadata.reflect(bind=engine)
        
        # Export each table
        export_data = {}
        
        for table_name in ['stocks', 'portfolio_transactions', 'portfolio_settings']:
            if table_name in metadata.tables:
                table = Table(table_name, metadata, autoload_with=engine)
                result = session.execute(table.select())
                rows = [dict(row._mapping) for row in result]
                
                # Convert datetime objects to strings
                for row in rows:
                    for key, value in row.items():
                        if isinstance(value, datetime):
                            row[key] = value.isoformat()
                
                export_data[table_name] = rows
                print(f"[OK] Exported {len(rows)} rows from '{table_name}'")
            else:
                print(f"[SKIP] Table '{table_name}' not found")
                export_data[table_name] = []
        
        # Save to JSON
        filename = f'data_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"\n[SUCCESS] Data exported to: {filename}")
        print("=" * 60)
        return filename
    
    except Exception as e:
        print(f"[ERROR] Export failed: {e}")
        return False
    finally:
        session.close()


def import_json_to_postgres(json_file, postgres_url):
    """Import data from JSON to PostgreSQL"""
    print("=" * 60)
    print("IMPORTING DATA TO POSTGRESQL")
    print("=" * 60)
    
    if not os.path.exists(json_file):
        print(f"[ERROR] JSON file not found: {json_file}")
        return False
    
    # Load JSON data
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    try:
        # Connect to PostgreSQL
        if postgres_url.startswith('postgres://'):
            postgres_url = postgres_url.replace('postgres://', 'postgresql://', 1)
        
        engine = create_engine(postgres_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create tables if they don't exist
        from app import db, Stock, PortfolioTransaction, PortfolioSettings
        from sqlalchemy import create_engine as ce
        
        # Create all tables
        db.metadata.create_all(engine)
        print("[OK] Tables created/verified in PostgreSQL")
        
        # Import stocks
        if data.get('stocks'):
            for row in data['stocks']:
                # Convert ISO format strings back to datetime
                if row.get('last_updated'):
                    try:
                        row['last_updated'] = datetime.fromisoformat(row['last_updated'])
                    except:
                        row['last_updated'] = None
                
                stock = Stock(**row)
                session.merge(stock)  # merge instead of add to handle duplicates
            
            session.commit()
            print(f"[OK] Imported {len(data['stocks'])} stocks")
        
        # Import transactions
        if data.get('portfolio_transactions'):
            for row in data['portfolio_transactions']:
                # Convert datetime strings
                if row.get('transaction_date'):
                    row['transaction_date'] = datetime.fromisoformat(row['transaction_date'])
                if row.get('created_at'):
                    row['created_at'] = datetime.fromisoformat(row['created_at'])
                
                transaction = PortfolioTransaction(**row)
                session.merge(transaction)
            
            session.commit()
            print(f"[OK] Imported {len(data['portfolio_transactions'])} transactions")
        
        # Import settings
        if data.get('portfolio_settings'):
            for row in data['portfolio_settings']:
                if row.get('updated_at'):
                    try:
                        row['updated_at'] = datetime.fromisoformat(row['updated_at'])
                    except:
                        row['updated_at'] = None
                
                settings = PortfolioSettings(**row)
                session.merge(settings)
            
            session.commit()
            print(f"[OK] Imported portfolio settings")
        
        print("\n[SUCCESS] All data imported to PostgreSQL!")
        print("=" * 60)
        
        # Verify import
        stock_count = session.query(Stock).count()
        txn_count = session.query(PortfolioTransaction).count()
        print(f"\nVerification:")
        print(f"  Stocks in database: {stock_count}")
        print(f"  Transactions in database: {txn_count}")
        print("=" * 60)
        
        return True
    
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        session.close()


def main():
    """Main migration workflow"""
    print("\n" + "=" * 60)
    print("SQLite to PostgreSQL Migration Tool")
    print("=" * 60 + "\n")
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Export: python migrate_to_postgres.py export")
        print("  Import: python migrate_to_postgres.py import <json_file> <postgres_url>")
        print("\nExample:")
        print("  1. Export from SQLite:")
        print("     python migrate_to_postgres.py export")
        print("\n  2. Import to PostgreSQL:")
        print("     python migrate_to_postgres.py import data_export_xxx.json postgresql://user:pass@host:5432/db")
        print("\nOr set DATABASE_URL environment variable:")
        print("  export DATABASE_URL='postgresql://...'")
        print("  python migrate_to_postgres.py import data_export_xxx.json")
        return
    
    command = sys.argv[1]
    
    if command == 'export':
        json_file = export_sqlite_to_json()
        if json_file:
            print("\n[NEXT STEP]")
            print(f"Now import to PostgreSQL:")
            print(f"  python migrate_to_postgres.py import {json_file} <POSTGRES_URL>")
    
    elif command == 'import':
        if len(sys.argv) < 3:
            print("[ERROR] Please provide JSON file")
            return
        
        json_file = sys.argv[2]
        
        # Get PostgreSQL URL from argument or environment
        postgres_url = None
        if len(sys.argv) >= 4:
            postgres_url = sys.argv[3]
        else:
            postgres_url = os.environ.get('DATABASE_URL')
        
        if not postgres_url:
            print("[ERROR] PostgreSQL URL not provided")
            print("Either pass as argument or set DATABASE_URL environment variable")
            return
        
        success = import_json_to_postgres(json_file, postgres_url)
        if success:
            print("\n[DONE] Migration completed successfully!")
            print("Your data is now in PostgreSQL and ready for production!")
    
    else:
        print(f"[ERROR] Unknown command: {command}")
        print("Use 'export' or 'import'")


if __name__ == '__main__':
    main()

