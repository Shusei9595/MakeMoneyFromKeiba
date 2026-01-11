import pandas as pd
import sys
import yaml
import json
from pathlib import Path
from datetime import datetime
import logging

# Add project root to sys.path
sys.path.insert(0, str(Path.cwd()))

from src.data_collection.netkeiba_scraper import LiveRaceScraper

def collect_108():
    with open('config/scraping_config.yaml') as f:
        config = yaml.safe_load(f)
    
    scraper = LiveRaceScraper(config)
    
    race_ids = [
        "202642010801", "202642010802", "202642010803", "202642010804", "202642010805", "202642010806", 
        "202642010807", "202642010808", "202642010809", "202642010810", "202642010811", "202642010812",
        "202647010801", "202647010802", "202647010803", "202647010804", "202647010805", "202647010806", 
        "202647010807", "202647010808", "202647010809", "202647010810",
        "202650010801", "202650010802", "202650010803", "202650010804", "202650010805", "202650010806", 
        "202650010807", "202650010808", "202650010809", "202650010810", "202650010811", "202650010812",
        "202665010801", "202665010802", "202665010803", "202665010804", "202665010805", "202665010806", 
        "202665010807", "202665010808", "202665010809", "202665010810", "202665010811", "202665010812"
    ]
    
    all_data = []
    
    for rid in race_ids:
        print(f"Collecting {rid}...")
        df_shutuba = scraper.scrape_shutuba(rid)
        if not df_shutuba.empty:
            print(f"  Shutuba found: {len(df_shutuba)} horses")
            df_results = scraper.scrape_results(rid)
            if not df_results.empty:
                print(f"  Results found: {len(df_results)} horses")
                df_merged = pd.merge(
                    df_shutuba, 
                    df_results[['horse_number', 'finish_position']], 
                    on='horse_number', 
                    how='left'
                )
                df_merged['odds'] = pd.to_numeric(df_merged['odds_win'], errors='coerce')
                all_data.append(df_merged)
            else:
                print("  Results not found, using shutuba only")
                all_data.append(df_shutuba)
        else:
            print("  Shutuba NOT found")
                
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        final_df['race_date'] = '2026-01-08'
        # Basic feature mocks for prediction
        final_df['recent_3_avg_speed'] = 38.0
        final_df['last_race_position'] = 4
        final_df['recent_form_score'] = 7.0
        
        output_path = Path('data/live_20260108.csv')
        final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"Saved to {output_path}")

if __name__ == '__main__':
    collect_108()
