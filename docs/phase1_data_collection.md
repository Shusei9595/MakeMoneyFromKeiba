# Phase 1: データ収集

## 概要

netkeiba等の競馬データソースから過去のレース結果、馬情報、騎手・調教師データ、オッズ情報を収集します。

## 目標

- ✅ レース結果データの収集（過去3年分）
- ✅ 馬情報の収集（血統、戦績）
- ✅ 騎手・調教師データの収集
- ✅ オッズデータの収集
- ✅ データ品質の検証

## データ収集対象

### 1. レース結果データ
- レースID、開催日、競馬場
- レース番号、レース名
- 距離、馬場状態、天候
- コース種別（芝/ダート）、コース形状（右回り/左回り）
- 頭数、出走馬リスト

### 2. 馬情報
- 馬ID、馬名
- 生年月日、性別、毛色
- 血統情報（父、母、母父）
- 過去成績（着順、タイム、賞金）
- 馬体重、体重変化

### 3. 騎手・調教師データ
- 騎手ID、騎手名
- 調教師ID、調教師名
- 過去成績（勝率、連対率、複勝率）
- 所属厩舎

### 4. オッズデータ
- 単勝オッズ
- 複勝オッズ（min/max）
- ワイドオッズ
- 馬連オッズ
- 3連複オッズ
- 3連単オッズ

## 実装構造

```
src/data_collection/
├── __init__.py
├── netkeiba_scraper.py      # メインスクレイパー
├── race_scraper.py           # レース結果収集
├── horse_scraper.py          # 馬情報収集
├── jockey_trainer_scraper.py # 騎手・調教師収集
├── odds_scraper.py           # オッズ収集
├── data_validator.py         # データ検証
└── run_collection.py         # 実行スクリプト
```

## データ収集の実装

### race_scraper.py

```python
"""
レース結果スクレイパー
"""
import time
import logging
from typing import List, Dict, Any
import requests
from bs4 import BeautifulSoup
import pandas as pd


class RaceResultScraper:
    """レース結果を収集"""
    
    def __init__(self, config: Dict[str, Any]):
        self.base_url = config['base_url']
        self.request_interval = config.get('request_interval', 1.0)
        self.logger = logging.getLogger(__name__)
    
    def scrape_race(self, race_id: str) -> Dict[str, Any]:
        """
        単一レースのデータを収集
        
        Args:
            race_id: レースID（例: "202401050811"）
        
        Returns:
            レースデータの辞書
        """
        url = f"{self.base_url}/race/{race_id}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            race_data = {
                'race_id': race_id,
                'race_name': self._extract_race_name(soup),
                'race_date': self._extract_race_date(soup),
                'track_name': self._extract_track_name(soup),
                'distance': self._extract_distance(soup),
                'track_condition': self._extract_track_condition(soup),
                'weather': self._extract_weather(soup),
                'horses': self._extract_horses(soup)
            }
            
            self.logger.info(f"Successfully scraped race {race_id}")
            time.sleep(self.request_interval)
            
            return race_data
            
        except Exception as e:
            self.logger.error(f"Error scraping race {race_id}: {e}")
            return {}
    
    def scrape_date_range(
        self, 
        start_date: str, 
        end_date: str
    ) -> pd.DataFrame:
        """
        日付範囲のレースデータを収集
        
        Args:
            start_date: 開始日（YYYY-MM-DD）
            end_date: 終了日（YYYY-MM-DD）
        
        Returns:
            レースデータのDataFrame
        """
        # 実装省略
        pass
```

### data_validator.py

```python
"""
データ検証モジュール
"""
import pandas as pd
from typing import Dict, List


class DataValidator:
    """データ品質を検証"""
    
    def validate_race_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        レースデータの品質を検証
        
        Args:
            df: レースデータのDataFrame
        
        Returns:
            検証結果レポート
        """
        report = {
            'total_records': len(df),
            'missing_values': {},
            'invalid_values': {},
            'duplicates': 0,
            'quality_score': 0.0
        }
        
        # 欠損値チェック
        for col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                report['missing_values'][col] = {
                    'count': int(missing_count),
                    'percentage': float(missing_count / len(df) * 100)
                }
        
        # 重複チェック
        report['duplicates'] = int(df.duplicated().sum())
        
        # 品質スコア算出
        missing_ratio = sum(
            v['count'] for v in report['missing_values'].values()
        ) / (len(df) * len(df.columns))
        duplicate_ratio = report['duplicates'] / len(df)
        
        report['quality_score'] = max(0, 1.0 - missing_ratio - duplicate_ratio)
        
        return report
```

