import pandas as pd
import sys
import yaml
import json
from pathlib import Path
import logging

# Add project root to sys.path
sys.path.insert(0, str(Path.cwd()))

from src.data_collection.netkeiba_scraper import LiveRaceScraper

def collect_results():
    with open('config/scraping_config.yaml') as f:
        config = yaml.safe_load(f)
    
    scraper = LiveRaceScraper(config)
    
    # Urawa: 01-12R (2026420109xx)
    # Kasamatsu: 01-11R (2026470109xx)
    race_ids = [
        f"2026420109{str(i).zfill(2)}" for i in range(1, 13)
    ] + [
        f"2026470109{str(i).zfill(2)}" for i in range(1, 12)
    ]
    
    results_data = {}
    
    for rid in race_ids:
        print(f"Collecting results for {rid}...")
        df_res = scraper.scrape_results(rid)
        payouts = scraper.scrape_payouts(rid)
        
        if not df_res.empty:
            results_data[rid] = {
                'finish_positions': df_res.to_dict(orient='records'),
                'payouts': payouts
            }
            print(f"  Successfully collected results and payouts.")
        else:
            print(f"  FAILED to collect results for {rid}")
            
    if results_data:
        output_path = Path('data/results_20260109.json')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        print(f"All results saved to {output_path}")

if __name__ == '__main__':
    collect_results()
