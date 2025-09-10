import sqlite3
import pandas as pd
import pybaseball as pyb
from datetime import datetime, timedelta
import json
import os

class MLBDatabaseManager:
    def __init__(self, db_path='mlb_data.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_tables()
        
    def create_tables(self):
        """Create database tables for MLB data"""
        cursor = self.conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_hitting (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                player_id TEXT,
                player_name TEXT NOT NULL,
                team TEXT,
                games INTEGER,
                plate_appearances INTEGER,
                at_bats INTEGER,
                runs INTEGER,
                hits INTEGER,
                doubles INTEGER,
                triples INTEGER,
                home_runs INTEGER,
                rbi INTEGER,
                stolen_bases INTEGER,
                caught_stealing INTEGER,
                walks INTEGER,
                strikeouts INTEGER,
                batting_avg REAL,
                on_base_pct REAL,
                slugging_pct REAL,
                ops REAL,
                woba REAL,
                wrc_plus REAL,
                war REAL,
                UNIQUE(date, player_name)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_pitching (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                player_id TEXT,
                player_name TEXT NOT NULL,
                team TEXT,
                games INTEGER,
                games_started INTEGER,
                innings_pitched REAL,
                hits_allowed INTEGER,
                runs_allowed INTEGER,
                earned_runs INTEGER,
                home_runs_allowed INTEGER,
                walks_allowed INTEGER,
                strikeouts INTEGER,
                era REAL,
                whip REAL,
                fip REAL,
                xfip REAL,
                war REAL,
                saves INTEGER,
                holds INTEGER,
                UNIQUE(date, player_name)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS statcast_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                player_id TEXT,
                player_name TEXT,
                pitch_type TEXT,
                game_date DATE,
                release_speed REAL,
                release_pos_x REAL,
                release_pos_y REAL,
                release_pos_z REAL,
                batter TEXT,
                pitcher TEXT,
                events TEXT,
                description TEXT,
                zone INTEGER,
                stand TEXT,
                p_throws TEXT,
                home_team TEXT,
                away_team TEXT,
                type TEXT,
                hit_location INTEGER,
                bb_type TEXT,
                balls INTEGER,
                strikes INTEGER,
                pfx_x REAL,
                pfx_z REAL,
                plate_x REAL,
                plate_z REAL,
                vx0 REAL,
                vy0 REAL,
                vz0 REAL,
                ax REAL,
                ay REAL,
                az REAL,
                sz_top REAL,
                sz_bot REAL,
                hit_distance_sc REAL,
                launch_speed REAL,
                launch_angle REAL,
                effective_speed REAL,
                release_spin_rate REAL,
                release_extension REAL,
                game_pk INTEGER,
                pitcher_id INTEGER,
                batter_id INTEGER,
                hc_x REAL,
                hc_y REAL,
                barrel INTEGER,
                UNIQUE(date, game_pk, pitcher_id, batter_id, balls, strikes, pitch_type)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_updates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                update_date DATE NOT NULL,
                data_date DATE NOT NULL,
                records_added INTEGER,
                status TEXT,
                UNIQUE(data_date)
            )
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_hitting_date ON daily_hitting(date);
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_hitting_player ON daily_hitting(player_name);
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_pitching_date ON daily_pitching(date);
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_pitching_player ON daily_pitching(player_name);
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_statcast_date ON statcast_data(date);
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_statcast_player ON statcast_data(player_name);
        ''')
        
        self.conn.commit()
    
    def fetch_and_store_date_range(self, start_date, end_date):
        """Fetch and store data for a date range"""
        current_date = start_date
        
        while current_date <= end_date:
            print(f"Fetching data for {current_date.strftime('%Y-%m-%d')}...")
            self.fetch_and_store_single_day(current_date)
            current_date += timedelta(days=1)
    
    def fetch_and_store_single_day(self, date):
        """Fetch and store data for a single day"""
        date_str = date.strftime('%Y-%m-%d')
        
        try:
            statcast_data = pyb.statcast(start_dt=date_str, end_dt=date_str)
            
            if not statcast_data.empty:
                statcast_data['date'] = date_str
                
                columns_to_keep = [col for col in statcast_data.columns 
                                 if col in self.get_statcast_columns()]
                statcast_subset = statcast_data[columns_to_keep].copy()
                
                statcast_subset['barrel'] = (
                    (statcast_subset['launch_speed'] >= 98) & 
                    (statcast_subset['launch_angle'].between(26, 30))
                ).fillna(False).astype(int)
                
                statcast_subset.to_sql('statcast_data', self.conn, 
                                      if_exists='append', index=False)
                
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO data_updates (update_date, data_date, records_added, status)
                    VALUES (?, ?, ?, ?)
                ''', (datetime.now().strftime('%Y-%m-%d'), date_str, len(statcast_subset), 'success'))
                
                self.conn.commit()
                print(f"  ✓ Stored {len(statcast_subset)} statcast records for {date_str}")
            else:
                print(f"  ⚠ No data available for {date_str}")
                
        except Exception as e:
            print(f"  ✗ Error fetching data for {date_str}: {e}")
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO data_updates (update_date, data_date, records_added, status)
                VALUES (?, ?, ?, ?)
            ''', (datetime.now().strftime('%Y-%m-%d'), date_str, 0, f'error: {str(e)}'))
            self.conn.commit()
    
    def get_statcast_columns(self):
        """Get list of statcast columns to keep"""
        return ['date', 'player_name', 'pitch_type', 'game_date', 'release_speed',
                'release_pos_x', 'release_pos_y', 'release_pos_z', 'batter', 'pitcher',
                'events', 'description', 'zone', 'stand', 'p_throws', 'home_team',
                'away_team', 'type', 'hit_location', 'bb_type', 'balls', 'strikes',
                'pfx_x', 'pfx_z', 'plate_x', 'plate_z', 'vx0', 'vy0', 'vz0',
                'ax', 'ay', 'az', 'sz_top', 'sz_bot', 'hit_distance_sc',
                'launch_speed', 'launch_angle', 'effective_speed', 'release_spin_rate',
                'release_extension', 'game_pk', 'pitcher', 'batter', 'hc_x', 'hc_y']
    
    def remove_old_data(self, days_to_keep=45):
        """Remove data older than specified days"""
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')
        
        cursor = self.conn.cursor()
        
        cursor.execute('DELETE FROM daily_hitting WHERE date < ?', (cutoff_date,))
        cursor.execute('DELETE FROM daily_pitching WHERE date < ?', (cutoff_date,))
        cursor.execute('DELETE FROM statcast_data WHERE date < ?', (cutoff_date,))
        cursor.execute('DELETE FROM data_updates WHERE data_date < ?', (cutoff_date,))
        
        self.conn.commit()
        print(f"Removed data older than {cutoff_date}")
    
    def get_player_data(self, player_name, start_date=None, end_date=None):
        """Get all data for a specific player"""
        if not start_date:
            start_date = (datetime.now() - timedelta(days=45)).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        query_hitting = '''
            SELECT * FROM daily_hitting 
            WHERE player_name = ? AND date BETWEEN ? AND ?
            ORDER BY date DESC
        '''
        
        query_pitching = '''
            SELECT * FROM daily_pitching 
            WHERE player_name = ? AND date BETWEEN ? AND ?
            ORDER BY date DESC
        '''
        
        query_statcast = '''
            SELECT * FROM statcast_data 
            WHERE (player_name = ? OR batter = ? OR pitcher = ?) 
            AND date BETWEEN ? AND ?
            ORDER BY date DESC
        '''
        
        hitting_df = pd.read_sql_query(query_hitting, self.conn, 
                                      params=(player_name, start_date, end_date))
        pitching_df = pd.read_sql_query(query_pitching, self.conn,
                                       params=(player_name, start_date, end_date))
        statcast_df = pd.read_sql_query(query_statcast, self.conn,
                                       params=(player_name, player_name, player_name, 
                                             start_date, end_date))
        
        return {
            'hitting': hitting_df,
            'pitching': pitching_df,
            'statcast': statcast_df
        }
    
    def get_league_averages(self, date):
        """Get league averages for comparison"""
        query = '''
            SELECT 
                AVG(batting_avg) as avg_batting_avg,
                AVG(on_base_pct) as avg_obp,
                AVG(slugging_pct) as avg_slg,
                AVG(ops) as avg_ops,
                AVG(era) as avg_era,
                AVG(whip) as avg_whip
            FROM (
                SELECT batting_avg, on_base_pct, slugging_pct, ops, NULL as era, NULL as whip
                FROM daily_hitting WHERE date = ?
                UNION ALL
                SELECT NULL, NULL, NULL, NULL, era, whip
                FROM daily_pitching WHERE date = ?
            )
        '''
        
        return pd.read_sql_query(query, self.conn, params=(date, date))
    
    def close(self):
        """Close database connection"""
        self.conn.close()

if __name__ == "__main__":
    db = MLBDatabaseManager()
    
    print("Initializing database with last 45 days of data...")
    print("This will take several minutes...\n")
    
    end_date = datetime.now() - timedelta(days=1)
    start_date = end_date - timedelta(days=44)
    
    db.fetch_and_store_date_range(start_date, end_date)
    
    print("\n✓ Database initialized successfully!")
    db.close()