## データ収集の実行

### run_collection.py

```bash
# 2024年1月のデータを収集
python src/data_collection/run_collection.py \
    --start-date 2024-01-01 \
    --end-date 2024-01-31 \
    --output data/raw/

# 進捗表示付き
python src/data_collection/run_collection.py \
    --start-date 2024-01-01 \
    --end-date 2024-12-31 \
    --output data/raw/ \
    --verbose
```

### 出力ファイル構造

```
data/raw/
├── races/
│   ├── 2024-01/
│   │   ├── race_202401050811.csv
│   │   ├── race_202401050812.csv
│   │   └── ...
│   └── 2024-02/
│       └── ...
├── horses/
│   ├── horse_2020100123.csv
│   └── ...
├── jockeys/
│   └── jockey_01234.csv
└── odds/
    └── odds_202401050811.csv
```

## データ品質管理

### 欠損値の処理方針

| カラム | 処理方法 |
|--------|----------|
| race_date | 必須（欠損は除外） |
| distance | 必須（欠損は除外） |
| track_condition | デフォルト値（"良"） |
| weather | デフォルト値（"晴"） |
| horse_weight | 中央値で補完 |
| odds | 欠損レコードは除外 |

### データ検証チェックリスト

- ✅ 全レースIDがユニーク
- ✅ 日付フォーマットの統一（YYYY-MM-DD）
- ✅ 数値カラムの型チェック
- ✅ オッズの範囲チェック（1.0〜999.9）
- ✅ 馬体重の範囲チェック（300〜600kg）

## 注意事項

### 1. Polite Crawling

```python
# リクエスト間隔を設定（最低1秒）
REQUEST_INTERVAL = 1.0

# User-Agentの設定
HEADERS = {
    'User-Agent': 'MakeMoneyFromKeiba/1.0 (Educational Purpose)'
}

# リトライ設定
MAX_RETRIES = 3
RETRY_DELAY = 5.0
```

### 2. robots.txt の遵守

```python
from urllib.robotparser import RobotFileParser

rp = RobotFileParser()
rp.set_url("https://db.netkeiba.com/robots.txt")
rp.read()

if rp.can_fetch("*", url):
    # スクレイピング実行
    pass
else:
    # スキップ
    pass
```

### 3. エラーハンドリング

```python
try:
    data = scraper.scrape_race(race_id)
except requests.exceptions.Timeout:
    logger.warning(f"Timeout for race {race_id}, retrying...")
except requests.exceptions.HTTPError as e:
    logger.error(f"HTTP error for race {race_id}: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

## テスト

### tests/test_data_collection.py

```bash
# データ収集のテスト
pytest tests/test_data_collection.py -v

# カバレッジ確認
pytest tests/test_data_collection.py --cov=src/data_collection
```

## 成功基準

- ✅ 過去3年分（約10,000レース）のデータ収集完了
- ✅ データ品質スコア > 0.95
- ✅ 欠損値率 < 5%
- ✅ 全テストがパス

## トラブルシューティング

### ネットワークエラー

```bash
# プロキシ設定
export HTTP_PROXY="http://proxy.example.com:8080"
export HTTPS_PROXY="https://proxy.example.com:8080"
```

### レート制限

```bash
# リクエスト間隔を延長
python run_collection.py --request-interval 2.0
```

## 次のステップ

Phase 1が完了したら、[Phase 2: データ前処理](phase2_preprocessing.md) に進んでください。

## 参考資料

- [requests ドキュメント](https://requests.readthedocs.io/)
- [BeautifulSoup ドキュメント](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [Webスクレイピングのベストプラクティス](https://www.scrapinghub.com/best-practices/)
