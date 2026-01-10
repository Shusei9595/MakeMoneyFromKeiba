import yaml
import sys
import re
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path.cwd()))

from src.data_collection.netkeiba_scraper import LiveRaceScraper

def debug_jra_parsing():
    with open('config/scraping_config.yaml') as f:
        config = yaml.safe_load(f)
    
    config['live_base_url'] = 'https://race.netkeiba.com'
    scraper = LiveRaceScraper(config)
    
    rid = '202606010401'
    url = f"https://race.netkeiba.com/race/shutuba.html?race_id={rid}"
    soup = scraper._get_page(url)
    
    if not soup: return
    
    rows = soup.find_all('tr', class_='HorseList')
    print(f"Found {len(rows)} rows.")
    for i, row in enumerate(rows[:2]):
        cols = row.find_all('td')
        print(f"Row {i} cols: {len(cols)}")
        if len(cols) >= 10:
            hid_link = cols[3].find('a')
            hid = scraper._extract_id(hid_link['href']) if hid_link else "MISSING"
            print(f"  Horse: {cols[3].get_text(strip=True)}")
            print(f"  ID: {hid}")
            
if __name__ == '__main__':
    debug_jra_parsing()
