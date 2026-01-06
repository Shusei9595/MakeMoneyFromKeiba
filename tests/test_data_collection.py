import pytest
from unittest.mock import Mock, patch
import pandas as pd
from pathlib import Path
import sys

# srcモジュールへのパスを通す
sys.path.append(str(Path(__file__).parent.parent))

from src.data_collection.netkeiba_scraper import (
    RaceResultScraper,
    HorseInfoScraper,
    JockeyTrainerScraper
)
from src.data_collection.data_validator import DataValidator


@pytest.fixture
def mock_config():
    """テスト用の設定"""
    return {
        'base_url': 'https://db.netkeiba.com',
        'request_interval': 0.0,
        'timeout': 10,
        'user_agent': 'TestBot',
        'max_retries': 2
    }


@pytest.fixture
def sample_race_html():
    """サンプルのレースページHTML"""
    # 最小限のHTML構造
    return """
    <html>
        <div class="data_intro">
            <h1>Test Race</h1>
            <dl class="racedata01">
                芝2000m (右) 天候:晴 芝:良
            </dl>
            <p class="smalltxt">
                2024年1月1日 1回東京1日目
            </p>
        </div>
        <table class="race_table_01">
            <tr><!-- Header --></tr>
            <tr>
                <td>1</td><!-- finish -->
                <td>1</td><!-- frame -->
                <td>1</td><!-- horse_num -->
                <td><a href="/horse/2021100000/">Test Horse</a></td>
                <td>牡3</td>
                <td>56.0</td>
                <td><a href="/jockey/00000/">Test Jockey</a></td>
                <td>1:59.9</td>
                <td></td>
                <td></td><td></td><td></td><td></td><td></td>
                <td>480(+2)</td>
                <td></td><td></td><td></td>
                 <td><a href="/trainer/00000/">Test Trainer</a></td>
            </tr>
        </table>
    </html>
    """

class TestRaceResultScraper:
    """RaceResultScraperのテスト"""
    
    def test_init(self, mock_config):
        """初期化のテスト"""
        scraper = RaceResultScraper(mock_config)
        assert scraper.base_url == 'https://db.netkeiba.com'
        assert scraper.request_interval == 0.0
    
    @patch('requests.Session.get')
    def test_get_page_success(self, mock_get, mock_config, sample_race_html):
        """ページ取得成功のテスト"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_race_html
        mock_response.apparent_encoding = 'utf-8' # encodingの設定
        mock_get.return_value = mock_response
        
        scraper = RaceResultScraper(mock_config)
        soup = scraper._get_page('https://db.netkeiba.com/race/202401010101/')
        
        assert soup is not None
        assert soup.find('h1').text == 'Test Race'
    
    @patch('requests.Session.get')
    def test_get_page_404(self, mock_get, mock_config):
        """404エラーのテスト"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        scraper = RaceResultScraper(mock_config)
        soup = scraper._get_page('https://db.netkeiba.com/race/invalid/')
        
        assert soup is None
    
    @patch('requests.Session.get')
    def test_scrape_race(self, mock_get, mock_config, sample_race_html):
        """レース情報取得のテスト"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = sample_race_html
        mock_response.apparent_encoding = 'utf-8'
        mock_get.return_value = mock_response
        
        scraper = RaceResultScraper(mock_config)
        data = scraper.scrape_race('202401010101')
        
        assert 'results' in data
        assert len(data['results']) == 1
        result = data['results'][0]
        assert result['horse_name'] == 'Test Horse'
        assert result['finish_position'] == '1'
        assert result['track_type'] == '芝'
        assert result['distance'] == 2000


class TestDataValidator:
    """DataValidatorのテスト"""
    
    def test_validate_race_data_valid(self):
        """正常なデータの検証テスト"""
        df = pd.DataFrame({
            'race_id': ['202401010101'],
            'race_date': ['2024-01-01'],
            'track_name': ['東京'],
            'race_name': ['Test Race'],
            'finish_position': [1],
            'horse_id': ['2021100000'],
            'horse_name': ['テストホース'],
            'jockey_id': ['00000'],
            'odds': [5.2]
        })
        
        validator = DataValidator()
        result = validator.validate_race_data(df)
        
        assert result['is_valid'] == True
        assert result['total_records'] == 1
    
    def test_validate_race_data_missing_column(self):
        """必須カラム欠落のテスト"""
        df = pd.DataFrame({
            'race_id': ['202401010101'],
            # race_date missing
            'finish_position': [1]
        })
        
        validator = DataValidator()
        result = validator.validate_race_data(df)
        
        assert result['is_valid'] == False
        assert any('Missing required columns' in e for e in result['errors'])

    def test_validate_race_data_missing_values(self):
        """欠損値があるデータの検証テスト"""
        df = pd.DataFrame({
            'race_id': ['202401010101'],
            'race_date': [None],  # 欠損
            'track_name': ['東京'],
            'race_name': ['Test Race'],
            'finish_position': [1],
            'horse_id': ['2021100000'],
            'horse_name': ['テストホース'],
            'jockey_id': ['00000']
        })
        
        validator = DataValidator()
        result = validator.validate_race_data(df)
        
        # is_validはTrueだがwarningが出る設計（必須カラムの値欠損はwarning扱い）
        # ただしValidator実装で"Missing values found in required column"をwarningに入れている
        assert result['is_valid'] == True
        assert 'race_date' in result['missing_values']
        assert len(result['warnings']) > 0
