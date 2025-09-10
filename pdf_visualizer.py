import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Rectangle
import pandas as pd
import numpy as np
from datetime import datetime
from database_manager import MLBDatabaseManager
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.utils import ImageReader
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io
from PIL import Image as PILImage, ImageDraw, ImageOps
import requests
import os

class PDFPlayerVisualizer:
    def __init__(self, db_manager):
        self.db = db_manager
        
    def download_player_headshot(self, player_id, size='medium'):
        """Download player headshot from MLB API"""
        if not player_id:
            return None
            
        # Different size options
        size_configs = {
            'small': 'w_120,h_180',
            'medium': 'w_180,h_270', 
            'large': 'w_213,h_320'
        }
        
        size_param = size_configs.get(size, size_configs['medium'])
        
        # Primary MLB photo API endpoint
        url = f"https://img.mlbstatic.com/mlb-photos/image/upload/c_fill,g_auto/{size_param}/v1/people/{player_id}/headshot/67/current"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200 and len(response.content) > 1000:  # Ensure it's a real image
                return PILImage.open(io.BytesIO(response.content))
        except Exception as e:
            print(f"Failed to download headshot for player {player_id}: {e}")
            
        # Fallback URL
        fallback_url = f"https://securea.mlb.com/mlb/images/players/head_shot/{player_id}.jpg"
        try:
            response = requests.get(fallback_url, timeout=10)
            if response.status_code == 200:
                return PILImage.open(io.BytesIO(response.content))
        except Exception as e:
            print(f"Fallback headshot download failed for player {player_id}: {e}")
            
        return None
    
    def create_circular_headshot(self, image, size=(150, 150)):
        """Convert headshot to circular format"""
        if not image:
            return None
            
        # Resize image to square
        image = image.resize(size, PILImage.Resampling.LANCZOS)
        
        # Create circular mask
        mask = PILImage.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)
        
        # Apply mask to create circular image
        output = PILImage.new('RGBA', size, (0, 0, 0, 0))
        output.paste(image, (0, 0))
        output.putalpha(mask)
        
        return output
    
    def get_team_colors(self, team_code):
        """Get team colors for styling"""
        team_colors = {
            'LAA': ('#BA0021', '#C4CED4'),  # Angels
            'HOU': ('#002D62', '#EB6E1F'),  # Astros  
            'OAK': ('#003831', '#EFB21E'),  # Athletics
            'TOR': ('#134A8E', '#1D2D5C'),  # Blue Jays
            'ATL': ('#CE1141', '#13274F'),  # Braves
            'MIL': ('#12284B', '#FFC52F'),  # Brewers
            'STL': ('#C41E3A', '#FEDB00'),  # Cardinals
            'CHC': ('#0E3386', '#CC3433'),  # Cubs
            'ARI': ('#A71930', '#E3D4AD'),  # Diamondbacks
            'LAD': ('#005A9C', '#EF3E42'),  # Dodgers
            'SF': ('#FD5A1E', '#27251F'),   # Giants
            'CLE': ('#E31937', '#0C2340'),  # Guardians
            'SEA': ('#0C2C56', '#005C5C'),  # Mariners
            'MIA': ('#00A3E0', '#FF6600'),  # Marlins
            'NYM': ('#002D72', '#FF5910'),  # Mets
            'WSH': ('#AB0003', '#14225A'),  # Nationals
            'BAL': ('#DF4601', '#000000'),  # Orioles
            'SD': ('#2F241D', '#FFC425'),   # Padres
            'PHI': ('#E81828', '#002D72'),  # Phillies
            'PIT': ('#FDB827', '#27251F'),  # Pirates
            'TEX': ('#003278', '#C0111F'),  # Rangers
            'TB': ('#092C5C', '#8FBCE6'),   # Rays
            'BOS': ('#BD3039', '#0C2340'),  # Red Sox
            'CIN': ('#C6011F', '#000000'),  # Reds
            'COL': ('#33006F', '#C4CED4'),  # Rockies
            'CWS': ('#27251F', '#C4CED4'),  # White Sox
            'DET': ('#0C2340', '#FA4616'),  # Tigers
            'KC': ('#004687', '#BD9B60'),   # Royals
            'MIN': ('#002B5C', '#D31145'),  # Twins
            'NYY': ('#132448', '#C4CED4'),  # Yankees
        }
        return team_colors.get(team_code, ('#000000', '#FFFFFF'))  # Default black/white
    
    def create_team_logo_placeholder(self, team_code):
        """Create a simple text-based team logo placeholder"""
        if not team_code:
            return None
            
        # Get team colors
        primary_color, secondary_color = self.get_team_colors(team_code)
        
        # Create a simple logo with team abbreviation
        logo_size = (80, 80)
        logo = PILImage.new('RGBA', logo_size, (255, 255, 255, 0))  # Transparent background
        draw = ImageDraw.Draw(logo)
        
        # Draw circle background in team colors
        try:
            # Convert hex colors to RGB
            if primary_color.startswith('#'):
                rgb_color = tuple(int(primary_color[i:i+2], 16) for i in (1, 3, 5))
            else:
                rgb_color = (0, 0, 0)  # Default to black
                
            # Draw circular background
            draw.ellipse([5, 5, 75, 75], fill=rgb_color + (255,), outline=(0, 0, 0, 255), width=2)
            
            # Add team text (this is basic - would need proper font loading for better results)
            # For now, just return the colored circle
            print(f"✓ Created placeholder logo for {team_code}")
            return logo
            
        except Exception as e:
            print(f"✗ Failed to create placeholder logo for {team_code}: {e}")
            return None
    
    def get_team_logo(self, team_code):
        """Get team logo from local files (PNG or SVG)"""
        if not team_code:
            return None
        
        # Map team codes to SVG filenames
        team_svg_map = {
            'ARI': 'arizona_diamondbacks.svg',
            'ATL': 'atlanta_braves.svg', 
            'BAL': 'baltimore_orioles.svg',
            'BOS': 'boston_redsox.svg',
            'CHC': 'chicago_cubs.svg',
            'CWS': 'chicago_whitesox.svg',
            'CIN': 'cincinnati_reds.svg',
            'CLE': 'cleveland_guardians.svg',
            'COL': 'colorado_rockies.svg',
            'DET': 'detroit_tigers.svg',
            'HOU': 'houston_astros.svg',
            'KC': 'kansascity_royals.svg',
            'LAA': 'losangeles_angles.svg',
            'LAD': 'losangeles_dodgers.svg',
            'MIA': 'miami_marlins.svg',
            'MIL': 'milwaukee_brewers.svg',
            'MIN': 'minnesota_twins.svg',
            'NYM': 'newyork_mets.svg',
            'NYY': 'newyork_yankees.svg',
            'OAK': 'athletics.svg',
            'PHI': 'philadelphia_phillies.svg',
            'PIT': 'pittsburgh_pirates.svg',
            'SD': 'sandiego_padres.svg',
            'SF': 'sanfrancisco_giants.svg',
            'SEA': 'seattle_mariners.svg',
            'STL': 'stlouis_cardinals.svg',
            'TB': 'tampabay_rays.svg',
            'TEX': 'texas_rangers.svg',
            'TOR': 'toronto_bluejays.svg',
            'WSH': 'washington_nationals.svg'
        }
            
        # Try SVG with mapped filename, then PNG with team code, then fallback
        logo_paths = [
            f"team_logos/{team_svg_map.get(team_code, '')}" if team_svg_map.get(team_code) else None,
            f"team_logos/{team_code}.png",
            f"team_logos/{team_code}.svg"
        ]
        
        # Remove None values
        logo_paths = [path for path in logo_paths if path]
        
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    if logo_path.endswith('.svg'):
                        # Handle SVG files
                        logo = self._convert_svg_to_png(logo_path)
                        if logo:
                            print(f"✓ Loaded {team_code} logo from SVG file")
                            return logo
                    else:
                        # Handle PNG files
                        logo = PILImage.open(logo_path)
                        print(f"✓ Loaded {team_code} logo from PNG file")
                        return logo
                except Exception as e:
                    print(f"✗ Failed to load {team_code} logo from {logo_path}: {e}")
                    continue
        
        print(f"✗ No logo files found for {team_code}")
        # Fallback to placeholder if no local files found
        print(f"Creating fallback placeholder for {team_code}...")
        return self.create_team_logo_placeholder(team_code)
    
    def _convert_svg_to_png(self, svg_path, size=(100, 100)):
        """Convert SVG to PNG using cairosvg or other methods"""
        try:
            # Method 1: Try using cairosvg (most reliable for SVG)
            try:
                import cairosvg
                from io import BytesIO
                
                # Convert SVG to PNG bytes
                png_bytes = cairosvg.svg2png(url=svg_path, output_width=size[0], output_height=size[1])
                
                # Convert to PIL Image
                png_image = PILImage.open(BytesIO(png_bytes))
                return png_image.convert('RGBA')
                
            except ImportError:
                print("cairosvg not available, trying alternative method...")
                
            # Method 2: Try using wand (ImageMagick)
            try:
                from wand.image import Image as WandImage
                
                with WandImage(filename=svg_path) as img:
                    img.format = 'png'
                    img.resize(size[0], size[1])
                    blob = img.make_blob()
                    
                return PILImage.open(BytesIO(blob)).convert('RGBA')
                
            except ImportError:
                print("wand not available, trying svglib...")
                
            # Method 3: Try using svglib + reportlab
            try:
                from svglib.svglib import renderSVG
                from reportlab.graphics import renderPM
                from io import BytesIO
                
                drawing = renderSVG.renderSVG(svg_path)
                png_bytes = renderPM.drawToString(drawing, fmt='PNG')
                
                png_image = PILImage.open(BytesIO(png_bytes))
                return png_image.resize(size, PILImage.Resampling.LANCZOS).convert('RGBA')
                
            except ImportError:
                print("svglib not available")
                
        except Exception as e:
            print(f"Failed to convert SVG {svg_path}: {e}")
            
        return None
    
    def create_headshot_with_logo(self, headshot, team_code, headshot_size=(120, 120)):
        """Create headshot with team logo overlay"""
        if not headshot:
            return None
            
        # Create circular headshot
        circular_headshot = self.create_circular_headshot(headshot, headshot_size)
        if not circular_headshot:
            return None
            
        # Download team logo
        team_logo = self.download_team_logo(team_code)
        if not team_logo:
            return circular_headshot  # Return without logo if download fails
            
        try:
            # Resize logo to be small overlay (about 1/3 the size of headshot)
            logo_size = (headshot_size[0] // 3, headshot_size[1] // 3)
            team_logo = team_logo.resize(logo_size, PILImage.Resampling.LANCZOS)
            
            # Ensure logo has alpha channel
            if team_logo.mode != 'RGBA':
                team_logo = team_logo.convert('RGBA')
            
            # Position logo in bottom-right corner of headshot
            logo_position = (
                headshot_size[0] - logo_size[0] - 5,  # 5px margin from right
                headshot_size[1] - logo_size[1] - 5   # 5px margin from bottom
            )
            
            # Create a copy of the headshot to modify
            result = circular_headshot.copy()
            
            # Paste logo with transparency
            result.paste(team_logo, logo_position, team_logo)
            
            return result
            
        except Exception as e:
            print(f"Failed to overlay team logo: {e}")
            return circular_headshot  # Return headshot without logo
        
    def create_player_report(self, player_name, save_path=None):
        """Create a professional PDF report for a player"""
        print(f"\nGenerating PDF report for {player_name}...")
        
        player_data = self.db.get_player_data(player_name)
        
        if player_data['statcast'].empty:
            print(f"No data found for {player_name}")
            return None
        
        # Get player info and stats
        player_info = self._get_player_info(player_name, player_data)
        recent_stats = self._get_recent_games_stats(player_name, player_data)
        
        # Set up PDF
        if not save_path:
            safe_name = player_name.replace(' ', '_').replace(',', '')
            save_path = f"{safe_name}_report.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(
            save_path,
            pagesize=letter,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch
        )
        
        # Build content
        story = []
        
        # Add header with headshot
        player_id = self.db.get_player_id_from_name(player_name)
        self._add_header_with_headshot(story, player_info, player_id)
        
        # Add stats table
        self._add_stats_table(story, recent_stats)
        
        # Add charts
        chart_images = self._create_charts(player_name, player_data)
        self._add_charts_to_story(story, chart_images)
        
        # Build PDF
        doc.build(story)
        
        # Clean up any temp files after PDF is built
        try:
            import glob
            for temp_file in glob.glob('temp_headshot_*.png'):
                os.remove(temp_file)
            for temp_file in glob.glob('temp_logo_*.png'):
                os.remove(temp_file)
        except:
            pass
        
        print(f"✓ PDF report saved as {save_path}")
        return save_path
    
    def _get_player_info(self, player_name, data):
        """Extract player basic information"""
        statcast = data['statcast']
        
        if statcast.empty:
            return {}
            
        recent = statcast.iloc[0] if not statcast.empty else None
        
        # Determine if primarily pitcher
        is_pitcher = (statcast['player_name'] == player_name).any()
        position = "Pitcher" if is_pitcher else "Hitter"
        
        team = recent['home_team'] if recent is not None else "Unknown"
        bats = recent['stand'] if recent is not None else "Unknown"
        throws = recent['p_throws'] if recent is not None else "Unknown"
        
        return {
            'name': player_name,
            'position': position,
            'team': team,
            'bats': bats,
            'throws': throws
        }
    
    def _get_recent_games_stats(self, player_name, data):
        """Get stats for recent games plus 45-day totals"""
        statcast = data['statcast']
        
        if statcast.empty:
            return pd.DataFrame()
            
        # Get player ID for lookups
        player_id = self.db.get_player_id_from_name(player_name)
        if not player_id:
            return pd.DataFrame()
            
        # Get unique game dates
        game_dates = sorted(statcast['game_date'].dropna().unique(), reverse=True)[:3]
        
        stats_list = []
        
        # Determine if player is primarily a hitter or pitcher
        as_hitter = statcast[statcast['batter'] == str(player_id)]
        as_pitcher = statcast[statcast['player_name'] == player_name]
        
        is_primarily_hitter = len(as_hitter) >= len(as_pitcher)
        
        # Calculate stats for each recent game
        for game_date in game_dates:
            game_data = statcast[statcast['game_date'] == game_date]
            
            if is_primarily_hitter:
                hitter_data = game_data[game_data['batter'] == str(player_id)]
                if not hitter_data.empty:
                    stats = self._calculate_hitter_game_stats(hitter_data, game_date)
                    stats_list.append(stats)
            else:
                pitcher_data = game_data[game_data['player_name'] == player_name]
                if not pitcher_data.empty:
                    stats = self._calculate_pitcher_game_stats(pitcher_data, game_date)
                    stats_list.append(stats)
        
        # Add 45-day totals
        if is_primarily_hitter:
            # Hitter totals - same logic as game stats
            at_bat_events = ['single', 'double', 'triple', 'home_run', 'field_out', 'strikeout', 
                            'force_out', 'grounded_into_double_play', 'field_error', 'pop_out', 
                            'flyout', 'lineout']
            
            plate_appearances = as_hitter[as_hitter['events'].notna()]
            at_bats = plate_appearances[plate_appearances['events'].isin(at_bat_events)]
            total_abs = len(at_bats)
            
            hits = len(plate_appearances[plate_appearances['events'].isin(['single', 'double', 'triple', 'home_run'])])
            home_runs = len(plate_appearances[plate_appearances['events'] == 'home_run'])
            doubles = len(plate_appearances[plate_appearances['events'] == 'double'])
            triples = len(plate_appearances[plate_appearances['events'] == 'triple'])
            
            total_bases = hits + doubles + (2 * triples) + (3 * home_runs)
            slg = total_bases / total_abs if total_abs > 0 else 0
            avg = hits / total_abs if total_abs > 0 else 0
            
            stats_list.append({
                'Date': '45-Day Total',
                'AB': total_abs,
                'H': hits,
                'HR': home_runs,
                'AVG': f"{avg:.3f}",
                'SLG': f"{slg:.3f}"
            })
        else:
            # Pitcher totals
            pitcher_data = as_pitcher
            total_pitches = len(pitcher_data)
            strikeouts = len(pitcher_data[pitcher_data['events'] == 'strikeout'])
            outs = len(pitcher_data[pitcher_data['events'].isin(['strikeout', 'field_out', 'force_out', 'grounded_into_double_play', 'pop_out', 'flyout'])])
            innings = outs / 3.0
            
            stats_list.append({
                'Date': '45-Day Total',
                'IP': f"{innings:.1f}",
                'K': strikeouts,
                'Pitches': total_pitches
            })
            
        return pd.DataFrame(stats_list)
    
    def _calculate_hitter_game_stats(self, game_data, game_date):
        """Calculate hitting stats for a single game"""
        # At-bats = plate appearances that end the at-bat (not walks, HBP, sac flies, etc.)
        at_bat_events = ['single', 'double', 'triple', 'home_run', 'field_out', 'strikeout', 
                        'force_out', 'grounded_into_double_play', 'field_error', 'pop_out', 
                        'flyout', 'lineout']
        
        # Get unique plate appearances (grouped by at-bat outcome)
        plate_appearances = game_data[game_data['events'].notna()]
        
        at_bats = plate_appearances[plate_appearances['events'].isin(at_bat_events)]
        total_abs = len(at_bats)
        
        hits = len(plate_appearances[plate_appearances['events'].isin(['single', 'double', 'triple', 'home_run'])])
        home_runs = len(plate_appearances[plate_appearances['events'] == 'home_run'])
        doubles = len(plate_appearances[plate_appearances['events'] == 'double'])
        triples = len(plate_appearances[plate_appearances['events'] == 'triple'])
        
        # Calculate slugging
        total_bases = hits + doubles + (2 * triples) + (3 * home_runs)
        slg = total_bases / total_abs if total_abs > 0 else 0
        avg = hits / total_abs if total_abs > 0 else 0
        
        return {
            'Date': str(game_date)[:10],
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
        outs = len(game_data[game_data['events'].isin(['strikeout', 'field_out', 'force_out', 'grounded_into_double_play', 'pop_out', 'flyout'])])
        innings = outs / 3.0
        
        return {
            'Date': str(game_date)[:10],
            'IP': f"{innings:.1f}",
            'K': strikeouts,
            'Pitches': total_pitches
        }
    
    def _add_header_with_headshot(self, story, player_info, player_id):
        """Add player header with headshot to PDF"""
        styles = getSampleStyleSheet()
        
        # Download and process headshot
        headshot_image = None
        temp_headshot_path = None
        if player_id:
            print(f"Downloading headshot for player ID {player_id}...")
            raw_headshot = self.download_player_headshot(player_id, size='medium')
            if raw_headshot:
                # Create clean circular headshot (no logo overlay)
                print("Creating clean circular headshot...")
                clean_headshot = self.create_circular_headshot(raw_headshot, size=(120, 120))
                if clean_headshot:
                    # Save to absolute path in current directory
                    import os
                    temp_headshot_path = os.path.abspath(f'temp_headshot_{player_id}.png')
                    clean_headshot.save(temp_headshot_path, 'PNG')
                    
                    # Check file exists before creating Image
                    if os.path.exists(temp_headshot_path):
                        headshot_image = Image(temp_headshot_path, width=1.2*inch, height=1.2*inch)
                        print(f"✓ Headshot loaded from {temp_headshot_path}")
                    else:
                        print(f"✗ Headshot file not found: {temp_headshot_path}")
                        headshot_image = None
        
        # Create header layout table
        header_data = []
        
        if headshot_image:
            # Download and prepare full team logo for right side
            team_code = player_info.get('team', '')
            team_logo_image = None
            
            if team_code:
                print(f"Loading {team_code} team logo...")
                team_logo = self.get_team_logo(team_code)
                if team_logo:
                    # Resize team logo for header (larger than overlay)
                    team_logo_resized = team_logo.resize((80, 80), PILImage.Resampling.LANCZOS)
                    
                    # Save team logo temporarily
                    temp_logo_path = os.path.abspath(f'temp_logo_{team_code}.png')
                    team_logo_resized.save(temp_logo_path, 'PNG')
                    
                    if os.path.exists(temp_logo_path):
                        team_logo_image = Image(temp_logo_path, width=0.8*inch, height=0.8*inch)
            
            # Header with headshot on left, info in center, team logo on right
            player_name = player_info.get('name', 'Unknown Player')
            
            # Create custom style for player details
            details_style = ParagraphStyle(
                'PlayerDetails',
                parent=styles['Normal'],
                fontSize=12,
                leading=16,
                leftIndent=0,
                spaceAfter=6,
                alignment=1  # Center alignment
            )
            
            details_text = f"""
            <font size=18><b>{player_name}</b></font><br/>
            <b>Team:</b> {player_info.get('team', 'N/A')}<br/>
            <b>Bats/Throws:</b> {player_info.get('bats', 'N/A')}/{player_info.get('throws', 'N/A')}
            """
            
            details_para = Paragraph(details_text, details_style)
            
            # Create 3-column layout: headshot | player info | team logo
            if team_logo_image:
                header_data = [[headshot_image, details_para, team_logo_image]]
                col_widths = [1.5*inch, 5*inch, 1.5*inch]
            else:
                # Fallback to 2-column if no team logo
                header_data = [[headshot_image, details_para]]
                col_widths = [1.5*inch, 6.5*inch]
            
            # Create table
            header_table = Table(header_data, colWidths=col_widths)
            header_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # Center headshot
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),    # Center align text
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), # Vertical center
                ('LEFTPADDING', (1, 0), (1, 0), 20),   # Add space between headshot and text
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            
            # If we have 3 columns, style the team logo column
            if team_logo_image:
                header_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),  # Center headshot
                    ('ALIGN', (1, 0), (1, 0), 'LEFT'),    # Left align text
                    ('ALIGN', (2, 0), (2, 0), 'CENTER'),  # Center team logo
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), # Vertical center
                    ('LEFTPADDING', (1, 0), (1, 0), 20),   # Add space between headshot and text
                    ('RIGHTPADDING', (1, 0), (1, 0), 20),  # Add space between text and logo
                    ('TOPPADDING', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ]))
            
            story.append(header_table)
        else:
            # Fallback to text-only header
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=12,
                alignment=TA_CENTER,
                textColor=colors.black,
                fontName='Helvetica-Bold'
            )
            
            story.append(Paragraph(player_info.get('name', 'Unknown Player'), title_style))
            
            details_style = ParagraphStyle(
                'Details',
                parent=styles['Normal'],
                fontSize=14,
                spaceAfter=20,
                alignment=TA_CENTER,
                textColor=colors.black
            )
            
            details_text = f"""
            <b>Team:</b> {player_info.get('team', 'N/A')} | 
            <b>Bats/Throws:</b> {player_info.get('bats', 'N/A')}/{player_info.get('throws', 'N/A')}
            """
            
            story.append(Paragraph(details_text, details_style))
        
        story.append(Spacer(1, 20))
    
    def _add_stats_table(self, story, stats_df):
        """Add statistics table to PDF"""
        if stats_df.empty:
            return
        
        # Prepare table data
        headers = list(stats_df.columns)
        table_data = [headers]
        
        for _, row in stats_df.iterrows():
            table_data.append(list(row.values))
        
        # Create table
        table = Table(table_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch])
        
        # Style the table
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            
            # Data styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            
            # Grid styling
            ('GRID', (0, 0), (-1, -1), 2, colors.black),
            ('LINEWIDTH', (0, 0), (-1, -1), 2),
            
            # Row spacing
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.white]),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 30))
    
    def _create_charts(self, player_name, data):
        """Create matplotlib charts and return as images"""
        statcast = data['statcast']
        
        if statcast.empty:
            return []
        
        # Get player ID to determine hitter vs pitcher
        player_id = self.db.get_player_id_from_name(player_name)
        if not player_id:
            return []
            
        as_hitter = statcast[statcast['batter'] == str(player_id)]
        as_pitcher = statcast[statcast['player_name'] == player_name]
        
        is_primarily_hitter = len(as_hitter) >= len(as_pitcher)
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle(f'{player_name} - Performance Charts', fontsize=16, fontweight='bold')
        
        if is_primarily_hitter:
            self._create_hitter_charts(axes, as_hitter)
        else:
            self._create_pitcher_charts(axes, as_pitcher, statcast)
        
        plt.tight_layout()
        
        # Save to memory
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
        img_buffer.seek(0)
        plt.close()
        
        return [img_buffer]
    
    def _create_hitter_charts(self, axes, hitter_data):
        """Create charts specific to hitters"""
        
        # Chart 1: Exit Velocity Distribution
        if 'launch_speed' in hitter_data.columns:
            velocities = hitter_data['launch_speed'].dropna()
            if not velocities.empty:
                axes[0, 0].hist(velocities, bins=15, alpha=0.7, color='blue', edgecolor='black')
                axes[0, 0].set_title('Exit Velocity Distribution', fontweight='bold')
                axes[0, 0].set_xlabel('Exit Velocity (mph)')
                axes[0, 0].set_ylabel('Frequency')
                axes[0, 0].grid(True, alpha=0.3)
        
        # Chart 2: Launch Angle vs Exit Velocity
        if 'launch_angle' in hitter_data.columns and 'launch_speed' in hitter_data.columns:
            launch_angles = hitter_data['launch_angle'].dropna()
            exit_velos = hitter_data['launch_speed'].dropna()
            if not launch_angles.empty and not exit_velos.empty:
                # Get matching indices
                valid_data = hitter_data[hitter_data['launch_angle'].notna() & hitter_data['launch_speed'].notna()]
                if not valid_data.empty:
                    axes[0, 1].scatter(valid_data['launch_angle'], valid_data['launch_speed'], 
                                     alpha=0.6, s=30, color='red', edgecolors='black')
                    axes[0, 1].set_title('Launch Angle vs Exit Velocity', fontweight='bold')
                    axes[0, 1].set_xlabel('Launch Angle (degrees)')
                    axes[0, 1].set_ylabel('Exit Velocity (mph)')
                    axes[0, 1].grid(True, alpha=0.3)
        
        # Chart 3: Hit Type Distribution
        if 'events' in hitter_data.columns:
            hit_events = hitter_data[hitter_data['events'].isin(['single', 'double', 'triple', 'home_run'])]
            if not hit_events.empty:
                event_counts = hit_events['events'].value_counts()
                event_counts.plot(kind='bar', ax=axes[1, 0], color='green', alpha=0.7)
                axes[1, 0].set_title('Hit Type Distribution', fontweight='bold')
                axes[1, 0].set_xlabel('Hit Type')
                axes[1, 0].set_ylabel('Count')
                axes[1, 0].tick_params(axis='x', rotation=45)
                axes[1, 0].grid(True, alpha=0.3)
        
        # Chart 4: Game-by-Game At-Bats
        game_dates = sorted(hitter_data['game_date'].dropna().unique())[:10]
        if len(game_dates) > 1:
            daily_abs = []
            for date in game_dates:
                daily_count = len(hitter_data[hitter_data['game_date'] == date])
                daily_abs.append(daily_count)
            
            axes[1, 1].plot(range(len(daily_abs)), daily_abs, marker='o', linewidth=2, color='purple')
            axes[1, 1].set_title('Plate Appearances per Game', fontweight='bold')
            axes[1, 1].set_xlabel('Games (Recent to Past)')
            axes[1, 1].set_ylabel('Plate Appearances')
            axes[1, 1].grid(True, alpha=0.3)
    
    def _create_pitcher_charts(self, axes, pitcher_data, full_statcast):
        """Create charts specific to pitchers"""
        
        # Chart 1: Pitch Velocity Distribution
        if 'release_speed' in pitcher_data.columns:
            velocities = pitcher_data['release_speed'].dropna()
            if not velocities.empty:
                axes[0, 0].hist(velocities, bins=20, alpha=0.7, color='steelblue', edgecolor='black')
                axes[0, 0].set_title('Pitch Velocity Distribution', fontweight='bold')
                axes[0, 0].set_xlabel('Velocity (mph)')
                axes[0, 0].set_ylabel('Frequency')
                axes[0, 0].grid(True, alpha=0.3)
        
        # Chart 2: Strike Zone Heat Map (simplified)
        if 'plate_x' in pitcher_data.columns and 'plate_z' in pitcher_data.columns:
            plate_x = pitcher_data['plate_x'].dropna()
            plate_z = pitcher_data['plate_z'].dropna()
            if not plate_x.empty and not plate_z.empty:
                axes[0, 1].scatter(plate_x, plate_z, alpha=0.6, s=20, color='red')
                axes[0, 1].set_title('Pitch Location', fontweight='bold')
                axes[0, 1].set_xlabel('Horizontal Position')
                axes[0, 1].set_ylabel('Vertical Position')
                axes[0, 1].grid(True, alpha=0.3)
        
        # Chart 3: Pitch Type Usage
        if 'pitch_type' in pitcher_data.columns:
            pitch_counts = pitcher_data['pitch_type'].value_counts()
            if not pitch_counts.empty:
                pitch_counts.plot(kind='bar', ax=axes[1, 0], color='green', alpha=0.7)
                axes[1, 0].set_title('Pitch Type Usage', fontweight='bold')
                axes[1, 0].set_xlabel('Pitch Type')
                axes[1, 0].set_ylabel('Count')
                axes[1, 0].tick_params(axis='x', rotation=45)
                axes[1, 0].grid(True, alpha=0.3)
        
        # Chart 4: Game-by-Game Performance
        game_dates = sorted(pitcher_data['game_date'].dropna().unique())[:10]
        if len(game_dates) > 1:
            daily_pitches = []
            for date in game_dates:
                daily_count = len(pitcher_data[pitcher_data['game_date'] == date])
                daily_pitches.append(daily_count)
            
            axes[1, 1].plot(range(len(daily_pitches)), daily_pitches, marker='o', linewidth=2, color='purple')
            axes[1, 1].set_title('Pitches per Game (Recent)', fontweight='bold')
            axes[1, 1].set_xlabel('Games (Recent to Past)')
            axes[1, 1].set_ylabel('Pitch Count')
            axes[1, 1].grid(True, alpha=0.3)
    
    def _add_charts_to_story(self, story, chart_images):
        """Add chart images to PDF story"""
        for img_buffer in chart_images:
            # Convert to PIL Image and then to reportlab Image
            pil_img = PILImage.open(img_buffer)
            
            # Save temporarily
            temp_path = 'temp_chart.png'
            pil_img.save(temp_path)
            
            # Add to story
            img = Image(temp_path, width=8*inch, height=6*inch)
            story.append(img)
            story.append(Spacer(1, 20))