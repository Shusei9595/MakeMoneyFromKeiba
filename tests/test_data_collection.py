"""
データ収集システムのテストコード
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
from pathlib import Path
import sys

# モジュールのインポートパスを追加
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data_collection.netkeiba_scraper import (
    BaseScraper,
    RaceResultScraper,
    HorseInfoScraper,
    JockeyTrainerScraper,
    OddsDataScraper
)
from data_collection.data_validator import DataValidator


@pytest.fixture
def mock_config():
    """テスト用の設定"""
    return {
        'base_url': 'https://db.netkeiba.com',
        'request_interval': 0.1,  # テストは高速化
        'timeout': 10,
        'user_agent': 'TestBot/1.0',
        'max_retries': 2,
        'error_handling': {
            'retry_delay': 0.5,
            'exponential_backoff': True,
            'skip_on_error': True
        }
    }


@pytest.fixture
def sample_race_html():
    """サンプルのレースページHTML"""
    return """
    <html>
        <body>
            <div class="RaceName">東京1R</div>
            <div class="RaceData01">芝1600m 良 晴</div>
            <div class="RaceData02">2024年1月6日 1回東京1日目 1R</div>
            <table class="RaceTable01">
                <tr>
                    <th>着順</th>
                    <th>枠番</th>
                    <th>馬番</th>
                    <th>馬名</th>
                    <th>性齢</th>
                    <th>斤量</th>
                    <th>騎手</th>
                    <th>タイム</th>
                    <th>着差</th>
                    <th>人気</th>
                    <th>単勝</th>
                </tr>
                <tr>
                    <td>1</td>
                    <td>1</td>
                    <td>1</td>
                    <td><a href="/horse/2021100001">テストホース</a></td>
                    <td>牡3</td>
                    <td>56.0</td>
                    <td><a href="/jockey/01234">テスト騎手</a></td>
                    <td>1:35.2</td>
                    <td>0.0</td>
                    <td>1</td>
                    <td>2.5</td>
                </tr>
            </table>
        </body>
    </html>
    """


@pytest.fixture
def sample_horse_html():
    """サンプルの馬ページHTML"""
    return """
    <html>
        <body>
            <div class="horse_title">
                <h1>テストホース</h1>
            </div>
            <table class="db_prof_table">
                <tr>
                    <th>生年月日</th>
                    <td>2021年4月1日</td>
                </tr>
                <tr>
                    <th>性別</th>
                    <td>牡</td>
                </tr>
                <tr>
                    <th>毛色</th>
                    <td>鹿毛</td>
                </tr>
            </table>
            <table class="blood_table">
                <tr>
                    <td><a href="/horse/2018100001">テスト父</a></td>
                </tr>
            </table>
        </body>
    </html>
    """


class TestBaseScraper:
    """BaseScraperのテスト"""
    
    def test_init(self, mock_config):
        """初期化のテスト"""
        scraper = BaseScraper(mock_config)
        assert scraper.base_url == 'https://db.netkeiba.com'
        assert scraper.request_interval == 0.1
        assert scraper.timeout == 10
        assert scraper.max_retries == 2
    
    @patch('requests.Session.get')
    def test_get_page_success(self, mock_get, mock_config, sample_race_html):
        """ページ取得成功のテスト"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = sample_race_html.encode('utf-8')
        mock_get.return_value = mock_response
        
        scraper = BaseScraper(mock_config)
        soup = scraper._get_page('https://db.netkeiba.com/race/202401010101/')
        
        assert soup is not None
        assert mock_get.called
    
    @patch('requests.Session.get')
    def test_get_page_404(self, mock_get, mock_config):
        """404エラーのテスト"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        scraper = BaseScraper(mock_config)
        soup = scraper._get_page('https://db.netkeiba.com/race/invalid/')
        
        assert soup is None
    
    @patch('requests.Session.get')
    def test_get_page_timeout(self, mock_get, mock_config):
        """タイムアウトのテスト"""
        import requests
        mock_get.side_effect = requests.Timeout("Timeout")
        
        scraper = BaseScraper(mock_config)
        soup = scraper._get_page('https://db.netkeiba.com/race/timeout/')
        
        assert soup is None
        assert mock_get.call_count == mock_config['max_retries']
    
    @patch('requests.Session.get')
    def test_get_page_retry_with_backoff(self, mock_get, mock_config):
        """リトライとエクスポネンシャルバックオフのテスト"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        scraper = BaseScraper(mock_config)
        soup = scraper._get_page('https://db.netkeiba.com/race/error/')
        
        assert soup is None
        assert mock_get.call_count == mock_config['max_retries']


