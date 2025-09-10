#!/usr/bin/env python3
"""
Daily update script to maintain 45-day rolling window of MLB data
Designed to run via GitHub Actions
"""

import sys
from datetime import datetime, timedelta
from database_manager import MLBDatabaseManager
import os

def daily_update():
    """Run daily update to maintain 45-day window"""
    print(f"Starting daily update at {datetime.now()}")
    print("="*60)
    
    try:
        db = MLBDatabaseManager()
        
        yesterday = datetime.now() - timedelta(days=1)
        print(f"\n1. Fetching yesterday's data ({yesterday.strftime('%Y-%m-%d')})...")
        db.fetch_and_store_single_day(yesterday)
        
        print("\n2. Removing data older than 45 days...")
        db.remove_old_data(days_to_keep=45)
        
        print("\n3. Verifying database integrity...")
        cursor = db.conn.cursor()
        cursor.execute('''
            SELECT 
                MIN(date) as oldest_date,
                MAX(date) as newest_date,
                COUNT(DISTINCT date) as days_count,
                COUNT(*) as total_records
            FROM statcast_data
        ''')
        
        result = cursor.fetchone()
        print(f"  Database contains:")
        print(f"  - Date range: {result[0]} to {result[1]}")
        print(f"  - Days covered: {result[2]}")
        print(f"  - Total records: {result[3]:,}")
        
        db.close()
        
        print("\n✓ Daily update completed successfully!")
        return 0
        
    except Exception as e:
        print(f"\n✗ Error during daily update: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(daily_update())