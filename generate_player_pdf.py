#!/usr/bin/env python3
"""
Generate PDF reports for MLB players
"""

import sys
import os
from database_manager import MLBDatabaseManager
from pdf_visualizer import PDFPlayerVisualizer

def main():
    print("=" * 60)
    print("MLB PLAYER PDF REPORT GENERATOR")
    print("=" * 60)
    
    # Get player name
    if len(sys.argv) > 1:
        player_name = sys.argv[1]
    else:
        player_name = input("\nEnter player name (Last, First): ")
    
    if not player_name.strip():
        print("❌ Please provide a player name")
        return
    
    print(f"\nGenerating PDF report for: {player_name}")
    
    # Connect to database
    print("\nConnecting to database...")
    try:
        db = MLBDatabaseManager()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Create PDF visualizer
    print("Creating PDF report...")
    try:
        visualizer = PDFPlayerVisualizer(db)
        pdf_path = visualizer.create_player_report(player_name)
        
        if pdf_path:
            print(f"\n✅ SUCCESS!")
            print(f"  PDF report saved as: {pdf_path}")
            print(f"  Open this file to view the professional report")
        else:
            print(f"\n❌ FAILED!")
            print(f"  No data found for {player_name}")
            print(f"  Make sure you spelled the name correctly")
            print(f"  Note: Database only contains last 45 days of data")
            print(f"  Use: python find_players.py to see available players")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()