class TestRaceResultScraper:
    """RaceResultScraperのテスト"""
    
    def test_init(self, mock_config):
        """初期化のテスト"""
        scraper = RaceResultScraper(mock_config)
        assert isinstance(scraper, BaseScraper)
    
    @patch.object(RaceResultScraper, '_get_page')
    def test_scrape_race_success(self, mock_get_page, mock_config, sample_race_html):
        """レース情報取得成功のテスト"""
        from bs4 import BeautifulSoup
        mock_get_page.return_value = BeautifulSoup(sample_race_html, 'html.parser')
        
        scraper = RaceResultScraper(mock_config)
        result = scraper.scrape_race('202401010101')
        
        assert 'race_info' in result
        assert 'results' in result
        assert result['race_info']['race_id'] == '202401010101'
    
    @patch.object(RaceResultScraper, '_get_page')
    def test_scrape_race_not_found(self, mock_get_page, mock_config):
        """レースが見つからない場合のテスト"""
        mock_get_page.return_value = None
        
        scraper = RaceResultScraper(mock_config)
        result = scraper.scrape_race('invalid_id')
        
        assert result == {}
    
    def test_parse_time(self, mock_config):
        """タイムパース機能のテスト"""
        scraper = RaceResultScraper(mock_config)
        
        # 分:秒形式
        assert scraper._parse_time('1:35.2') == 95.2
        
        # 秒のみ
        assert scraper._parse_time('35.2') == 35.2
        
        # 無効な値
        assert scraper._parse_time('invalid') == 0.0
    
    @patch.object(RaceResultScraper, '_get_race_ids_in_range')
    @patch.object(RaceResultScraper, 'scrape_race')
    def test_scrape_date_range(self, mock_scrape_race, mock_get_ids, mock_config):
        """期間指定収集のテスト"""
        mock_get_ids.return_value = ['202401010101', '202401010102']
        mock_scrape_race.return_value = {
            'race_info': {'race_id': '202401010101'},
            'results': [
                {'race_id': '202401010101', 'horse_name': 'テストホース1'},
                {'race_id': '202401010101', 'horse_name': 'テストホース2'}
            ]
        }
        
        scraper = RaceResultScraper(mock_config)
        df = scraper.scrape_date_range('2024-01-01', '2024-01-01')
        
        assert not df.empty
        assert len(df) > 0
    
    @patch('requests.Session.get')
    def test_get_race_ids_in_range(self, mock_get, mock_config):
        """レースID取得機能のテスト"""
        # 開催一覧ページのモックHTML
        html = """
        <html>
            <div class="race_top_data_info">
                <dl>
                    <dd><a href="/race/202401010101/" title="レース1">レース1</a></dd>
                    <dd><a href="/race/202401010102/" title="レース2">レース2</a></dd>
                </dl>
            </div>
        </html>
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = html.encode('utf-8')
        mock_get.return_value = mock_response
        
        scraper = RaceResultScraper(mock_config)
        ids = scraper._get_race_ids_in_range('2024-01-01', '2024-01-01')
        
        assert len(ids) == 2
        assert '202401010101' in ids
        assert '202401010102' in ids

    def test_parse_dividends(self, mock_config):
        """払い戻し情報のパーステスト"""
        html = """
        <table class="pay_table_01">
            <tr>
                <th>単勝</th>
                <td>1</td>
                <td>250</td>
            </tr>
            <tr>
                <th>複勝</th>
                <td>1<br>2</td>
                <td>110<br>150</td>
            </tr>
        </table>
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        
        scraper = RaceResultScraper(mock_config)
        dividends = scraper._parse_dividends(soup, 'dummy_id')
        
        assert 'win' in dividends
        assert dividends['win']['payouts'] == [250]
        assert dividends['win']['combinations'] == ['1']
        
        assert 'place' in dividends
        assert dividends['place']['payouts'] == [110, 150]
        assert set(dividends['place']['combinations']) == {'1', '2'}


class TestHorseInfoScraper:
    """HorseInfoScraperのテスト"""
    
    def test_init(self, mock_config):
        """初期化のテスト"""
        scraper = HorseInfoScraper(mock_config)
        assert isinstance(scraper, BaseScraper)
    
    @patch.object(HorseInfoScraper, '_get_page')
    @patch.object(HorseInfoScraper, 'scrape_horse_results')
    def test_scrape_horse_success(self, mock_results, mock_get_page, mock_config, sample_horse_html):
        """馬情報取得成功のテスト"""
        from bs4 import BeautifulSoup
        mock_get_page.return_value = BeautifulSoup(sample_horse_html, 'html.parser')
        mock_results.return_value = pd.DataFrame()
        
        scraper = HorseInfoScraper(mock_config)
        result = scraper.scrape_horse('2021100001')
        
        assert result['horse_id'] == '2021100001'
        assert 'horse_name' in result


