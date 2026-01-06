import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from typing import Dict, List, Optional, Union
import logging
from pathlib import Path
import re
from urllib.parse import urljoin

class BaseScraper:
    """スクレイピングの基底クラス"""
    
    def __init__(self, config: Dict):
        """
        Args:
            config: scraping_config.yaml から読み込んだ設定
        """
        self.base_url = config.get('base_url', 'https://db.netkeiba.com')
        self.request_interval = config.get('request_interval', 1.0)
        self.timeout = config.get('timeout', 30)
        self.user_agent = config.get('user_agent', 'Mozilla/5.0')
        self.max_retries = config.get('max_retries', 3)
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        URLからページを取得
        
        機能:
        - リトライ機能（max_retries回まで）
        - エラーハンドリング（404, 500等）
        - レート制限（request_interval秒待機）
        - タイムアウト処理
        
        Returns:
            BeautifulSoup object or None (失敗時)
        """
        for attempt in range(self.max_retries + 1):
            try:
                time.sleep(self.request_interval)
                response = self.session.get(url, timeout=self.timeout)
                response.encoding = response.apparent_encoding  # 文字化け対策
                
                if response.status_code == 200:
                    return BeautifulSoup(response.text, 'lxml')
                elif response.status_code == 404:
                    self.logger.warning(f"Page not found: {url}")
                    return None
                else:
                    self.logger.warning(f"Request failed: {url}, status: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request exception: {url}, error: {e}")
            
            if attempt < self.max_retries:
                sleep_time = 2 ** attempt  # 指数バックオフ
                self.logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
        
        self.logger.error(f"Max retries reached for: {url}")
        return None
    
    def _save_to_csv(self, data: List[Dict], filepath: Path):
        """データをCSVで保存"""
        if not data:
            self.logger.warning("No data to save.")
            return
            
        df = pd.DataFrame(data)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(filepath, index=False, encoding='utf-8-sig') # Excel互換のためutf-8-sig
        self.logger.info(f"Saved {len(df)} records to {filepath}")


class RaceResultScraper(BaseScraper):
    """レース結果を取得するスクレイパー"""
    
    def scrape_race(self, race_id: str) -> Dict:
        """
        1レースの結果を取得
        """
        url = urljoin(self.base_url, f"/race/{race_id}/")
        soup = self._get_page(url)
        if not soup:
            return {}

        try:
            # --- レース基本情報 ---
            data_intro = soup.find('div', class_='data_intro')
            racedata01 = data_intro.find('dl', class_='racedata01')
            racedata02 = data_intro.find('p', class_='smalltxt')
            
            race_name = data_intro.find('h1').text.strip() if data_intro.find('h1') else ""
            race_number = 0 # TODO: Parse race number properly if needed, usually in H1 or title
            
            # 詳細情報のパース (芝2000m (右) 天候:曇 芝:良 など)
            race_details_text = racedata01.text.strip() if racedata01 else ""
            
            track_type = "芝" if "芝" in race_details_text else "ダート" if "ダ" in race_details_text else "障害"
            distance_match = re.search(r'(\d+)m', race_details_text)
            distance = int(distance_match.group(1)) if distance_match else 0
            
            weather = "晴" if "晴" in race_details_text else "曇" if "曇" in race_details_text else "雨" if "雨" in race_details_text else "小雨" if "小雨" in race_details_text else "雪" if "雪" in race_details_text else ""
            condition = "良" if "良" in race_details_text else "稍重" if "稍重" in race_details_text else "重" if "重" in race_details_text else "不良" if "不良" in race_details_text else ""

            # 日付と競馬場の取得 (2024年1月6日 1回京都2日目 3歳未勝利 など)
            meta_text = racedata02.text.strip() if racedata02 else ""
            date_match = re.search(r'(\d+)年(\d+)月(\d+)日', meta_text)
            race_date = f"{date_match.group(1)}-{date_match.group(2).zfill(2)}-{date_match.group(3).zfill(2)}" if date_match else ""
            
            track_name = ""
            for t in ["札幌", "函館", "福島", "新潟", "東京", "中山", "中京", "京都", "阪神", "小倉"]:
                if t in meta_text:
                    track_name = t
                    break
            
            # --- 出走馬データ ---
            results = []
            table = soup.find('table', class_='race_table_01')
            if table:
                rows = table.find_all('tr')[1:] # ヘッダー除外
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) < 10: continue
                    
                    try:
                        finish_position = cols[0].text.strip()
                        frame_number = cols[1].text.strip()
                        horse_number = cols[2].text.strip()
                        horse_link = cols[3].find('a')
                        horse_name = horse_link.text.strip() if horse_link else ""
                        horse_id = horse_link['href'].split('/')[-2] if horse_link else ""
                        
                        sex_age = cols[4].text.strip()
                        weight = cols[5].text.strip()
                        
                        jockey_link = cols[6].find('a')
                        jockey_name = jockey_link.text.strip() if jockey_link else ""
                        jockey_id = jockey_link['href'].split('/')[-2] if jockey_link else ""
                        
                        finish_time = cols[7].text.strip()
                        margin = cols[8].text.strip()
                        
                        # 通過順とか上がりとか取得できるが、カラム位置は可変の可能性あり注意
                        # 今回は簡易実装
                        
                        trainer_link = cols[18].find('a') if len(cols) > 18 else None
                        trainer_name = trainer_link.text.strip() if trainer_link else ""
                        trainer_id = trainer_link['href'].split('/')[-2] if trainer_link else ""

                        horse_weight = cols[14].text.strip() if len(cols) > 14 else ""
                        
                        results.append({
                            'race_id': race_id,
                            'race_date': race_date,
                            'track_name': track_name,
                            'race_name': race_name,
                            'distance': distance,
                            'track_type': track_type,
                            'track_condition': condition,
                            'weather': weather,
                            'finish_position': finish_position,
                            'frame_number': frame_number,
                            'horse_number': horse_number,
                            'horse_id': horse_id,
                            'horse_name': horse_name,
                            'sex_age': sex_age,
                            'weight': weight,
                            'jockey_id': jockey_id,
                            'jockey_name': jockey_name,
                            'finish_time': finish_time,
                            'margin': margin,
                            'trainer_id': trainer_id,
                            'trainer_name': trainer_name,
                            'horse_weight': horse_weight
                        })
                    except Exception as e:
                        self.logger.error(f"Error parsing row in race {race_id}: {e}")
                        continue
            
            return {'race_info': {
                'race_id': race_id,
                'race_date': race_date,
                'track_name': track_name,
                'race_name': race_name
            }, 'results': results}

        except Exception as e:
            self.logger.error(f"Error scraping race {race_id}: {e}")
            return {}
    
    def scrape_date_range(self, start_date: str, end_date: str, 
                          tracks: Optional[List[str]] = None) -> pd.DataFrame:
        """
        期間指定でレース結果を取得
        """
        all_results = []
        
        # 日付リスト作成
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        date_range = pd.date_range(start, end)
        
        for date in date_range:
            date_str = date.strftime('%Y%m%d')
            url = f"https://db.netkeiba.com/race/list/{date_str}/"
            
            self.logger.info(f"Scraping race list for {date_str}...")
            soup = self._get_page(url)
            if not soup:
                continue
            
            # レースIDの抽出
            # db.netkeiba.com/race/list/YYYYMMDD では、各レースへのリンクがある
            # <a href="/race/202401010101/" title="3歳未勝利">
            race_links = soup.select('dl.race_top_data a')
            race_ids = set()
            for link in race_links:
                href = link.get('href')
                if href and href.startswith('/race/'):
                    rid = href.split('/')[-2]
                    # tracksフィルタリングがあれば行う（ここではリストページから場所判定は難しいのでIDを取得後に詳細でフィルタするか、URL構造解析するか）
                    # 今回は簡易的にすべて取得してからフィルタリングするか、IDから類推する
                    # ID体系: YYYYPPBBRR (YYYY:年, PP:場所コード, BB:開催回, RR:日)
                    # 場所コード: 01:札幌, 02:函館, 03:福島, 04:新潟, 05:東京, 06:中山, 07:中京, 08:京都, 09:阪神, 10:小倉
                    
                    if tracks:
                        track_code = rid[4:6]
                        place_map = {
                            '01': '札幌', '02': '函館', '03': '福島', '04': '新潟', '05': '東京',
                            '06': '中山', '07': '中京', '08': '京都', '09': '阪神', '10': '小倉'
                        }
                        place_name = place_map.get(track_code)
                        if place_name not in tracks:
                            continue
                    
                    race_ids.add(rid)
            
            self.logger.info(f"Found {len(race_ids)} races for {date_str}")
            
            for rid in race_ids:
                self.logger.info(f"Scraping race {rid}...")
                data = self.scrape_race(rid)
                if data and 'results' in data and data['results']:
                    all_results.extend(data['results'])
                time.sleep(self.request_interval)

        return pd.DataFrame(all_results)


class HorseInfoScraper(BaseScraper):
    """馬の基本情報を取得するスクレイパー"""
    
    def scrape_horse(self, horse_id: str) -> Dict:
        # TODO: Implement basic horse info scraping
        return {}
    
    def scrape_horse_results(self, horse_id: str) -> pd.DataFrame:
        # TODO: Implement horse results scraping
        return pd.DataFrame()


class JockeyTrainerScraper(BaseScraper):
    """騎手・調教師の情報を取得するスクレイパー"""
    
    def scrape_jockey(self, jockey_id: str) -> Dict:
        # TODO: Implement jockey scraping
        return {}
    
    def scrape_trainer(self, trainer_id: str) -> Dict:
        # TODO: Implement trainer scraping
        return {}


class OddsDataScraper(BaseScraper):
    """オッズデータを取得するスクレイパー"""
    
    def scrape_odds(self, race_id: str, odds_type: str = 'win') -> Dict:
        # TODO: Implement odds scraping
        return {}
