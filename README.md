# MLB Player Performance Visualization System

A comprehensive baseball analytics system that maintains a 45-day rolling window of MLB data and generates stunning player-specific visualizations.

## Features

- **Automated Data Collection**: Daily updates via GitHub Actions (FREE!)
- **45-Day Rolling Window**: Maintains recent performance data in SQLite database
- **Player-Specific Dashboards**: Generate comprehensive visualizations for any MLB player
- **Multiple Visualization Types**:
  - Exit velocity vs launch angle scatter plots
  - Spray charts
  - Pitch velocity distributions
  - Strike zone heat maps
  - Rolling averages and trends
  - Performance by count/situation
  - And much more!

## Quick Start

### Generate a Player Visualization

```bash
# Interactive mode
python generate_player_viz.py

# Or specify a player directly
python generate_player_viz.py Shohei Ohtani
```

This will create an HTML file with an interactive dashboard that you can open in your browser.

### Initialize Database (First Time Setup)

```bash
python database_manager.py
```

This will download the last 45 days of MLB data. It takes about 5-10 minutes.

## Automated Daily Updates (GitHub Actions)

The system includes a GitHub Actions workflow that:
1. Runs every day at 6 AM UTC
2. Fetches yesterday's MLB data
3. Removes data older than 45 days
4. Generates sample dashboards for star players
5. Commits changes back to the repository

**This is completely FREE with GitHub!** (2000 minutes/month for free accounts)

To enable:
1. Push this code to a GitHub repository
2. Go to Settings → Actions → General
3. Enable "Read and write permissions" for workflows
4. The workflow will run automatically or you can trigger it manually

## File Structure

```
comprehensive_visualization/
├── database_manager.py       # Database operations and schema
├── player_visualizer.py      # Player-specific visualization generator
├── daily_update.py          # Daily update script (runs via GitHub Actions)
├── generate_player_viz.py   # Simple interface for generating visualizations
├── mlb_data.db             # SQLite database (created after initialization)
├── requirements.txt         # Python dependencies
└── .github/
    └── workflows/
        └── daily_update.yml # GitHub Actions workflow
```

## Visualization Examples

### Hitter Dashboard
- Exit velocity vs launch angle with barrel zone
- 10-game rolling averages
- Spray charts with hit types
- Performance by pitch type
- Count-specific performance
- Hot/cold zones
- Trends over time

### Pitcher Dashboard  
- Velocity distributions by pitch type
- Movement profiles
- Release point consistency
- Pitch usage percentages
- Velocity trends
- Spin rate analysis
- Strike zone heat maps
- Whiff rates by pitch

## Database Schema

The SQLite database maintains:
- Daily hitting statistics
- Daily pitching statistics
- Statcast pitch-by-pitch data
- Data update logs

All data is indexed for fast player lookups.

## Requirements

- Python 3.8+
- See `requirements.txt` for package dependencies

## Manual Daily Update

If you prefer to run updates manually instead of using GitHub Actions:

```bash
python daily_update.py
```

## Tips

1. **Player Names**: Use full names as they appear on MLB rosters (e.g., "Shohei Ohtani", not "Ohtani")
2. **Data Availability**: The system maintains 45 days of data. Players need recent activity to appear.
3. **Two-Way Players**: The system automatically detects if a player is both a hitter and pitcher.
4. **Performance**: Initial database setup takes 5-10 minutes. Daily updates take about 1 minute.

## LinkedIn Integration

The system can generate LinkedIn-ready content highlighting top performers. Check the `linkedin_post.txt` file after running daily updates.

## Troubleshooting

- **No data for player**: Check spelling, ensure player has been active in last 45 days
- **Database errors**: Delete `mlb_data.db` and re-run `python database_manager.py`
- **GitHub Actions failing**: Check you have write permissions enabled in repository settings

## License

MIT