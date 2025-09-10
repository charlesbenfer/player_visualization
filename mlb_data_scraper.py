import pybaseball as pyb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

pyb.cache.enable()

class MLBDataScraper:
    def __init__(self):
        self.yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        self.today = datetime.now().strftime('%Y-%m-%d')
        
    def get_yesterday_games(self):
        """Get all games from yesterday"""
        try:
            schedule = pyb.schedule_and_record(
                datetime.now().year,
                datetime.now().year
            )
            yesterday_games = schedule[schedule['Date'] == self.yesterday]
            return yesterday_games
        except Exception as e:
            print(f"Error fetching yesterday's games: {e}")
            return pd.DataFrame()
    
    def get_daily_pitcher_stats(self, date=None):
        """Get pitcher stats for a specific date"""
        if date is None:
            date = self.yesterday
            
        try:
            start_date = date
            end_date = date
            
            pitching_stats = pyb.pitching_stats(
                start_season=datetime.now().year,
                end_season=datetime.now().year,
                qual=0
            )
            
            return pitching_stats
        except Exception as e:
            print(f"Error fetching pitcher stats: {e}")
            return pd.DataFrame()
    
    def get_daily_hitter_stats(self, date=None):
        """Get hitter stats for a specific date"""
        if date is None:
            date = self.yesterday
            
        try:
            batting_stats = pyb.batting_stats(
                start_season=datetime.now().year,
                end_season=datetime.now().year,
                qual=0
            )
            
            return batting_stats
        except Exception as e:
            print(f"Error fetching hitter stats: {e}")
            return pd.DataFrame()
    
    def get_statcast_data(self, start_date=None, end_date=None):
        """Get Statcast data for specific date range"""
        if start_date is None:
            start_date = self.yesterday
        if end_date is None:
            end_date = self.yesterday
            
        try:
            statcast_data = pyb.statcast(start_dt=start_date, end_dt=end_date)
            return statcast_data
        except Exception as e:
            print(f"Error fetching Statcast data: {e}")
            return pd.DataFrame()
    
    def get_top_performers(self, df, metric, n=5, ascending=False):
        """Get top N performers based on a specific metric"""
        if metric in df.columns:
            return df.nlargest(n, metric) if not ascending else df.nsmallest(n, metric)
        return pd.DataFrame()
    
    def calculate_advanced_metrics(self, statcast_df):
        """Calculate advanced metrics from Statcast data"""
        if statcast_df.empty:
            return statcast_df
        
        metrics_df = statcast_df.copy()
        
        if 'launch_speed' in metrics_df.columns and 'launch_angle' in metrics_df.columns:
            barrel_mask = (
                (metrics_df['launch_speed'] >= 98) & 
                (metrics_df['launch_angle'].between(26, 30))
            )
            metrics_df['barrel'] = barrel_mask.fillna(False).astype(int)
        
        if 'release_speed' in metrics_df.columns:
            metrics_df['velo_percentile'] = pd.qcut(
                metrics_df['release_speed'].dropna(), 
                q=100, 
                labels=False, 
                duplicates='drop'
            )
        
        return metrics_df
    
    def get_team_standings(self):
        """Get current team standings"""
        try:
            standings = pyb.standings(datetime.now().year)
            return standings
        except Exception as e:
            print(f"Error fetching standings: {e}")
            return []

if __name__ == "__main__":
    scraper = MLBDataScraper()
    
    print(f"Fetching MLB data for {scraper.yesterday}")
    print("=" * 50)
    
    print("\nFetching yesterday's games...")
    games = scraper.get_yesterday_games()
    if not games.empty:
        print(f"Found {len(games)} games")
    
    print("\nFetching pitcher stats...")
    pitchers = scraper.get_daily_pitcher_stats()
    if not pitchers.empty:
        print(f"Found stats for {len(pitchers)} pitchers")
        print("\nTop 5 pitchers by strikeouts:")
        top_k = scraper.get_top_performers(pitchers, 'SO', n=5)
        if not top_k.empty:
            print(top_k[['Name', 'Team', 'SO', 'ERA', 'WHIP']].head())
    
    print("\nFetching hitter stats...")
    hitters = scraper.get_daily_hitter_stats()
    if not hitters.empty:
        print(f"Found stats for {len(hitters)} hitters")
        print("\nTop 5 hitters by home runs:")
        top_hr = scraper.get_top_performers(hitters, 'HR', n=5)
        if not top_hr.empty:
            print(top_hr[['Name', 'Team', 'HR', 'AVG', 'OPS']].head())
    
    print("\nFetching Statcast data...")
    statcast = scraper.get_statcast_data()
    if not statcast.empty:
        print(f"Found {len(statcast)} Statcast records")
        statcast_with_metrics = scraper.calculate_advanced_metrics(statcast)
        
    print("\nData collection complete!")