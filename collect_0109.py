import pandas as pd
import sys
import yaml
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path.cwd()))

from src.data_collection.netkeiba_scraper import LiveRaceScraper

def collect_0109():
    with open('config/scraping_config.yaml') as f:
        config = yaml.safe_load(f)
    
    scraper = LiveRaceScraper(config)
    
    # Racetracks and Race IDs for 2026/01/09
    # Urawa (浦和): 01-12R
    # Kasamatsu (笠松): 01-11R
    race_ids = [
        f"2026420109{str(i).zfill(2)}" for i in range(1, 13)
    ] + [
        f"2026470109{str(i).zfill(2)}" for i in range(1, 12)
    ]
    
    all_data = []
    
    for rid in race_ids:
        print(f"Collecting {rid}...")
        df_shutuba = scraper.scrape_shutuba(rid)
        if not df_shutuba.empty:
            print(f"  Shutuba found: {len(df_shutuba)} horses")
            # For live data (forward test), results are not yet available
            # Just collect shutuba and prepare for prediction
            all_data.append(df_shutuba)
        else:
            print(f"  Shutuba NOT found for {rid}")
                
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df['race_date'] = '2026-01-09'
        
        # Parse odds to numeric
        final_df['odds'] = pd.to_numeric(final_df['odds_win'], errors='coerce')
        
        # Basic feature mocks for prediction (as real historical features are not ready)
        final_df['recent_3_avg_speed'] = 38.0
        final_df['last_race_position'] = 4
        final_df['recent_form_score'] = 7.0
        
        output_path = Path('data/live_20260109.csv')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"Saved {len(final_df)} records to {output_path}")

if __name__ == '__main__':
    collect_0109()
