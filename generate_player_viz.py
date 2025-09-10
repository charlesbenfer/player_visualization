#!/usr/bin/env python3
"""
Simple interface to generate player visualizations
"""

import sys
from database_manager import MLBDatabaseManager
from player_visualizer import PlayerVisualizer

def main():
    print("\n" + "="*60)
    print("MLB PLAYER VISUALIZATION GENERATOR")
    print("="*60)
    
    if len(sys.argv) > 1:
        player_name = ' '.join(sys.argv[1:])
        print(f"\nGenerating visualization for: {player_name}")
    else:
        print("\nPopular players to try:")
        print("  - Shohei Ohtani")
        print("  - Aaron Judge") 
        print("  - Mookie Betts")
        print("  - Ronald Acuna Jr.")
        print("  - Freddie Freeman")
        print("  - Mike Trout")
        print("  - Gerrit Cole")
        print("  - Spencer Strider")
        print("  - Jacob deGrom")
        
        player_name = input("\nEnter player name: ").strip()
    
    print("\nConnecting to database...")
    db = MLBDatabaseManager()
    
    print("Creating visualization...")
    visualizer = PlayerVisualizer(db)
    
    fig = visualizer.create_player_dashboard(player_name, save_html=True)
    
    if fig:
        filename = f"{player_name.replace(' ', '_')}_dashboard.html"
        print(f"\n✓ SUCCESS!")
        print(f"  Dashboard saved as: {filename}")
        print(f"  Open this file in your browser to view the interactive visualization")
    else:
        print(f"\n✗ No data found for {player_name}")
        print("  Make sure you spelled the name correctly")
        print("  Note: Database only contains last 45 days of data")
    
    db.close()

if __name__ == "__main__":
    main()