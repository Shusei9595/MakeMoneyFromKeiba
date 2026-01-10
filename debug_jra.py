import yaml
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path.cwd()))

from src.data_collection.netkeiba_scraper import LiveRaceScraper

def debug_jra():
    with open('config/scraping_config.yaml') as f:
        config = yaml.safe_load(f)
    
    config['live_base_url'] = 'https://race.netkeiba.com'
    scraper = LiveRaceScraper(config)
    
    rid = '202606010411' # フェアリーS?
    print(f"Debugging JRA race {rid}...")
    
    url = f"https://race.netkeiba.com/race/shutuba.html?race_id={rid}"
    soup = scraper._get_page(url)
    
    if soup:
        print(f"Title: {soup.title.string}")
        rows = soup.find_all('tr', class_='HorseList')
        print(f"Found {len(rows)} HorseList rows.")
        
        if not rows:
            print("Trying fallback table search...")
            table = soup.find('table', class_='Shutuba_Table')
            if table:
                print("Found Shutuba_Table.")
                rows = table.find_all('tr')
                print(f"Total rows in table: {len(rows)}")
                if len(rows) > 0:
                    print(f"First row HTML: {rows[0].get_text(strip=True)[:100]}")
            else:
                print("Shutuba_Table NOT found.")
                # Print some part of the body to see what's there
                print(f"Body snippet: {soup.body.get_text(strip=True)[:500]}")
    else:
        print("Failed to fetch page.")

if __name__ == '__main__':
    debug_jra()
