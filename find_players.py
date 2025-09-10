#!/usr/bin/env python3
"""
Helper script to find available players in the database
"""

from database_manager import MLBDatabaseManager
import pandas as pd
import sys

def find_players(search_term=None):
    """Find players in the database"""
    db = MLBDatabaseManager()
    
    try:
        # Get all available players using Chadwick Register
        all_players = db.get_all_available_players()
        
        if search_term:
            # Filter results by search term
            filtered_players = [p for p in all_players if search_term.lower() in p['name'].lower()]
            print(f"\nPlayers matching '{search_term}':")
            players_to_show = filtered_players
        else:
            print("\nAll available players:")
            players_to_show = all_players
        
        print("=" * 70)
        print(f"{'Player Name':<30} {'Type':<12} {'ID':<10}")
        print("=" * 70)
        
        for player in players_to_show:
            print(f"{player['name']:<30} {player['type']:<12} {player['id']:<10}")
        
        print(f"\nTotal: {len(players_to_show)} players found")
        print(f"  Hitters: {len([p for p in players_to_show if p['type'] == 'hitter'])}")
        print(f"  Pitchers: {len([p for p in players_to_show if p['type'] == 'pitcher'])}")
        print(f"  Two-way: {len([p for p in players_to_show if p['type'] == 'two-way'])}")
        
        print("\nUsage: python generate_player_pdf.py \"Last name, First name\"")
        print("Example: python generate_player_pdf.py \"Judge, Aaron\"")
        
    except Exception as e:
        print(f"Error: {e}")
        print("Falling back to pitcher-only list...")
        
        # Fallback to old method
        query = '''
        SELECT DISTINCT player_name, COUNT(*) as pitch_count
        FROM statcast_data 
        WHERE player_name IS NOT NULL
        GROUP BY player_name
        ORDER BY player_name
        '''
        
        result = pd.read_sql_query(query, db.conn)
        
        if search_term:
            mask = result['player_name'].str.contains(search_term, case=False, na=False)
            result = result[mask]
            print(f"\nPitchers matching '{search_term}':")
        else:
            print("\nAvailable pitchers:")
        
        print("=" * 50)
        print(f"{'Player Name':<25} {'Pitches':<10}")
        print("=" * 50)
        
        for _, row in result.iterrows():
            print(f"{row['player_name']:<25} {row['pitch_count']:<10}")
        
        print(f"\nTotal: {len(result)} pitchers found")
        
    finally:
        db.close()

def main():
    if len(sys.argv) > 1:
        search_term = sys.argv[1]
        find_players(search_term)
    else:
        find_players()

if __name__ == "__main__":
    main()