import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from database_manager import MLBDatabaseManager
import requests
from io import BytesIO
from PIL import Image
import base64

class PlayerVisualizer:
    def __init__(self, db_manager):
        self.db = db_manager
        
    def get_player_info(self, player_name, data):
        """Extract player basic information"""
        statcast = data['statcast']
        
        if statcast.empty:
            return {}
            
        # Get most recent game info
        recent = statcast.iloc[0] if not statcast.empty else None
        
        # Determine if primarily hitter or pitcher
        is_pitcher = not data['pitching'].empty
        is_hitter = not data['hitting'].empty
        
        if is_pitcher and is_hitter:
            position = "Two-Way Player"
        elif is_pitcher:
            position = "Pitcher" 
        else:
            # Try to get position from statcast data or default to hitter
            position = "Hitter"
            
        team = recent['home_team'] if recent is not None else "Unknown"
        
        # Get batting/throwing info from statcast
        bats = recent['stand'] if recent is not None else "Unknown"
        throws = recent['p_throws'] if recent is not None else "Unknown"
        
        return {
            'name': player_name,
            'position': position,
            'team': team,
            'bats': bats,
            'throws': throws
        }
    
    def get_recent_games_stats(self, player_name, data):
        """Get stats for 3 most recent games plus 45-day totals"""
        statcast = data['statcast']
        
        if statcast.empty:
            return pd.DataFrame()
            
        # Get unique game dates
        game_dates = sorted(statcast['game_date'].dropna().unique(), reverse=True)[:3]
        
        stats_list = []
        
        # Determine if this is primarily a pitcher (player_name matches) or we need to look for them as a batter
        is_pitcher_data = (statcast['player_name'] == player_name).any()
        
        # Calculate stats for each recent game
        for game_date in game_dates:
            game_data = statcast[statcast['game_date'] == game_date]
            
            if is_pitcher_data:
                # Player is the pitcher in this data
                pitcher_data = game_data[game_data['player_name'] == player_name]
                if not pitcher_data.empty:
                    stats = self._calculate_pitcher_game_stats(pitcher_data, game_date)
                    stats_list.append(stats)
            else:
                # Player should be found as a batter (need to match by ID or different logic)
                # For now, skip hitter logic since our data seems to be pitcher-centric
                pass
        
        # Add 45-day totals
        total_stats = self._calculate_45_day_totals(player_name, data)
        if total_stats:
            stats_list.append(total_stats)
            
        return pd.DataFrame(stats_list)
    
    def _calculate_hitter_game_stats(self, game_data, game_date):
        """Calculate hitting stats for a single game"""
        total_abs = len(game_data[game_data['type'].isin(['X', 'S'])])  # At-bats (excluding walks, HBP)
        hits = len(game_data[game_data['events'].isin(['single', 'double', 'triple', 'home_run'])])
        home_runs = len(game_data[game_data['events'] == 'home_run'])
        doubles = len(game_data[game_data['events'] == 'double'])
        triples = len(game_data[game_data['events'] == 'triple'])
        
        # Calculate slugging
        total_bases = hits + doubles + (2 * triples) + (3 * home_runs)
        slg = total_bases / total_abs if total_abs > 0 else 0
        avg = hits / total_abs if total_abs > 0 else 0
        
        return {
            'Date': game_date,
            'AB': total_abs,
            'H': hits,
            'HR': home_runs,
            'AVG': f"{avg:.3f}",
            'SLG': f"{slg:.3f}"
        }
    
    def _calculate_pitcher_game_stats(self, game_data, game_date):
        """Calculate pitching stats for a single game"""
        total_pitches = len(game_data)
        strikeouts = len(game_data[game_data['events'] == 'strikeout'])
        
        # Estimate innings (rough approximation)
        outs = len(game_data[game_data['events'].isin(['strikeout', 'field_out', 'force_out', 'grounded_into_double_play'])])
        innings = outs / 3.0
        
        return {
            'Date': game_date,
            'IP': f"{innings:.1f}",
            'K': strikeouts,
            'Pitches': total_pitches
        }
    
    def _calculate_45_day_totals(self, player_name, data):
        """Calculate 45-day totals"""
        statcast = data['statcast']
        
        # Check if this player appears as pitcher (in player_name column)
        is_pitcher_data = (statcast['player_name'] == player_name).any()
        
        if is_pitcher_data:
            # Calculate pitching totals
            pitcher_data = statcast[statcast['player_name'] == player_name]
            total_pitches = len(pitcher_data)
            strikeouts = len(pitcher_data[pitcher_data['events'] == 'strikeout'])
            
            # Calculate innings more accurately
            outs = len(pitcher_data[pitcher_data['events'].isin(['strikeout', 'field_out', 'force_out', 'grounded_into_double_play', 'pop_out', 'flyout'])])
            innings = outs / 3.0
            
            return {
                'Date': '45-Day Total',
                'IP': f"{innings:.1f}",
                'K': strikeouts,
                'Pitches': total_pitches
            }
        else:
            # For now, return empty for hitters since we need better logic to match batter IDs to names
            return {
                'Date': '45-Day Total',
                'Note': 'Hitter data needs ID mapping'
            }
        
    def create_player_dashboard(self, player_name, save_html=True):
        """Create comprehensive dashboard for a specific player"""
        print(f"\nGenerating dashboard for {player_name}...")
        
        player_data = self.db.get_player_data(player_name)
        
        if player_data['statcast'].empty:
            print(f"No data found for {player_name}")
            return None
        
        # Get player info and recent games stats
        player_info = self.get_player_info(player_name, player_data)
        recent_stats = self.get_recent_games_stats(player_name, player_data)
        
        # Create the new layout dashboard
        fig = self._create_modern_dashboard(player_name, player_data, player_info, recent_stats)
        
        if save_html:
            filename = f"{player_name.replace(' ', '_')}_dashboard.html"
            fig.write_html(filename)
            print(f"✓ Dashboard saved as {filename}")
        
        return fig
    
    def _create_modern_dashboard(self, player_name, data, player_info, recent_stats):
        """Create modern dashboard with header and stats table"""
        
        # Create subplot structure: header area + stats table + visualizations
        fig = make_subplots(
            rows=4, cols=4,
            row_heights=[0.2, 0.3, 0.25, 0.25],  # Header, stats table, charts row 1, charts row 2
            subplot_titles=['', '', '', '',  # Header row - no titles
                           '', '', '', '',  # Stats table row - no titles
                           'Exit Velocity vs Launch Angle', 'Spray Chart', 'Pitch Velocity', 'Performance Trends',
                           'Hot Zones', 'Count Performance', 'Key Metrics', 'Recent Form'],
            specs=[
                [{'colspan': 4}, None, None, None],  # Header spans all columns
                [{'type': 'table', 'colspan': 4}, None, None, None],  # Stats table spans all columns
                [{'type': 'scatter'}, {'type': 'scatter'}, {'type': 'histogram'}, {'type': 'scatter'}],
                [{'type': 'heatmap'}, {'type': 'bar'}, {'type': 'indicator'}, {'type': 'scatter'}]
            ],
            vertical_spacing=0.08
        )
        
        # Add header with player info
        self._add_player_header(fig, player_info, row=1, col=1)
        
        # Add recent games stats table
        self._add_stats_table(fig, recent_stats, row=2, col=1)
        
        # Add visualization charts (simplified for now)
        self._add_basic_charts(fig, player_name, data)
        
        # Update layout
        fig.update_layout(
            height=1200,
            title=f"{player_name} - Performance Dashboard",
            showlegend=False,
            font=dict(size=12),
            plot_bgcolor='white',
            paper_bgcolor='white'
        )
        
        return fig
    
    def _add_player_header(self, fig, player_info, row, col):
        """Add player information header"""
        
        # Create header text
        header_text = f"""
        <b>{player_info.get('name', 'Unknown Player')}</b><br>
        Position: {player_info.get('position', 'N/A')}<br>
        Team: {player_info.get('team', 'N/A')}<br>
        Bats/Throws: {player_info.get('bats', 'N/A')}/{player_info.get('throws', 'N/A')}
        """
        
        # Add as annotation since we can't put text in subplot directly
        fig.add_annotation(
            text=header_text,
            xref="paper", yref="paper",
            x=0.5, y=0.92,
            showarrow=False,
            font=dict(size=16),
            align="center"
        )
    
    def _add_stats_table(self, fig, stats_df, row, col):
        """Add recent games statistics table"""
        
        if stats_df.empty:
            # Add empty table message
            fig.add_annotation(
                text="No recent game data available",
                xref="paper", yref="paper",
                x=0.5, y=0.6,
                showarrow=False,
                font=dict(size=14)
            )
            return
        
        # Create table
        table_data = []
        headers = list(stats_df.columns)
        
        # Add each row
        for _, row_data in stats_df.iterrows():
            table_data.append(list(row_data.values))
        
        fig.add_trace(
            go.Table(
                header=dict(
                    values=headers,
                    fill_color='white',
                    align='center',
                    font=dict(size=14, color='black', family='Arial Black'),
                    line=dict(color='black', width=3)
                ),
                cells=dict(
                    values=list(zip(*table_data)) if table_data else [[]],
                    fill_color='white',
                    align='center',
                    font=dict(size=12, color='black', family='Arial Black'),
                    line=dict(color='black', width=3)
                )
            ),
            row=row, col=col
        )
    
    def _add_basic_charts(self, fig, player_name, data):
        """Add basic visualization charts"""
        statcast = data['statcast']
        
        if statcast.empty:
            return
            
        # Determine if hitter or pitcher
        as_hitter = statcast[statcast['batter'] == player_name]
        as_pitcher = statcast[statcast['pitcher'] == player_name]
        
        if len(as_hitter) >= len(as_pitcher):
            self._add_hitter_charts(fig, as_hitter)
        else:
            self._add_pitcher_charts(fig, as_pitcher)
    
    def _add_hitter_charts(self, fig, hitter_data):
        """Add charts for hitters"""
        
        # Exit velocity vs launch angle (batted balls only)
        batted_balls = hitter_data[hitter_data['launch_speed'].notna()].copy()
        if not batted_balls.empty:
            fig.add_trace(
                go.Scatter(
                    x=batted_balls['launch_angle'],
                    y=batted_balls['launch_speed'],
                    mode='markers',
                    marker=dict(size=8, opacity=0.6, color='blue'),
                    name='Batted Balls'
                ),
                row=3, col=1
            )
        
        # Spray chart (simplified)
        if not batted_balls.empty and 'hc_x' in batted_balls.columns:
            fig.add_trace(
                go.Scatter(
                    x=batted_balls['hc_x'],
                    y=batted_balls['hc_y'], 
                    mode='markers',
                    marker=dict(size=6, opacity=0.7, color='red'),
                    name='Hit Location'
                ),
                row=3, col=2
            )
    
    def _add_pitcher_charts(self, fig, pitcher_data):
        """Add charts for pitchers"""
        
        # Pitch velocity distribution
        if not pitcher_data.empty and 'release_speed' in pitcher_data.columns:
            velocities = pitcher_data['release_speed'].dropna()
            if not velocities.empty:
                fig.add_trace(
                    go.Histogram(
                        x=velocities,
                        nbinsx=20,
                        name='Pitch Velocity'
                    ),
                    row=3, col=3
                )
    
    def _create_hitter_dashboard(self, player_name, data):
        """Create dashboard for a hitter"""
        statcast = data['statcast']
        
        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=(
                'Exit Velocity vs Launch Angle', 'Rolling 10-Game Average', 'Spray Chart',
                'Pitch Type Performance', 'Count Performance', 'Hot/Cold Zones',
                'Exit Velocity Trends', 'Performance by Pitcher Hand', 'Key Metrics'
            ),
            specs=[
                [{'type': 'scatter'}, {'type': 'scatter'}, {'type': 'scatter'}],
                [{'type': 'bar'}, {'type': 'bar'}, {'type': 'heatmap'}],
                [{'type': 'scatter'}, {'type': 'bar'}, {'type': 'indicator'}]
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.10
        )
        
        batted_balls = statcast[statcast['launch_speed'].notna()].copy()
        if not batted_balls.empty:
            barrel_mask = (batted_balls['launch_speed'] >= 98) & \
                         (batted_balls['launch_angle'].between(26, 30))
            colors = ['red' if b else 'blue' for b in barrel_mask]
            
            fig.add_trace(
                go.Scatter(
                    x=batted_balls['launch_angle'],
                    y=batted_balls['launch_speed'],
                    mode='markers',
                    marker=dict(color=colors, size=8, opacity=0.6),
                    text=batted_balls['events'],
                    hovertemplate='LA: %{x}°<br>EV: %{y} mph<br>%{text}<extra></extra>',
                    showlegend=False
                ),
                row=1, col=1
            )
            
            fig.add_shape(
                type="rect", x0=10, y0=98, x1=30, y1=116,
                fillcolor="rgba(0,255,0,0.1)", line=dict(color="green", width=2),
                row=1, col=1
            )
        
        if not batted_balls.empty:
            batted_balls['date'] = pd.to_datetime(batted_balls['date'])
            daily_avg = batted_balls.groupby('date')['launch_speed'].mean().reset_index()
            daily_avg['rolling_avg'] = daily_avg['launch_speed'].rolling(window=10, min_periods=1).mean()
            
            fig.add_trace(
                go.Scatter(
                    x=daily_avg['date'],
                    y=daily_avg['rolling_avg'],
                    mode='lines+markers',
                    line=dict(color='orange', width=2),
                    marker=dict(size=6),
                    showlegend=False
                ),
                row=1, col=2
            )
        
        hits = statcast[(statcast['hc_x'].notna()) & (statcast['hc_y'].notna())]
        if not hits.empty:
            hit_colors = {'single': 'blue', 'double': 'green', 'triple': 'orange', 'home_run': 'red'}
            colors = [hit_colors.get(e, 'gray') for e in hits['events']]
            
            fig.add_trace(
                go.Scatter(
                    x=hits['hc_x'] - 125,
                    y=200 - hits['hc_y'],
                    mode='markers',
                    marker=dict(color=colors, size=10),
                    text=hits['events'],
                    hovertemplate='%{text}<extra></extra>',
                    showlegend=False
                ),
                row=1, col=3
            )
        
        pitch_types = statcast.groupby('pitch_type')['events'].value_counts().unstack(fill_value=0)
        if not pitch_types.empty:
            for event in ['single', 'double', 'triple', 'home_run']:
                if event in pitch_types.columns:
                    fig.add_trace(
                        go.Bar(
                            x=pitch_types.index,
                            y=pitch_types[event],
                            name=event,
                            showlegend=False
                        ),
                        row=2, col=1
                    )
        
        count_perf = statcast.groupby(['balls', 'strikes'])['launch_speed'].mean().reset_index()
        if not count_perf.empty:
            count_perf['count'] = count_perf['balls'].astype(str) + '-' + count_perf['strikes'].astype(str)
            fig.add_trace(
                go.Bar(
                    x=count_perf['count'],
                    y=count_perf['launch_speed'],
                    marker_color='purple',
                    showlegend=False
                ),
                row=2, col=2
            )
        
        zone_data = statcast.groupby('zone')['launch_speed'].mean().reset_index()
        if not zone_data.empty and len(zone_data) > 1:
            zone_matrix = np.zeros((3, 3))
            for _, row in zone_data.iterrows():
                if 1 <= row['zone'] <= 9:
                    zone_idx = int(row['zone']) - 1
                    zone_matrix[zone_idx // 3, zone_idx % 3] = row['launch_speed']
            
            fig.add_trace(
                go.Heatmap(
                    z=zone_matrix,
                    colorscale='RdYlBu',
                    showscale=True,
                    colorbar=dict(x=0.65, len=0.25, y=0.38)
                ),
                row=2, col=3
            )
        
        if not batted_balls.empty:
            batted_balls['date'] = pd.to_datetime(batted_balls['date'])
            daily_velo = batted_balls.groupby('date')['launch_speed'].agg(['mean', 'max']).reset_index()
            
            fig.add_trace(
                go.Scatter(
                    x=daily_velo['date'],
                    y=daily_velo['mean'],
                    mode='lines',
                    name='Avg EV',
                    line=dict(color='blue'),
                    showlegend=True
                ),
                row=3, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=daily_velo['date'],
                    y=daily_velo['max'],
                    mode='lines',
                    name='Max EV',
                    line=dict(color='red'),
                    showlegend=True
                ),
                row=3, col=1
            )
        
        vs_hand = statcast.groupby('p_throws')['launch_speed'].mean().reset_index()
        if not vs_hand.empty:
            fig.add_trace(
                go.Bar(
                    x=vs_hand['p_throws'],
                    y=vs_hand['launch_speed'],
                    marker_color=['lightblue', 'lightcoral'],
                    showlegend=False
                ),
                row=3, col=2
            )
        
        if not batted_balls.empty:
            avg_ev = batted_balls['launch_speed'].mean()
            max_ev = batted_balls['launch_speed'].max()
            barrel_rate = (barrel_mask.sum() / len(batted_balls) * 100) if 'barrel_mask' in locals() else 0
            
            fig.add_trace(
                go.Indicator(
                    mode="number",
                    value=avg_ev,
                    title={"text": f"Avg Exit Velo: {avg_ev:.1f} mph"},
                    domain={'y': [0.7, 1], 'x': [0, 1]}
                ),
                row=3, col=3
            )
            
            fig.add_trace(
                go.Indicator(
                    mode="number",
                    value=max_ev,
                    title={"text": f"Max Exit Velo: {max_ev:.1f} mph"},
                    domain={'y': [0.35, 0.65], 'x': [0, 1]}
                ),
                row=3, col=3
            )
            
            fig.add_trace(
                go.Indicator(
                    mode="number",
                    value=barrel_rate,
                    title={"text": f"Barrel Rate: {barrel_rate:.1f}%"},
                    domain={'y': [0, 0.3], 'x': [0, 1]}
                ),
                row=3, col=3
            )
        
        fig.update_xaxes(title_text="Launch Angle (°)", row=1, col=1)
        fig.update_yaxes(title_text="Exit Velocity (mph)", row=1, col=1)
        fig.update_xaxes(title_text="Date", row=1, col=2)
        fig.update_yaxes(title_text="Rolling Avg EV (mph)", row=1, col=2)
        fig.update_xaxes(title_text="Horizontal", row=1, col=3)
        fig.update_yaxes(title_text="Depth", row=1, col=3)
        fig.update_xaxes(title_text="Pitch Type", row=2, col=1)
        fig.update_yaxes(title_text="Count", row=2, col=1)
        fig.update_xaxes(title_text="Count", row=2, col=2)
        fig.update_yaxes(title_text="Avg Exit Velocity", row=2, col=2)
        fig.update_xaxes(title_text="Date", row=3, col=1)
        fig.update_yaxes(title_text="Exit Velocity (mph)", row=3, col=1)
        fig.update_xaxes(title_text="Pitcher Hand", row=3, col=2)
        fig.update_yaxes(title_text="Avg Exit Velocity", row=3, col=2)
        
        fig.update_layout(
            title=f"{player_name} - Hitting Performance Dashboard (Last 45 Days)",
            height=1000,
            showlegend=True,
            template='plotly_white'
        )
        
        return fig
    
    def _create_pitcher_dashboard(self, player_name, data):
        """Create dashboard for a pitcher"""
        statcast = data['statcast']
        
        fig = make_subplots(
            rows=3, cols=3,
            subplot_titles=(
                'Velocity by Pitch Type', 'Movement Profile', 'Release Point Consistency',
                'Pitch Usage', 'Velocity Trends', 'Spin Rate Analysis',
                'Strike Zone Heat Map', 'Whiff Rate by Pitch', 'Key Metrics'
            ),
            specs=[
                [{'type': 'violin'}, {'type': 'scatter'}, {'type': 'scatter'}],
                [{'type': 'pie'}, {'type': 'scatter'}, {'type': 'scatter'}],
                [{'type': 'heatmap'}, {'type': 'bar'}, {'type': 'indicator'}]
            ],
            vertical_spacing=0.12,
            horizontal_spacing=0.10
        )
        
        pitches = statcast[statcast['pitcher'] == player_name].copy()
        
        if not pitches.empty and 'pitch_type' in pitches.columns:
            for i, pitch_type in enumerate(pitches['pitch_type'].value_counts().head(5).index):
                pitch_data = pitches[pitches['pitch_type'] == pitch_type]['release_speed'].dropna()
                if not pitch_data.empty:
                    fig.add_trace(
                        go.Violin(
                            y=pitch_data,
                            name=pitch_type,
                            box_visible=True,
                            meanline_visible=True,
                            showlegend=False
                        ),
                        row=1, col=1
                    )
        
        if 'pfx_x' in pitches.columns and 'pfx_z' in pitches.columns:
            movement_data = pitches[['pfx_x', 'pfx_z', 'pitch_type']].dropna()
            if not movement_data.empty:
                for pitch_type in movement_data['pitch_type'].unique()[:5]:
                    pitch_movement = movement_data[movement_data['pitch_type'] == pitch_type]
                    fig.add_trace(
                        go.Scatter(
                            x=pitch_movement['pfx_x'] * 12,
                            y=pitch_movement['pfx_z'] * 12,
                            mode='markers',
                            name=pitch_type,
                            marker=dict(size=8, opacity=0.6),
                            showlegend=True
                        ),
                        row=1, col=2
                    )
        
        if 'release_pos_x' in pitches.columns and 'release_pos_z' in pitches.columns:
            release_data = pitches[['release_pos_x', 'release_pos_z', 'pitch_type']].dropna()
            if not release_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=release_data['release_pos_x'],
                        y=release_data['release_pos_z'],
                        mode='markers',
                        marker=dict(
                            color=pd.Categorical(release_data['pitch_type']).codes,
                            colorscale='Viridis',
                            size=6,
                            opacity=0.5
                        ),
                        text=release_data['pitch_type'],
                        hovertemplate='%{text}<br>X: %{x:.2f}<br>Z: %{y:.2f}<extra></extra>',
                        showlegend=False
                    ),
                    row=1, col=3
                )
        
        if 'pitch_type' in pitches.columns:
            pitch_usage = pitches['pitch_type'].value_counts()
            fig.add_trace(
                go.Pie(
                    labels=pitch_usage.index,
                    values=pitch_usage.values,
                    hole=0.3,
                    showlegend=True
                ),
                row=2, col=1
            )
        
        if 'release_speed' in pitches.columns:
            pitches['date'] = pd.to_datetime(pitches['date'])
            daily_velo = pitches.groupby(['date', 'pitch_type'])['release_speed'].mean().reset_index()
            
            for pitch_type in daily_velo['pitch_type'].unique()[:3]:
                pitch_velo = daily_velo[daily_velo['pitch_type'] == pitch_type]
                fig.add_trace(
                    go.Scatter(
                        x=pitch_velo['date'],
                        y=pitch_velo['release_speed'],
                        mode='lines+markers',
                        name=pitch_type,
                        showlegend=True
                    ),
                    row=2, col=2
                )
        
        if 'release_spin_rate' in pitches.columns:
            spin_data = pitches[['release_speed', 'release_spin_rate', 'pitch_type']].dropna()
            if not spin_data.empty:
                fig.add_trace(
                    go.Scatter(
                        x=spin_data['release_speed'],
                        y=spin_data['release_spin_rate'],
                        mode='markers',
                        marker=dict(
                            color=pd.Categorical(spin_data['pitch_type']).codes,
                            colorscale='Plasma',
                            size=6,
                            opacity=0.6,
                            showscale=True,
                            colorbar=dict(x=0.65, len=0.25, y=0.38)
                        ),
                        text=spin_data['pitch_type'],
                        hovertemplate='%{text}<br>Velo: %{x:.1f}<br>Spin: %{y:.0f}<extra></extra>',
                        showlegend=False
                    ),
                    row=2, col=3
                )
        
        if 'plate_x' in pitches.columns and 'plate_z' in pitches.columns:
            x_bins = np.linspace(-1.5, 1.5, 10)
            z_bins = np.linspace(0, 4, 10)
            
            hist, xedges, yedges = np.histogram2d(
                pitches['plate_x'].dropna(),
                pitches['plate_z'].dropna(),
                bins=[x_bins, z_bins]
            )
            
            fig.add_trace(
                go.Heatmap(
                    z=hist.T,
                    x=xedges[:-1],
                    y=yedges[:-1],
                    colorscale='Hot',
                    showscale=True,
                    colorbar=dict(x=0.3, len=0.25, y=0.12)
                ),
                row=3, col=1
            )
            
            fig.add_shape(
                type="rect", x0=-0.83, y0=1.5, x1=0.83, y1=3.5,
                line=dict(color="white", width=2),
                row=3, col=1
            )
        
        whiff_data = pitches[pitches['description'].str.contains('swinging_strike', na=False)]
        if not whiff_data.empty:
            whiff_rate = whiff_data.groupby('pitch_type').size() / pitches.groupby('pitch_type').size() * 100
            fig.add_trace(
                go.Bar(
                    x=whiff_rate.index,
                    y=whiff_rate.values,
                    marker_color='red',
                    showlegend=False
                ),
                row=3, col=2
            )
        
        if not pitches.empty:
            avg_velo = pitches['release_speed'].mean() if 'release_speed' in pitches.columns else 0
            avg_spin = pitches['release_spin_rate'].mean() if 'release_spin_rate' in pitches.columns else 0
            k_rate = (pitches['events'] == 'strikeout').sum() / len(pitches) * 100 if 'events' in pitches.columns else 0
            
            fig.add_trace(
                go.Indicator(
                    mode="number",
                    value=avg_velo,
                    title={"text": f"Avg Velocity: {avg_velo:.1f} mph"},
                    domain={'y': [0.7, 1], 'x': [0, 1]}
                ),
                row=3, col=3
            )
            
            fig.add_trace(
                go.Indicator(
                    mode="number",
                    value=avg_spin,
                    title={"text": f"Avg Spin: {avg_spin:.0f} rpm"},
                    domain={'y': [0.35, 0.65], 'x': [0, 1]}
                ),
                row=3, col=3
            )
            
            fig.add_trace(
                go.Indicator(
                    mode="number",
                    value=k_rate,
                    title={"text": f"K Rate: {k_rate:.1f}%"},
                    domain={'y': [0, 0.3], 'x': [0, 1]}
                ),
                row=3, col=3
            )
        
        fig.update_yaxes(title_text="Velocity (mph)", row=1, col=1)
        fig.update_xaxes(title_text="Horizontal Movement (in)", row=1, col=2)
        fig.update_yaxes(title_text="Vertical Movement (in)", row=1, col=2)
        fig.update_xaxes(title_text="Release X", row=1, col=3)
        fig.update_yaxes(title_text="Release Z", row=1, col=3)
        fig.update_xaxes(title_text="Date", row=2, col=2)
        fig.update_yaxes(title_text="Velocity (mph)", row=2, col=2)
        fig.update_xaxes(title_text="Velocity (mph)", row=2, col=3)
        fig.update_yaxes(title_text="Spin Rate (rpm)", row=2, col=3)
        fig.update_xaxes(title_text="Horizontal Location", row=3, col=1)
        fig.update_yaxes(title_text="Vertical Location", row=3, col=1)
        fig.update_xaxes(title_text="Pitch Type", row=3, col=2)
        fig.update_yaxes(title_text="Whiff Rate (%)", row=3, col=2)
        
        fig.update_layout(
            title=f"{player_name} - Pitching Performance Dashboard (Last 45 Days)",
            height=1000,
            showlegend=True,
            template='plotly_white'
        )
        
        return fig
    
    def _create_two_way_player_dashboard(self, player_name, data):
        """Create dashboard for a two-way player like Ohtani"""
        return self._create_hitter_dashboard(player_name, data)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        player_name = ' '.join(sys.argv[1:])
    else:
        player_name = input("Enter player name: ")
    
    db = MLBDatabaseManager()
    visualizer = PlayerVisualizer(db)
    
    fig = visualizer.create_player_dashboard(player_name)
    
    if fig:
        print(f"\n✓ Dashboard created successfully for {player_name}!")
    else:
        print(f"\n✗ Could not create dashboard for {player_name}")
    
    db.close()