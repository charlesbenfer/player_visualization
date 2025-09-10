#!/usr/bin/env python3
"""
Regenerate database with fresh 45-day data
"""

from database_manager import MLBDatabaseManager
from datetime import datetime, timedelta

def main():
    print("MLB Database Regeneration")
    print("=" * 40)
    print("This will clear all data and fetch fresh 45-day data")
    
    # Calculate date range
    end_date = datetime.now() - timedelta(days=1)  # Yesterday
    start_date = end_date - timedelta(days=44)  # 45 days total
    
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    db = MLBDatabaseManager()
    
    try:
        # Clear existing data
        print("\n1. Clearing existing data...")
        cursor = db.conn.cursor()
        cursor.execute("DELETE FROM statcast_data")
        cursor.execute("DELETE FROM daily_hitting") 
        cursor.execute("DELETE FROM daily_pitching")
        cursor.execute("DELETE FROM data_updates")
        db.conn.commit()
        print("✓ Database cleared")
        
        # Fetch fresh data
        print(f"\n2. Fetching 45 days of fresh data...")
        db.fetch_and_store_date_range(start_date, end_date)
        
        # Verify results
        print("\n3. Verifying database...")
        cursor.execute('''
            SELECT 
                MIN(date) as oldest_date,
                MAX(date) as newest_date,
                COUNT(DISTINCT date) as days_count,
                COUNT(*) as total_records
            FROM statcast_data
        ''')
        
        result = cursor.fetchone()
        print(f"✓ Database regenerated successfully!")
        print(f"  - Date range: {result[0]} to {result[1]}")
        print(f"  - Days covered: {result[2]}")
        print(f"  - Total records: {result[3]:,}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()