class TestJockeyTrainerScraper:
    """JockeyTrainerScraperのテスト"""
    
    def test_init(self, mock_config):
        """初期化のテスト"""
        scraper = JockeyTrainerScraper(mock_config)
        assert isinstance(scraper, BaseScraper)
    
    @patch.object(JockeyTrainerScraper, '_get_page')
    def test_scrape_jockey(self, mock_get_page, mock_config):
        """騎手情報取得のテスト"""
        mock_get_page.return_value = None  # 簡易テスト
        
        scraper = JockeyTrainerScraper(mock_config)
        result = scraper.scrape_jockey('01234')
        
        assert result == {}


class TestOddsDataScraper:
    """OddsDataScraperのテスト"""
    
    def test_init(self, mock_config):
        """初期化のテスト"""
        scraper = OddsDataScraper(mock_config)
        assert isinstance(scraper, BaseScraper)
    
    @patch.object(OddsDataScraper, '_get_page')
    def test_scrape_odds(self, mock_get_page, mock_config):
        """オッズ取得のテスト"""
        mock_get_page.return_value = None  # 簡易テスト
        
        scraper = OddsDataScraper(mock_config)
        result = scraper.scrape_odds('202401010101', 'win')
        
        assert result == {}


class TestDataValidator:
    """DataValidatorのテスト"""
    
    def test_init(self):
        """初期化のテスト"""
        validator = DataValidator()
        assert validator is not None
    
    def test_validate_race_data_valid(self):
        """正常なデータの検証テスト"""
        df = pd.DataFrame({
            'race_id': ['202401010101', '202401010101'],
            'race_date': ['2024-01-01', '2024-01-01'],
            'track_name': ['東京', '東京'],
            'horse_number': [1, 2],
            'horse_name': ['テストホース1', 'テストホース2'],
            'finish_position': [1, 2],
            'odds': [2.5, 5.0]
        })
        
        validator = DataValidator()
        result = validator.validate_race_data(df)
        
        assert result['is_valid'] == True
        assert result['total_records'] == 2
    
    def test_validate_race_data_empty(self):
        """空のDataFrameの検証テスト"""
        df = pd.DataFrame()
        
        validator = DataValidator()
        result = validator.validate_race_data(df)
        
        assert result['is_valid'] == False
        assert 'DataFrame is empty' in result['errors']
    
    def test_validate_race_data_missing_columns(self):
        """必須カラム欠損の検証テスト"""
        df = pd.DataFrame({
            'race_id': ['202401010101'],
            'horse_name': ['テストホース']
            # race_date が欠損
        })
        
        validator = DataValidator()
        result = validator.validate_race_data(df)
        
        assert result['is_valid'] == False
        assert len(result['errors']) > 0
    
    def test_validate_race_data_missing_values(self):
        """欠損値があるデータの検証テスト"""
        df = pd.DataFrame({
            'race_id': ['202401010101', '202401010101'],
            'race_date': ['2024-01-01', None],  # 欠損
            'track_name': ['東京', '東京'],
            'horse_number': [1, 2],
            'horse_name': ['テストホース1', 'テストホース2'],
            'finish_position': [1, 2]
        })
        
        validator = DataValidator()
        result = validator.validate_race_data(df)
        
        assert 'race_date' in result['missing_values']
    
    def test_validate_race_data_invalid_values(self):
        """無効な値の検証テスト"""
        df = pd.DataFrame({
            'race_id': ['202401010101'],
            'race_date': ['2024-01-01'],
            'track_name': ['東京'],
            'horse_number': [1],
            'horse_name': ['テストホース'],
            'finish_position': [99],  # 無効な着順
            'odds': [0.5]  # 無効なオッズ（<1.0）
        })
        
        validator = DataValidator()
        result = validator.validate_race_data(df)
        
        # 警告またはエラーが含まれるべき
        assert len(result['warnings']) > 0 or len(result['invalid_values']) > 0
    
    def test_validate_horse_data_valid(self):
        """馬データの検証テスト"""
        df = pd.DataFrame({
            'horse_id': ['2021100001', '2021100002'],
            'horse_name': ['テストホース1', 'テストホース2']
        })
        
        validator = DataValidator()
        result = validator.validate_horse_data(df)
        
        assert result['is_valid'] == True
        assert result['total_records'] == 2
    
    def test_validate_jockey_data_valid(self):
        """騎手データの検証テスト"""
        df = pd.DataFrame({
            'jockey_id': ['01234', '01235'],
            'jockey_name': ['テスト騎手1', 'テスト騎手2']
        })
        
        validator = DataValidator()
        result = validator.validate_jockey_data(df)
        
        assert result['is_valid'] == True
        assert result['total_records'] == 2
    
    def test_generate_report(self):
        """レポート生成のテスト"""
        validation_results = [
            {
                'is_valid': True,
                'total_records': 100,
                'missing_values': {'odds': 5},
                'invalid_values': {},
                'warnings': ['Some warning'],
                'errors': []
            }
        ]
        
        validator = DataValidator()
        report = validator.generate_report(validation_results)
        
        assert isinstance(report, str)
        assert '# Data Validation Report' in report
        assert 'PASSED' in report
        assert '100' in report


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
