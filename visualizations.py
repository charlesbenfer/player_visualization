import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

class MLBVisualizer:
    def __init__(self):
        self.colors = {
            'primary': '#003f5c',
            'secondary': '#58508d',
            'accent': '#bc5090',
            'highlight': '#ff6361',
            'light': '#ffa600'
        }
        
        self.team_colors = {
            'NYY': ('#003087', '#FFFFFF'),
            'BOS': ('#BD3039', '#0C2340'),
            'LAD': ('#005A9C', '#FFFFFF'),
            'HOU': ('#002D62', '#EB6E1F'),
            'ATL': ('#CE1141', '#13274F'),
            'TB': ('#092C5C', '#8FBCE6'),
            'TOR': ('#134A8E', '#1D2D5C'),
            'SEA': ('#0C2C56', '#005C5C'),
            'PHI': ('#E81828', '#002D72'),
            'SD': ('#2F241D', '#FFC425'),
            'MIL': ('#FFC52F', '#12284B'),
            'STL': ('#C41E3A', '#0C2340'),
            'CHC': ('#0E3386', '#CC3433'),
            'MIN': ('#002B5C', '#D31145'),
            'CLE': ('#00385D', '#E50022'),
            'BAL': ('#DF4601', '#000000'),
            'SF': ('#FD5A1E', '#27251F'),
            'CWS': ('#27251F', '#C4CED4'),
            'DET': ('#0C2340', '#FA4616'),
            'TEX': ('#003278', '#C0111F'),
            'ARI': ('#A71930', '#E3D4AD'),
            'PIT': ('#FDB827', '#27251F'),
            'WSH': ('#AB0003', '#14225A'),
            'LAA': ('#BA0021', '#003263'),
            'NYM': ('#FF5910', '#002D72'),
            'OAK': ('#003831', '#EFB21E'),
            'CIN': ('#C6011F', '#000000'),
            'KC': ('#004687', '#BD9B60'),
            'MIA': ('#00A3E0', '#EF3340'),
            'COL': ('#33006F', '#C4CED4')
        }
        
    def create_player_performance_card(self, player_data, stat_type='hitter'):
        """Create a comprehensive player performance card"""
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Season Performance', 'Key Metrics', 
                          'Comparison to League Average', 'Trend Analysis'),
            specs=[[{'type': 'bar'}, {'type': 'indicator'}],
                   [{'type': 'scatter'}, {'type': 'scatter'}]]
        )
        
        if stat_type == 'hitter':
            self._add_hitter_metrics(fig, player_data)
        else:
            self._add_pitcher_metrics(fig, player_data)
            
        fig.update_layout(
            height=800,
            showlegend=False,
            title_text=f"Player Performance Dashboard - {player_data.get('Name', 'Unknown')}",
            title_font_size=24
        )
        
        return fig
    
    def create_top_performers_dashboard(self, hitters_df, pitchers_df):
        """Create a comprehensive dashboard for top performers"""
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                'Top Hitters by OPS', 'Top Pitchers by ERA',
                'Home Run Leaders', 'Strikeout Leaders',
                'Batting Average Leaders', 'WHIP Leaders'
            ),
            specs=[[{'type': 'bar'}, {'type': 'bar'}],
                   [{'type': 'bar'}, {'type': 'bar'}],
                   [{'type': 'bar'}, {'type': 'bar'}]]
        )
        
        top_ops = hitters_df.nlargest(10, 'OPS')
        fig.add_trace(
            go.Bar(x=top_ops['Name'], y=top_ops['OPS'],
                  marker_color=self.colors['primary'],
                  text=top_ops['OPS'].round(3),
                  textposition='outside'),
            row=1, col=1
        )
        
        top_era = pitchers_df.nsmallest(10, 'ERA')
        fig.add_trace(
            go.Bar(x=top_era['Name'], y=top_era['ERA'],
                  marker_color=self.colors['secondary'],
                  text=top_era['ERA'].round(2),
                  textposition='outside'),
            row=1, col=2
        )
        
        top_hr = hitters_df.nlargest(10, 'HR')
        fig.add_trace(
            go.Bar(x=top_hr['Name'], y=top_hr['HR'],
                  marker_color=self.colors['accent'],
                  text=top_hr['HR'],
                  textposition='outside'),
            row=2, col=1
        )
        
        top_so = pitchers_df.nlargest(10, 'SO')
        fig.add_trace(
            go.Bar(x=top_so['Name'], y=top_so['SO'],
                  marker_color=self.colors['highlight'],
                  text=top_so['SO'],
                  textposition='outside'),
            row=2, col=2
        )
        
        top_avg = hitters_df.nlargest(10, 'AVG')
        fig.add_trace(
            go.Bar(x=top_avg['Name'], y=top_avg['AVG'],
                  marker_color=self.colors['light'],
                  text=top_avg['AVG'].round(3),
                  textposition='outside'),
            row=3, col=1
        )
        
        top_whip = pitchers_df.nsmallest(10, 'WHIP')
        fig.add_trace(
            go.Bar(x=top_whip['Name'], y=top_whip['WHIP'],
                  marker_color='#2ca02c',
                  text=top_whip['WHIP'].round(2),
                  textposition='outside'),
            row=3, col=2
        )
        
        fig.update_xaxes(tickangle=45)
        fig.update_layout(
            height=1200,
            showlegend=False,
            title_text="MLB Top Performers Dashboard",
            title_font_size=28
        )
        
        return fig
    
    def create_statcast_heatmap(self, statcast_df):
        """Create exit velocity and launch angle heatmap"""
        if 'launch_speed' not in statcast_df.columns or 'launch_angle' not in statcast_df.columns:
            return None
            
        fig = go.Figure(data=go.Scatter(
            x=statcast_df['launch_angle'],
            y=statcast_df['launch_speed'],
            mode='markers',
            marker=dict(
                size=8,
                color=statcast_df['launch_speed'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Exit Velocity (mph)")
            ),
            text=statcast_df['player_name'] if 'player_name' in statcast_df.columns else None,
            hovertemplate='Launch Angle: %{x}°<br>Exit Velocity: %{y} mph<extra></extra>'
        ))
        
        fig.add_shape(
            type="rect",
            x0=10, y0=98, x1=30, y1=116,
            fillcolor="rgba(255, 0, 0, 0.1)",
            line=dict(color="red", width=2)
        )
        
        fig.add_annotation(
            x=20, y=107,
            text="Sweet Spot",
            showarrow=False,
            font=dict(color="red", size=12)
        )
        
        fig.update_layout(
            title="Exit Velocity vs Launch Angle Analysis",
            xaxis_title="Launch Angle (degrees)",
            yaxis_title="Exit Velocity (mph)",
            height=600,
            template='plotly_dark'
        )
        
        return fig
    
    def create_team_comparison_radar(self, team_stats):
        """Create radar chart comparing team statistics"""
        categories = ['Batting Avg', 'OPS', 'ERA', 'WHIP', 'Fielding %']
        
        fig = go.Figure()
        
        for team in team_stats['Team'].unique()[:5]:
            team_data = team_stats[team_stats['Team'] == team].iloc[0]
            
            values = [
                team_data.get('AVG', 0),
                team_data.get('OPS', 0),
                1 / team_data.get('ERA', 1),
                1 / team_data.get('WHIP', 1),
                team_data.get('FLD%', 0)
            ]
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name=team
            ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="Team Performance Comparison",
            height=500
        )
        
        return fig
    
    def create_pitch_velocity_distribution(self, statcast_df):
        """Create pitch velocity distribution by pitch type"""
        if 'release_speed' not in statcast_df.columns or 'pitch_type' not in statcast_df.columns:
            return None
            
        pitch_types = statcast_df['pitch_type'].value_counts().head(6).index
        
        fig = go.Figure()
        
        for pitch in pitch_types:
            pitch_data = statcast_df[statcast_df['pitch_type'] == pitch]['release_speed'].dropna()
            
            fig.add_trace(go.Violin(
                y=pitch_data,
                name=pitch,
                box_visible=True,
                meanline_visible=True
            ))
        
        fig.update_layout(
            title="Pitch Velocity Distribution by Type",
            yaxis_title="Velocity (mph)",
            xaxis_title="Pitch Type",
            height=500,
            showlegend=False
        )
        
        return fig
    
    def create_home_run_trajectory(self, hr_data):
        """Create 3D visualization of home run trajectories"""
        if hr_data.empty:
            return None
            
        fig = go.Figure(data=[go.Scatter3d(
            x=hr_data.get('hc_x', []),
            y=hr_data.get('hc_y', []),
            z=hr_data.get('launch_speed', []),
            mode='markers',
            marker=dict(
                size=hr_data.get('launch_speed', []) / 10,
                color=hr_data.get('launch_angle', []),
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Launch Angle")
            ),
            text=hr_data.get('player_name', [])
        )])
        
        fig.update_layout(
            title="Home Run Trajectories",
            scene=dict(
                xaxis_title="Horizontal Position",
                yaxis_title="Depth",
                zaxis_title="Exit Velocity"
            ),
            height=600
        )
        
        return fig
    
    def save_dashboard_as_image(self, fig, filename):
        """Save plotly figure as static image"""
        fig.write_image(f"{filename}.png", width=1200, height=800, scale=2)
        return f"{filename}.png"
    
    def _add_hitter_metrics(self, fig, player_data):
        """Add hitter-specific metrics to figure"""
        pass
    
    def _add_pitcher_metrics(self, fig, player_data):
        """Add pitcher-specific metrics to figure"""
        pass