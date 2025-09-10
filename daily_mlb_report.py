import pybaseball as pyb
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

from mlb_data_scraper import MLBDataScraper
from visualizations import MLBVisualizer

class DailyMLBReport:
    def __init__(self):
        self.scraper = MLBDataScraper()
        self.visualizer = MLBVisualizer()
        self.date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
    def generate_daily_report(self):
        """Generate comprehensive daily MLB report with visualizations"""
        print(f"\n{'='*60}")
        print(f"MLB Daily Performance Report - {self.date}")
        print(f"{'='*60}\n")
        
        hitters_df = self.scraper.get_daily_hitter_stats()
        pitchers_df = self.scraper.get_daily_pitcher_stats()
        statcast_df = self.scraper.get_statcast_data()
        
        if not hitters_df.empty and not pitchers_df.empty:
            self.create_all_visualizations(hitters_df, pitchers_df, statcast_df)
            
            top_performers = self.identify_top_performers(hitters_df, pitchers_df)
            self.generate_linkedin_content(top_performers)
        else:
            print("Unable to fetch data. Please check your connection.")
    
    def create_all_visualizations(self, hitters_df, pitchers_df, statcast_df):
        """Create all visualizations for the daily report"""
        
        print("Creating Top Performers Dashboard...")
        top_performers_fig = self.visualizer.create_top_performers_dashboard(
            hitters_df, pitchers_df
        )
        top_performers_fig.write_html('top_performers_dashboard.html')
        print("✓ Top Performers Dashboard saved as 'top_performers_dashboard.html'")
        
        if not statcast_df.empty:
            print("\nCreating Statcast Analysis...")
            
            statcast_heatmap = self.visualizer.create_statcast_heatmap(statcast_df)
            if statcast_heatmap:
                statcast_heatmap.write_html('statcast_heatmap.html')
                print("✓ Statcast Heatmap saved as 'statcast_heatmap.html'")
            
            pitch_velocity = self.visualizer.create_pitch_velocity_distribution(statcast_df)
            if pitch_velocity:
                pitch_velocity.write_html('pitch_velocity_distribution.html')
                print("✓ Pitch Velocity Distribution saved as 'pitch_velocity_distribution.html'")
            
            hr_data = statcast_df[statcast_df['events'] == 'home_run'] if 'events' in statcast_df.columns else pd.DataFrame()
            if not hr_data.empty:
                hr_trajectory = self.visualizer.create_home_run_trajectory(hr_data)
                if hr_trajectory:
                    hr_trajectory.write_html('home_run_trajectories.html')
                    print("✓ Home Run Trajectories saved as 'home_run_trajectories.html'")
        
        self.create_advanced_analytics(hitters_df, pitchers_df, statcast_df)
        
    def create_advanced_analytics(self, hitters_df, pitchers_df, statcast_df):
        """Create advanced analytics visualizations"""
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                'OPS vs Batting Average', 
                'ERA vs WHIP',
                'Power vs Contact Rate',
                'Strikeout Rate vs Walk Rate'
            ),
            specs=[[{'type': 'scatter'}, {'type': 'scatter'}],
                   [{'type': 'scatter'}, {'type': 'scatter'}]]
        )
        
        top_50_hitters = hitters_df.nlargest(50, 'PA') if 'PA' in hitters_df.columns else hitters_df.head(50)
        if 'AVG' in top_50_hitters.columns and 'OPS' in top_50_hitters.columns:
            fig.add_trace(
                go.Scatter(
                    x=top_50_hitters['AVG'],
                    y=top_50_hitters['OPS'],
                    mode='markers',
                    marker=dict(
                        size=top_50_hitters['HR'] if 'HR' in top_50_hitters.columns else 10,
                        color=top_50_hitters['HR'] if 'HR' in top_50_hitters.columns else 'blue',
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title="Home Runs", x=0.45, y=0.85)
                    ),
                    text=top_50_hitters['Name'],
                    hovertemplate='%{text}<br>AVG: %{x:.3f}<br>OPS: %{y:.3f}<extra></extra>'
                ),
                row=1, col=1
            )
        
        top_50_pitchers = pitchers_df.nlargest(50, 'IP') if 'IP' in pitchers_df.columns else pitchers_df.head(50)
        if 'ERA' in top_50_pitchers.columns and 'WHIP' in top_50_pitchers.columns:
            fig.add_trace(
                go.Scatter(
                    x=top_50_pitchers['ERA'],
                    y=top_50_pitchers['WHIP'],
                    mode='markers',
                    marker=dict(
                        size=top_50_pitchers['SO'] / 10 if 'SO' in top_50_pitchers.columns else 10,
                        color=top_50_pitchers['SO'] if 'SO' in top_50_pitchers.columns else 'red',
                        colorscale='Plasma',
                        showscale=True,
                        colorbar=dict(title="Strikeouts", x=1.0, y=0.85)
                    ),
                    text=top_50_pitchers['Name'],
                    hovertemplate='%{text}<br>ERA: %{x:.2f}<br>WHIP: %{y:.2f}<extra></extra>'
                ),
                row=1, col=2
            )
        
        if 'ISO' in top_50_hitters.columns and 'AVG' in top_50_hitters.columns:
            fig.add_trace(
                go.Scatter(
                    x=top_50_hitters['ISO'],
                    y=top_50_hitters['AVG'],
                    mode='markers',
                    marker=dict(
                        size=8,
                        color='purple'
                    ),
                    text=top_50_hitters['Name'],
                    hovertemplate='%{text}<br>ISO: %{x:.3f}<br>AVG: %{y:.3f}<extra></extra>'
                ),
                row=2, col=1
            )
        
        if 'K%' in top_50_pitchers.columns and 'BB%' in top_50_pitchers.columns:
            fig.add_trace(
                go.Scatter(
                    x=top_50_pitchers['K%'],
                    y=top_50_pitchers['BB%'],
                    mode='markers',
                    marker=dict(
                        size=8,
                        color='orange'
                    ),
                    text=top_50_pitchers['Name'],
                    hovertemplate='%{text}<br>K%: %{x:.1f}<br>BB%: %{y:.1f}<extra></extra>'
                ),
                row=2, col=2
            )
        
        fig.update_xaxes(title_text="Batting Average", row=1, col=1)
        fig.update_yaxes(title_text="OPS", row=1, col=1)
        fig.update_xaxes(title_text="ERA", row=1, col=2)
        fig.update_yaxes(title_text="WHIP", row=1, col=2)
        fig.update_xaxes(title_text="ISO (Power)", row=2, col=1)
        fig.update_yaxes(title_text="Batting Average", row=2, col=1)
        fig.update_xaxes(title_text="Strikeout %", row=2, col=2)
        fig.update_yaxes(title_text="Walk %", row=2, col=2)
        
        fig.update_layout(
            height=800,
            title_text="Advanced Baseball Analytics",
            title_font_size=24,
            showlegend=False
        )
        
        fig.write_html('advanced_analytics.html')
        print("✓ Advanced Analytics saved as 'advanced_analytics.html'")
    
    def identify_top_performers(self, hitters_df, pitchers_df):
        """Identify top performers of the day"""
        top_performers = {
            'top_hitter_ops': None,
            'top_hitter_hr': None,
            'top_pitcher_era': None,
            'top_pitcher_so': None
        }
        
        if not hitters_df.empty:
            if 'OPS' in hitters_df.columns:
                top_ops = hitters_df.nlargest(1, 'OPS').iloc[0]
                top_performers['top_hitter_ops'] = {
                    'name': top_ops['Name'],
                    'team': top_ops.get('Team', 'Unknown'),
                    'ops': top_ops['OPS'],
                    'avg': top_ops.get('AVG', 0),
                    'hr': top_ops.get('HR', 0)
                }
            
            if 'HR' in hitters_df.columns:
                top_hr = hitters_df.nlargest(1, 'HR').iloc[0]
                top_performers['top_hitter_hr'] = {
                    'name': top_hr['Name'],
                    'team': top_hr.get('Team', 'Unknown'),
                    'hr': top_hr['HR'],
                    'rbi': top_hr.get('RBI', 0),
                    'ops': top_hr.get('OPS', 0)
                }
        
        if not pitchers_df.empty:
            qualified_pitchers = pitchers_df[pitchers_df['IP'] >= 50] if 'IP' in pitchers_df.columns else pitchers_df
            
            if 'ERA' in qualified_pitchers.columns and len(qualified_pitchers) > 0:
                top_era = qualified_pitchers.nsmallest(1, 'ERA').iloc[0]
                top_performers['top_pitcher_era'] = {
                    'name': top_era['Name'],
                    'team': top_era.get('Team', 'Unknown'),
                    'era': top_era['ERA'],
                    'whip': top_era.get('WHIP', 0),
                    'so': top_era.get('SO', 0)
                }
            
            if 'SO' in pitchers_df.columns:
                top_so = pitchers_df.nlargest(1, 'SO').iloc[0]
                top_performers['top_pitcher_so'] = {
                    'name': top_so['Name'],
                    'team': top_so.get('Team', 'Unknown'),
                    'so': top_so['SO'],
                    'era': top_so.get('ERA', 0),
                    'ip': top_so.get('IP', 0)
                }
        
        return top_performers
    
    def generate_linkedin_content(self, top_performers):
        """Generate LinkedIn post content"""
        print("\n" + "="*60)
        print("LINKEDIN POST CONTENT")
        print("="*60 + "\n")
        
        content = f"""⚾ MLB Performance Highlights - {self.date} ⚾

🔥 TODAY'S STANDOUT PERFORMERS 🔥

"""
        
        if top_performers['top_hitter_ops']:
            p = top_performers['top_hitter_ops']
            content += f"""🏆 BEST OPS: {p['name']} ({p['team']})
   • OPS: {p['ops']:.3f}
   • AVG: {p['avg']:.3f} | HR: {p['hr']}

"""
        
        if top_performers['top_hitter_hr']:
            p = top_performers['top_hitter_hr']
            content += f"""💪 HOME RUN LEADER: {p['name']} ({p['team']})
   • Home Runs: {p['hr']}
   • RBI: {p['rbi']} | OPS: {p['ops']:.3f}

"""
        
        if top_performers['top_pitcher_era']:
            p = top_performers['top_pitcher_era']
            content += f"""⭐ BEST ERA (Qualified): {p['name']} ({p['team']})
   • ERA: {p['era']:.2f}
   • WHIP: {p['whip']:.2f} | SO: {p['so']}

"""
        
        if top_performers['top_pitcher_so']:
            p = top_performers['top_pitcher_so']
            content += f"""🔥 STRIKEOUT LEADER: {p['name']} ({p['team']})
   • Strikeouts: {p['so']}
   • ERA: {p['era']:.2f} | IP: {p['ip']:.1f}

"""
        
        content += """📊 Full interactive dashboards and advanced analytics available!

#MLB #Baseball #DataAnalytics #SportsAnalytics #BaseballStats"""
        
        print(content)
        
        with open('linkedin_post.txt', 'w') as f:
            f.write(content)
        print("\n✓ LinkedIn post content saved to 'linkedin_post.txt'")
        
        return content

if __name__ == "__main__":
    report = DailyMLBReport()
    report.generate_daily_report()