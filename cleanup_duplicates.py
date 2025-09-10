#!/usr/bin/env python3
"""
Clean up duplicate records from the database
"""

from database_manager import MLBDatabaseManager

def main():
    print("MLB Database Duplicate Cleanup")
    print("=" * 40)
    
    db = MLBDatabaseManager()
    
    try:
        # Remove duplicates
        removed_count = db.remove_duplicate_data()
        
        if removed_count > 0:
            print(f"\n✅ Cleanup complete! Removed {removed_count} duplicate records")
        else:
            print(f"\n✅ Database is clean - no duplicates found")
            
    except Exception as e:
        print(f"\n❌ Error during cleanup: {e}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()