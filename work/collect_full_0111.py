import pandas as pd
import numpy as np
import sys
import yaml
import json
import time
from pathlib import Path
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, str(Path.cwd()))

from src.data_collection.netkeiba_scraper import LiveRaceScraper, HorseInfoScraper, RaceResultScraper

def calculate_horse_features(history_df):
    """
    馬の過去成績DataFrameから特徴量を算出
    """
    if history_df.empty:
        return {
            'recent_3_avg_speed': 0.0,
            'last_race_position': 0,
            'recent_form_score': 0.0
        }
    
    # 日付でソート（念のため）
    history_df['race_date'] = pd.to_datetime(history_df['race_date'], errors='coerce')
    history_df = history_df.dropna(subset=['race_date']).sort_values('race_date', ascending=False)
    
    # タイムを秒に変換
    temp_scraper = RaceResultScraper({})
    def parse_t(t_str):
        return temp_scraper._parse_time(t_str)
    
    history_df['finish_time'] = history_df['finish_time_str'].apply(parse_t)
    
    # 速度 (m/s)
    history_df['speed'] = history_df.apply(
        lambda x: x['distance'] / x['finish_time'] if x['finish_time'] > 0 else 0, axis=1
    )
    
    recent_races = history_df.head(5) # 直近5走
    
    # 特徴量算出
    # 1. 直近3走平均速度
    recent_3 = history_df.head(3)
    avg_speed = recent_3['speed'].replace(0, np.nan).mean()
    if np.isnan(avg_speed): avg_speed = 0.0
    
    # 2. 前走着順
    last_pos = history_df.iloc[0]['finish_position'] if len(history_df) > 0 else 0
    
    # 3. 近走スコア (着順が良いほど高スコア)
    # 1位->1.0, 2位->0.5, 3位->0.33... の重み付き平均
    def pos_to_score(p):
        if p <= 0: return 0
        return 1.0 / p
    
    recent_races['score'] = recent_races['finish_position'].apply(pos_to_score)
    form_score = recent_races['score'].mean() * 10 # 0-10スケール
    
    return {
        'recent_3_avg_speed': round(avg_speed, 3),
        'last_race_position': int(last_pos),
        'recent_form_score': round(form_score, 2)
    }

def collect_full():
    with open('config/scraping_config.yaml') as f:
        config = yaml.safe_load(f)
    
    nar_scraper = LiveRaceScraper(config)
    
    # JRA用の設定（ベースURLを一時的に変更）
    jra_config = config.copy()
    jra_config['live_base_url'] = 'https://race.netkeiba.com'
    jra_scraper = LiveRaceScraper(jra_config)
    
    horse_scraper = HorseInfoScraper(config)
    
    # 2026/01/11 レースID
    race_ids = {
        'JRA_Nakayama': [f"2026060104{str(i).zfill(2)}" for i in range(1, 13)],
        'JRA_Kyoto': [f"2026080104{str(i).zfill(2)}" for i in range(1, 13)],
        'NAR_Kochi': [f"2026540111{str(i).zfill(2)}" for i in range(1, 12)],
        'NAR_Saga': [f"2026550111{str(i).zfill(2)}" for i in range(1, 11)]
    }
    
    all_shutuba = []
    horse_cache = {} # horse_id -> features
    
    for category, ids in race_ids.items():
        scraper = jra_scraper if 'JRA' in category else nar_scraper
        print(f"\n--- Processing {category} ---")
        
        for rid in ids:
            print(f"Collecting entry for {rid}...")
            df_shutuba = scraper.scrape_shutuba(rid)
            if df_shutuba.empty:
                print(f"  Empty shutuba for {rid}")
                continue
            
            # 馬ごとの特徴量補完
            for idx, row in df_shutuba.iterrows():
                hid = row['horse_id']
                if not hid: continue
                
                if hid not in horse_cache:
                    print(f"  Fetching history for Horse {hid} ({row['horse_name']})...")
                    history = horse_scraper.scrape_horse_results(hid)
                    features = calculate_horse_features(history)
                    horse_cache[hid] = features
                    time.sleep(1.0) # アクセス制限回避
                
                # 特徴量を結合
                feats = horse_cache[hid]
                df_shutuba.at[idx, 'recent_3_avg_speed'] = feats['recent_3_avg_speed']
                df_shutuba.at[idx, 'last_race_position'] = feats['last_race_position']
                df_shutuba.at[idx, 'recent_form_score'] = feats['recent_form_score']
            
            all_shutuba.append(df_shutuba)
            time.sleep(2.0) # レースごとの間隔

    if all_shutuba:
        final_df = pd.concat(all_shutuba, ignore_index=True)
        final_df['race_date'] = '2026-01-11'
        
        # Parse odds to numeric
        final_df['odds'] = pd.to_numeric(final_df['odds_win'], errors='coerce').fillna(10.0)
        
        output_path = Path('data/live_20260111.csv')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\nSUCCESS: Saved {len(final_df)} records to {output_path}")
        print(f"Total unique horses analyzed: {len(horse_cache)}")
    else:
        print("No data collected.")

if __name__ == '__main__':
    collect_full()
