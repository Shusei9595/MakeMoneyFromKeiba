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
        output_path = Path('data/results_20260108.json')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, ensure_ascii=False, indent=2)
        print(f"All results saved to {output_path}")

if __name__ == '__main__':
    collect_results()
