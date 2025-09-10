#!/usr/bin/env python3
"""
Create clean, professional team logos using team colors and abbreviations
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_team_logos():
    """Create professional team logos with team colors and abbreviations"""
    
    # Team data with primary and secondary colors
    teams = {
        # American League East
        'BAL': {'colors': ('#DF4601', '#000000'), 'name': 'Orioles'},
        'BOS': {'colors': ('#BD3039', '#0C2340'), 'name': 'Red Sox'},
        'NYY': {'colors': ('#132448', '#C4CED4'), 'name': 'Yankees'},
        'TB': {'colors': ('#092C5C', '#8FBCE6'), 'name': 'Rays'},
        'TOR': {'colors': ('#134A8E', '#1D2D5C'), 'name': 'Blue Jays'},
        
        # American League Central  
        'CWS': {'colors': ('#27251F', '#C4CED4'), 'name': 'White Sox'},
        'CLE': {'colors': ('#E31937', '#0C2340'), 'name': 'Guardians'},
        'DET': {'colors': ('#0C2340', '#FA4616'), 'name': 'Tigers'},
        'KC': {'colors': ('#004687', '#BD9B60'), 'name': 'Royals'},
        'MIN': {'colors': ('#002B5C', '#D31145'), 'name': 'Twins'},
        
        # American League West
        'HOU': {'colors': ('#002D62', '#EB6E1F'), 'name': 'Astros'},
        'LAA': {'colors': ('#BA0021', '#C4CED4'), 'name': 'Angels'},
        'OAK': {'colors': ('#003831', '#EFB21E'), 'name': 'Athletics'},
        'SEA': {'colors': ('#0C2C56', '#005C5C'), 'name': 'Mariners'},
        'TEX': {'colors': ('#003278', '#C0111F'), 'name': 'Rangers'},
        
        # National League East
        'ATL': {'colors': ('#CE1141', '#13274F'), 'name': 'Braves'},
        'MIA': {'colors': ('#00A3E0', '#FF6600'), 'name': 'Marlins'},
        'NYM': {'colors': ('#002D72', '#FF5910'), 'name': 'Mets'},
        'PHI': {'colors': ('#E81828', '#002D72'), 'name': 'Phillies'},
        'WSH': {'colors': ('#AB0003', '#14225A'), 'name': 'Nationals'},
        
        # National League Central
        'CHC': {'colors': ('#0E3386', '#CC3433'), 'name': 'Cubs'},
        'CIN': {'colors': ('#C6011F', '#000000'), 'name': 'Reds'},
        'MIL': {'colors': ('#12284B', '#FFC52F'), 'name': 'Brewers'},
        'PIT': {'colors': ('#FDB827', '#27251F'), 'name': 'Pirates'},
        'STL': {'colors': ('#C41E3A', '#FEDB00'), 'name': 'Cardinals'},
        
        # National League West
        'ARI': {'colors': ('#A71930', '#E3D4AD'), 'name': 'D-backs'},
        'COL': {'colors': ('#33006F', '#C4CED4'), 'name': 'Rockies'},
        'LAD': {'colors': ('#005A9C', '#EF3E42'), 'name': 'Dodgers'},
        'SD': {'colors': ('#2F241D', '#FFC425'), 'name': 'Padres'},
        'SF': {'colors': ('#FD5A1E', '#27251F'), 'name': 'Giants'},
    }
    
    os.makedirs('team_logos', exist_ok=True)
    
    print("Creating professional team logos...")
    print("=" * 50)
    
    logo_size = (100, 100)
    
    for team_code, team_data in teams.items():
        try:
            print(f"Creating {team_code} logo...", end=" ")
            
            # Create new image with transparent background
            logo = Image.new('RGBA', logo_size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(logo)
            
            # Get colors
            primary_color = team_data['colors'][0]
            secondary_color = team_data['colors'][1]
            
            # Convert hex to RGB
            def hex_to_rgb(hex_color):
                return tuple(int(hex_color[i:i+2], 16) for i in (1, 3, 5))
            
            primary_rgb = hex_to_rgb(primary_color)
            secondary_rgb = hex_to_rgb(secondary_color)
            
            # Draw circular background
            margin = 5
            circle_bounds = [margin, margin, logo_size[0] - margin, logo_size[1] - margin]
            
            # Gradient effect: outer ring in secondary color, inner circle in primary
            draw.ellipse(circle_bounds, fill=secondary_rgb + (255,), outline=primary_rgb + (255,), width=3)
            
            # Inner circle
            inner_margin = 12
            inner_bounds = [inner_margin, inner_margin, logo_size[0] - inner_margin, logo_size[1] - inner_margin]
            draw.ellipse(inner_bounds, fill=primary_rgb + (255,))
            
            # Add team abbreviation text
            try:
                # Try to use a system font, fallback to default
                font_size = 24 if len(team_code) <= 3 else 20
                try:
                    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
                except:
                    try:
                        font = ImageFont.truetype("arial.ttf", font_size)
                    except:
                        font = ImageFont.load_default()
                
                # Get text dimensions
                bbox = draw.textbbox((0, 0), team_code, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                # Center the text
                x = (logo_size[0] - text_width) // 2
                y = (logo_size[1] - text_height) // 2
                
                # Add text with contrast color
                text_color = secondary_rgb if sum(primary_rgb) < 400 else (255, 255, 255)
                draw.text((x, y), team_code, fill=text_color + (255,), font=font)
                
            except Exception as e:
                # Fallback: just draw team code without special font
                draw.text((30, 35), team_code, fill=(255, 255, 255, 255))
            
            # Save logo
            filename = f"team_logos/{team_code}.png"
            logo.save(filename, 'PNG')
            
            print("✓")
            
        except Exception as e:
            print(f"✗ (Error: {e})")
    
    print("=" * 50)
    print(f"Team logos created in: team_logos/")
    print("Logos feature team colors and abbreviations in professional circular design")

if __name__ == "__main__":
    create_team_logos()