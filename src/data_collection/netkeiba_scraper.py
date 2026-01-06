"""
netkeibaからデータを収集するスクレイパーモジュール
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from typing import Dict, List, Optional
import logging
from pathlib import Path
from datetime import datetime
import re


class BaseScraper:
    """スクレイピングの基底クラス"""
    
    def __init__(self, config: Dict):
        """
        Args:
            config: scraping_config.yaml から読み込んだ設定
        """
        self.base_url = config['base_url']
        self.request_interval = config['request_interval']
        self.timeout = config['timeout']
        self.user_agent = config['user_agent']
        self.max_retries = config['max_retries']
        self.retry_delay = config.get('error_handling', {}).get('retry_delay', 2.0)
        self.exponential_backoff = config.get('error_handling', {}).get('exponential_backoff', True)
        self.skip_on_error = config.get('error_handling', {}).get('skip_on_error', True)
        
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})
        self.logger = logging.getLogger(self.__class__.__name__)
        self.last_request_time = 0
    
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
        # レート制限
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Fetching URL: {url} (attempt {attempt + 1}/{self.max_retries})")
                
                response = self.session.get(url, timeout=self.timeout)
                self.last_request_time = time.time()
                
                if response.status_code == 200:
                    self.logger.info(f"Successfully fetched: {url}")
                    return BeautifulSoup(response.content, 'html.parser')
                elif response.status_code == 404:
                    self.logger.warning(f"Page not found (404): {url}")
                    return None
                elif response.status_code >= 500:
                    self.logger.warning(f"Server error ({response.status_code}): {url}")
                    # リトライ
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (2 ** attempt if self.exponential_backoff else 1)
                        self.logger.info(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
                        continue
                else:
                    self.logger.error(f"HTTP {response.status_code}: {url}")
                    return None
                    
            except requests.Timeout:
                self.logger.warning(f"Timeout fetching {url}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt if self.exponential_backoff else 1)
                    self.logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                    continue
                return None
            except requests.RequestException as e:
                self.logger.error(f"Request error: {e}")
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt if self.exponential_backoff else 1)
                    time.sleep(delay)
                    continue
                return None
        
        return None
    
    def _save_to_csv(self, data: List[Dict], filepath: Path):
        """データをCSVで保存"""
        df = pd.DataFrame(data)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        self.logger.info(f"Saved {len(data)} records to {filepath}")


class RaceResultScraper(BaseScraper):
    """レース結果を取得するスクレイパー"""
    
    def scrape_race(self, race_id: str) -> Dict:
        """
        1レースの結果を取得
        
        URL例: https://db.netkeiba.com/race/{race_id}/
        
        Returns:
            レースデータの辞書
        """
        url = f"{self.base_url}/race/{race_id}/"
        soup = self._get_page(url)
        
        if soup is None:
            self.logger.warning(f"Failed to fetch race {race_id}")
            return {}
        
        try:
            race_data = self._parse_race_info(soup, race_id)
            horse_results = self._parse_race_results(soup, race_id)
            
            # レース情報と各馬の結果を結合
            results = []
            for horse in horse_results:
                combined = {**race_data, **horse}
                results.append(combined)
            
            return {'race_info': race_data, 'results': results}
            
        except Exception as e:
            self.logger.error(f"Error parsing race {race_id}: {e}")
            if not self.skip_on_error:
                raise
            return {}
    
    def _parse_race_info(self, soup: BeautifulSoup, race_id: str) -> Dict:
        """レース基本情報をパース"""
        race_data = {'race_id': race_id}
        
        try:
            # レース名
            race_title = soup.find('div', class_='RaceName')
            if race_title:
                race_data['race_name'] = race_title.get_text(strip=True)
            
            # レース詳細情報（距離、馬場、天候等）
            race_data1 = soup.find('div', class_='RaceData01')
            if race_data1:
                race_info_text = race_data1.get_text()
                
                # 距離を抽出
                distance_match = re.search(r'(\d+)m', race_info_text)
                if distance_match:
                    race_data['distance'] = int(distance_match.group(1))
                
                # トラック種類（芝/ダート）
                if '芝' in race_info_text:
                    race_data['track_type'] = '芝'
                elif 'ダート' in race_info_text:
                    race_data['track_type'] = 'ダート'
                else:
                    race_data['track_type'] = '不明'
                
                # 馬場状態
                for condition in ['良', '稍重', '重', '不良']:
                    if condition in race_info_text:
                        race_data['track_condition'] = condition
                        break
                
                # 天気
                for weather in ['晴', '曇', '雨', '小雨', '雪']:
                    if weather in race_info_text:
                        race_data['weather'] = weather
                        break
            
            # レース日付
            race_data2 = soup.find('div', class_='RaceData02')
            if race_data2:
                date_text = race_data2.get_text()
                date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_text)
                if date_match:
                    year, month, day = date_match.groups()
                    race_data['race_date'] = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                
                # 競馬場名を抽出
                track_match = re.search(r'(\d+)回(.+?)(\d+)日目', date_text)
                if track_match:
                    race_data['track_name'] = track_match.group(2).strip()
                    race_data['race_number'] = int(re.search(r'(\d+)R', date_text).group(1) if re.search(r'(\d+)R', date_text) else 0)
            
            # グレード
            race_data['grade'] = self._extract_grade(soup)
            
            # 出走頭数
            result_table = soup.find('table', class_='RaceTable01')
            if result_table:
                rows = result_table.find_all('tr')
                race_data['horse_count'] = len(rows) - 1  # ヘッダー行を除く
            
        except Exception as e:
            self.logger.warning(f"Error parsing race info: {e}")
        
        return race_data
    
    def _extract_grade(self, soup: BeautifulSoup) -> str:
        """グレード情報を抽出"""
        race_name_div = soup.find('div', class_='RaceName')
        if race_name_div:
            text = race_name_div.get_text()
            for grade in ['G1', 'G2', 'G3', 'OP', 'L', 'オープン', '特別']:
                if grade in text:
                    return grade
        return '一般'
    
    def _parse_race_results(self, soup: BeautifulSoup, race_id: str) -> List[Dict]:
        """レース結果テーブルをパース"""
        results = []
        
        result_table = soup.find('table', class_='RaceTable01')
        if not result_table:
            self.logger.warning(f"Result table not found for race {race_id}")
            return results
        
        rows = result_table.find_all('tr')[1:]  # ヘッダーをスキップ
        
        for row in rows:
            try:
                cols = row.find_all('td')
                if len(cols) < 10:
                    continue
                
                horse_data = {}
                
                # 着順
                finish_pos = cols[0].get_text(strip=True)
                horse_data['finish_position'] = int(finish_pos) if finish_pos.isdigit() else 0
                
                # 枠番
                frame = cols[1].get_text(strip=True)
                horse_data['frame_number'] = int(frame) if frame.isdigit() else 0
                
                # 馬番
                horse_num = cols[2].get_text(strip=True)
                horse_data['horse_number'] = int(horse_num) if horse_num.isdigit() else 0
                
                # 馬名とID
                horse_link = cols[3].find('a')
                if horse_link:
                    horse_data['horse_name'] = horse_link.get_text(strip=True)
                    horse_url = horse_link.get('href', '')
                    horse_id_match = re.search(r'/horse/(\d+)', horse_url)
                    if horse_id_match:
                        horse_data['horse_id'] = horse_id_match.group(1)
                
                # 性齢
                sex_age = cols[4].get_text(strip=True)
                horse_data['sex_age'] = sex_age
                
                # 斤量
                weight_text = cols[5].get_text(strip=True)
                try:
                    horse_data['weight'] = float(weight_text)
                except:
                    horse_data['weight'] = 0.0
                
                # 騎手
                jockey_link = cols[6].find('a')
                if jockey_link:
                    horse_data['jockey_name'] = jockey_link.get_text(strip=True)
                    jockey_url = jockey_link.get('href', '')
                    jockey_id_match = re.search(r'/jockey/(\d+)', jockey_url)
                    if jockey_id_match:
                        horse_data['jockey_id'] = jockey_id_match.group(1)
                
                # タイム
                time_text = cols[7].get_text(strip=True)
                horse_data['finish_time'] = self._parse_time(time_text)
                
                # 着差
                margin = cols[8].get_text(strip=True)
                horse_data['margin'] = margin
                
                # 人気
                popularity = cols[9].get_text(strip=True)
                horse_data['popularity'] = int(popularity) if popularity.isdigit() else 0
                
                # オッズ
                if len(cols) > 10:
                    odds_text = cols[10].get_text(strip=True)
                    try:
                        horse_data['odds'] = float(odds_text)
                    except:
                        horse_data['odds'] = 0.0
                
                # 上がり3F
                if len(cols) > 11:
                    last_3f = cols[11].get_text(strip=True)
                    try:
                        horse_data['last_3f_time'] = float(last_3f)
                    except:
                        horse_data['last_3f_time'] = 0.0
                
                # 通過順位
                if len(cols) > 12:
                    passing = cols[12].get_text(strip=True)
                    horse_data['passing_order'] = passing
                
                # 馬体重
                if len(cols) > 13:
                    weight_info = cols[13].get_text(strip=True)
                    weight_match = re.search(r'(\d+)\(([+-]?\d+)\)', weight_info)
                    if weight_match:
                        horse_data['horse_weight'] = int(weight_match.group(1))
                        horse_data['horse_weight_diff'] = int(weight_match.group(2))
                
                # 調教師
                if len(cols) > 14:
                    trainer_link = cols[14].find('a')
                    if trainer_link:
                        horse_data['trainer_name'] = trainer_link.get_text(strip=True)
                        trainer_url = trainer_link.get('href', '')
                        trainer_id_match = re.search(r'/trainer/(\d+)', trainer_url)
                        if trainer_id_match:
                            horse_data['trainer_id'] = trainer_id_match.group(1)
                
                results.append(horse_data)
                
            except Exception as e:
                self.logger.warning(f"Error parsing row: {e}")
                continue
        
        return results
    
    def _parse_time(self, time_str: str) -> float:
        """タイム文字列を秒に変換"""
        try:
            if ':' in time_str:
                parts = time_str.split(':')
                minutes = int(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(time_str)
        except:
            return 0.0
    
    def scrape_date_range(self, start_date: str, end_date: str, 
                          tracks: Optional[List[str]] = None) -> pd.DataFrame:
        """
        期間指定でレース結果を取得
        
        Args:
            start_date: 開始日 (YYYY-MM-DD)
            end_date: 終了日 (YYYY-MM-DD)
            tracks: 対象競馬場のリスト（Noneの場合は全競馬場）
        
        Returns:
            全レースのDataFrame
        """
        self.logger.info(f"Scraping races from {start_date} to {end_date}")
        
        # カレンダーから開催日とレースIDを取得
        race_ids = self._get_race_ids_in_range(start_date, end_date, tracks)
        
        all_results = []
        for i, race_id in enumerate(race_ids):
            self.logger.info(f"Processing race {i+1}/{len(race_ids)}: {race_id}")
            
            race_data = self.scrape_race(race_id)
            if race_data and 'results' in race_data:
                all_results.extend(race_data['results'])
        
        if not all_results:
            self.logger.warning("No race results found")
            return pd.DataFrame()
        
        return pd.DataFrame(all_results)
    
    def _get_race_ids_in_range(self, start_date: str, end_date: str, 
                                tracks: Optional[List[str]] = None) -> List[str]:
        """期間内のレースIDを取得"""
        # 簡易実装：実際にはカレンダーAPIやカレンダーページから取得する必要がある
        # ここではダミーデータを返す（実装時は実際のロジックに置き換える）
        self.logger.warning("Race ID fetching not fully implemented - returning sample data")
        
        # サンプルレースID（2024年1月6日の東京競馬場）
        # 実際の実装では、カレンダーページをスクレイピングしてレースIDを取得
        return ['202406010101', '202406010102']  # サンプル


class HorseInfoScraper(BaseScraper):
    """馬の基本情報を取得するスクレイパー"""
    
    def scrape_horse(self, horse_id: str) -> Dict:
        """
        1頭の馬の情報を取得
        
        URL例: https://db.netkeiba.com/horse/{horse_id}/
        
        Returns:
            馬情報の辞書
        """
        url = f"{self.base_url}/horse/{horse_id}/"
        soup = self._get_page(url)
        
        if soup is None:
            self.logger.warning(f"Failed to fetch horse {horse_id}")
            return {}
        
        try:
            horse_data = {'horse_id': horse_id}
            
            # 馬名
            horse_title = soup.find('div', class_='horse_title')
            if horse_title:
                h1 = horse_title.find('h1')
                if h1:
                    horse_data['horse_name'] = h1.get_text(strip=True)
            
            # 基本情報テーブル
            profile_table = soup.find('table', class_='db_prof_table')
            if profile_table:
                rows = profile_table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    if th and td:
                        label = th.get_text(strip=True)
                        value = td.get_text(strip=True)
                        
                        if '生年月日' in label:
                            horse_data['birth_date'] = value
                        elif '性別' in label or '性齢' in label:
                            horse_data['sex'] = value
                        elif '毛色' in label:
                            horse_data['coat_color'] = value
                        elif '生産者' in label:
                            horse_data['breeder'] = value
                        elif '馬主' in label:
                            horse_data['owner'] = value
                        elif '調教師' in label:
                            trainer_link = td.find('a')
                            if trainer_link:
                                horse_data['trainer_name'] = trainer_link.get_text(strip=True)
                                trainer_url = trainer_link.get('href', '')
                                trainer_id_match = re.search(r'/trainer/(\d+)', trainer_url)
                                if trainer_id_match:
                                    horse_data['trainer_id'] = trainer_id_match.group(1)
            
            # 血統情報
            pedigree_table = soup.find('table', class_='blood_table')
            if pedigree_table:
                # 父
                sire_link = pedigree_table.find('a', href=re.compile(r'/horse/\w+'))
                if sire_link:
                    horse_data['sire_name'] = sire_link.get_text(strip=True)
                    sire_url = sire_link.get('href', '')
                    sire_id_match = re.search(r'/horse/(\w+)', sire_url)
                    if sire_id_match:
                        horse_data['sire_id'] = sire_id_match.group(1)
            
            # 戦績サマリー
            race_results = self.scrape_horse_results(horse_id)
            if not race_results.empty:
                horse_data['total_races'] = len(race_results)
                horse_data['total_wins'] = len(race_results[race_results['finish_position'] == 1])
                horse_data['total_places'] = len(race_results[race_results['finish_position'] <= 2])
                horse_data['total_shows'] = len(race_results[race_results['finish_position'] <= 3])
            
            return horse_data
            
        except Exception as e:
            self.logger.error(f"Error parsing horse {horse_id}: {e}")
            if not self.skip_on_error:
                raise
            return {}
    
    def scrape_horse_results(self, horse_id: str) -> pd.DataFrame:
        """
        馬の全レース成績を取得
        
        Returns:
            馬の出走履歴DataFrame
        """
        url = f"{self.base_url}/horse/{horse_id}/"
        soup = self._get_page(url)
        
        if soup is None:
            return pd.DataFrame()
        
        try:
            results = []
            result_table = soup.find('table', class_='db_h_race_results')
            if result_table:
                rows = result_table.find_all('tr')[1:]  # ヘッダーをスキップ
                
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) < 5:
                        continue
                    
                    result = {}
                    
                    # 日付
                    if cols[0]:
                        result['race_date'] = cols[0].get_text(strip=True)
                    
                    # 競馬場
                    if cols[1]:
                        result['track_name'] = cols[1].get_text(strip=True)
                    
                    # レース名
                    if len(cols) > 4:
                        race_link = cols[4].find('a')
                        if race_link:
                            result['race_name'] = race_link.get_text(strip=True)
                    
                    # 着順
                    if len(cols) > 11:
                        finish = cols[11].get_text(strip=True)
                        result['finish_position'] = int(finish) if finish.isdigit() else 0
                    
                    results.append(result)
            
            return pd.DataFrame(results)
            
        except Exception as e:
            self.logger.error(f"Error parsing horse results: {e}")
            return pd.DataFrame()


class JockeyTrainerScraper(BaseScraper):
    """騎手・調教師の情報を取得するスクレイパー"""
    
    def scrape_jockey(self, jockey_id: str) -> Dict:
        """
        騎手の基本情報を取得
        
        URL例: https://db.netkeiba.com/jockey/{jockey_id}/
        
        Returns:
            騎手情報の辞書
        """
        url = f"{self.base_url}/jockey/{jockey_id}/"
        soup = self._get_page(url)
        
        if soup is None:
            self.logger.warning(f"Failed to fetch jockey {jockey_id}")
            return {}
        
        try:
            jockey_data = {'jockey_id': jockey_id}
            
            # 騎手名
            title = soup.find('div', class_='db_head')
            if title:
                h1 = title.find('h1')
                if h1:
                    jockey_data['jockey_name'] = h1.get_text(strip=True)
            
            # 基本情報
            profile_table = soup.find('table', class_='db_prof_table')
            if profile_table:
                rows = profile_table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    if th and td:
                        label = th.get_text(strip=True)
                        value = td.get_text(strip=True)
                        
                        if '生年月日' in label:
                            jockey_data['birth_date'] = value
                        elif '初騎乗' in label:
                            jockey_data['debut_date'] = value
                        elif '所属' in label:
                            jockey_data['affiliation'] = value
            
            # 通算成績
            stats_table = soup.find('table', class_='db_h_race_results')
            if stats_table:
                # 簡易実装：実際には統計情報をパース
                jockey_data['total_races'] = 0
                jockey_data['total_wins'] = 0
                jockey_data['win_rate'] = 0.0
                jockey_data['place_rate'] = 0.0
                jockey_data['show_rate'] = 0.0
            
            return jockey_data
            
        except Exception as e:
            self.logger.error(f"Error parsing jockey {jockey_id}: {e}")
            if not self.skip_on_error:
                raise
            return {}
    
    def scrape_trainer(self, trainer_id: str) -> Dict:
        """
        調教師の基本情報を取得
        
        URL例: https://db.netkeiba.com/trainer/{trainer_id}/
        
        Returns:
            調教師情報の辞書
        """
        url = f"{self.base_url}/trainer/{trainer_id}/"
        soup = self._get_page(url)
        
        if soup is None:
            self.logger.warning(f"Failed to fetch trainer {trainer_id}")
            return {}
        
        try:
            trainer_data = {'trainer_id': trainer_id}
            
            # 調教師名
            title = soup.find('div', class_='db_head')
            if title:
                h1 = title.find('h1')
                if h1:
                    trainer_data['trainer_name'] = h1.get_text(strip=True)
            
            # 基本情報
            profile_table = soup.find('table', class_='db_prof_table')
            if profile_table:
                rows = profile_table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    if th and td:
                        label = th.get_text(strip=True)
                        value = td.get_text(strip=True)
                        
                        if '生年月日' in label:
                            trainer_data['birth_date'] = value
                        elif '所属' in label:
                            trainer_data['affiliation'] = value
                        elif '厩舎' in label:
                            trainer_data['stable_name'] = value
            
            # 通算成績
            trainer_data['total_races'] = 0
            trainer_data['total_wins'] = 0
            trainer_data['win_rate'] = 0.0
            
            return trainer_data
            
        except Exception as e:
            self.logger.error(f"Error parsing trainer {trainer_id}: {e}")
            if not self.skip_on_error:
                raise
            return {}


class OddsDataScraper(BaseScraper):
    """オッズデータを取得するスクレイパー"""
    
    def scrape_odds(self, race_id: str, odds_type: str = 'win') -> Dict:
        """
        オッズデータを取得
        
        Args:
            race_id: レースID
            odds_type: オッズ種類（win, place, quinella, exacta, trio, trifecta等）
        
        Returns:
            オッズデータの辞書
        """
        # オッズタイプに応じたURL
        odds_url_map = {
            'win': f"{self.base_url}/race/{race_id}/",
            'place': f"{self.base_url}/odds/p/{race_id}/",
            'quinella': f"{self.base_url}/odds/q/{race_id}/",
            'exacta': f"{self.base_url}/odds/e/{race_id}/",
            'wide': f"{self.base_url}/odds/w/{race_id}/",
            'trio': f"{self.base_url}/odds/t/{race_id}/",
            'trifecta': f"{self.base_url}/odds/3t/{race_id}/",
        }
        
        url = odds_url_map.get(odds_type, odds_url_map['win'])
        soup = self._get_page(url)
        
        if soup is None:
            self.logger.warning(f"Failed to fetch odds for race {race_id}")
            return {}
        
        try:
            odds_data = {
                'race_id': race_id,
                'odds_type': odds_type,
                'odds': []
            }
            
            if odds_type == 'win':
                # 単勝オッズ
                odds_data['odds'] = self._parse_win_odds(soup)
            elif odds_type == 'place':
                # 複勝オッズ
                odds_data['odds'] = self._parse_place_odds(soup)
            else:
                # その他のオッズ（簡易実装）
                odds_data['odds'] = []
            
            return odds_data
            
        except Exception as e:
            self.logger.error(f"Error parsing odds: {e}")
            if not self.skip_on_error:
                raise
            return {}
    
    def _parse_win_odds(self, soup: BeautifulSoup) -> List[Dict]:
        """単勝オッズをパース"""
        odds_list = []
        
        # レース結果テーブルからオッズを抽出
        result_table = soup.find('table', class_='RaceTable01')
        if result_table:
            rows = result_table.find_all('tr')[1:]
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) > 10:
                    try:
                        horse_num = cols[2].get_text(strip=True)
                        odds_text = cols[10].get_text(strip=True)
                        
                        odds_list.append({
                            'horse_number': int(horse_num) if horse_num.isdigit() else 0,
                            'odds': float(odds_text) if odds_text else 0.0
                        })
                    except:
                        continue
        
        return odds_list
    
    def _parse_place_odds(self, soup: BeautifulSoup) -> List[Dict]:
        """複勝オッズをパース"""
        odds_list = []
        
        # 複勝オッズテーブル（実装はサイト構造に依存）
        # 簡易実装
        return odds_list
