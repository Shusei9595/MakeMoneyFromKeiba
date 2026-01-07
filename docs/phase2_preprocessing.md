# Phase 2: データ前処理

## 概要

Phase 1で収集した生データを機械学習に適した形式に変換し、約50個の特徴量を生成します。

## 目標

- ✅ データクリーニング（欠損値・外れ値処理）
- ✅ 特徴量エンジニアリング（約50特徴量）
- ✅ データ正規化・標準化
- ✅ 訓練/検証/テストデータの分割

## 実装構造

```
src/preprocessing/
├── __init__.py
├── data_cleaner.py           # データクリーニング
├── feature_engineer.py       # 特徴量生成
├── data_preprocessor.py      # 統合前処理
├── run_preprocessing.py      # 実行スクリプト
└── utils.py                  # ユーティリティ関数
```

## データクリーニング

### data_cleaner.py

```python
"""
データクリーニングモジュール
"""
import pandas as pd
import numpy as np
from typing import Dict, Any


class DataCleaner:
    """データクリーニングクラス"""
    
    def __init__(self, config: Dict[str, Any]):
        self.missing_strategy = config.get('missing_value_strategy', 'median')
        self.outlier_threshold = config.get('outlier_threshold', 3.0)
    
    def clean_race_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        レースデータをクリーニング
        
        処理内容:
        1. 欠損値処理
        2. 外れ値処理
        3. データ型変換
        4. 重複除去
        """
        df = df.copy()
        
        # 欠損値処理
        df = self._handle_missing_values(df)
        
        # 外れ値処理
        df = self._handle_outliers(df)
        
        # データ型変換
        df = self._convert_dtypes(df)
        
        # 重複除去
        df = df.drop_duplicates()
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """欠損値を処理"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            if self.missing_strategy == 'median':
                df[col].fillna(df[col].median(), inplace=True)
            elif self.missing_strategy == 'mean':
                df[col].fillna(df[col].mean(), inplace=True)
            elif self.missing_strategy == 'zero':
                df[col].fillna(0, inplace=True)
        
        # カテゴリカル変数は"unknown"で埋める
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            df[col].fillna('unknown', inplace=True)
        
        return df
    
    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """外れ値をクリッピング（Z-score > threshold）"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            mean = df[col].mean()
            std = df[col].std()
            
            if std > 0:
                z_scores = np.abs((df[col] - mean) / std)
                outliers = z_scores > self.outlier_threshold
                
                if outliers.sum() > 0:
                    # 上限・下限でクリッピング
                    lower = mean - self.outlier_threshold * std
                    upper = mean + self.outlier_threshold * std
                    df[col] = df[col].clip(lower, upper)
        
        return df
```

## 特徴量エンジニアリング

### 基本特徴量（約50個）

#### 1. 馬の過去成績（10特徴量）
```python
features = [
    'recent_3_avg_speed',          # 直近3走平均速度
    'recent_3_finish_variance',    # 直近3走着順分散
    'last_race_position',          # 前走着順
    'recent_3_win_count',          # 直近3走勝利数
    'recent_5_avg_odds',           # 直近5走平均オッズ
    'speed_trend_slope',           # 速度トレンド
    'consistency_score',           # 一貫性スコア
    'days_since_last_race',        # 前走からの日数
    'career_win_rate',             # 通算勝率
    'career_place_rate'            # 通算3着内率
]
```

#### 2. 距離適性（8特徴量）
```python
features = [
    'optimal_distance',            # 得意距離
    'distance_deviation',          # 今回距離との乖離
    'distance_category_win_rate',  # 同距離カテゴリ勝率
    'short_distance_performance',  # 短距離成績
    'middle_distance_performance', # 中距離成績
    'long_distance_performance',   # 長距離成績
    'distance_versatility',        # 距離適応力
    'distance_preference_index'    # 距離嗜好指数
]
```

#### 3. 騎手・調教師（10特徴量）
```python
features = [
    'jockey_win_rate',             # 騎手勝率
    'jockey_top3_rate',            # 騎手3着内率
    'trainer_win_rate',            # 調教師勝率
    'trainer_top3_rate',           # 調教師3着内率
    'jockey_trainer_combo_win_rate', # コンビネーション勝率
    'jockey_recent_form',          # 騎手最近の調子
    'trainer_recent_form',         # 調教師最近の調子
    'jockey_track_win_rate',       # 騎手の場所勝率
    'jockey_distance_win_rate',    # 騎手の距離勝率
    'jockey_prize_money_total'     # 騎手生涯賞金
]
```

#### 4. 血統（8特徴量）
```python
features = [
    'sire_win_rate',               # 父馬勝率
    'dam_win_rate',                # 母馬勝率
    'sire_of_dam_win_rate',        # 母父勝率
    'bloodline_speed_index',       # 血統スピード指数
    'bloodline_stamina_index',     # 血統スタミナ指数
    'bloodline_versatility',       # 血統汎用性
    'pedigree_distance_affinity',  # 血統距離適性
    'inbreeding_coefficient'       # 近親交配係数
]
```

#### 5. その他（14特徴量）
```python
features = [
    # 馬体・コンディション
    'weight',                      # 馬体重
    'weight_change',               # 前走比体重変化
    'weight_change_ratio',         # 体重変化率
    'age',                         # 馬齢
    
    # 馬場・天候
    'track_condition_encoded',     # 馬場状態
    'weather_encoded',             # 天候
    'track_type_encoded',          # 芝/ダート
    'good_track_win_rate',         # 良馬場勝率
    'heavy_track_win_rate',        # 重馬場勝率
    
    # オッズ
    'odds',                        # 単勝オッズ
    'popularity',                  # 人気順位
    'odds_deviation',              # オッズ乖離度
    
    # その他
    'race_number',                 # レース番号
    'num_horses'                   # 出走頭数
]
```

### feature_engineer.py

```python
"""
特徴量エンジニアリングモジュール
"""
import pandas as pd
import numpy as np


class FeatureEngineer:
    """特徴量生成クラス"""
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """全特徴量を生成"""
        df = df.copy()
        
        # 過去成績特徴量
        df = self._create_past_performance_features(df)
        
        # 距離適性特徴量
        df = self._create_distance_features(df)
        
        # 騎手・調教師特徴量
        df = self._create_jockey_trainer_features(df)
        
        # 血統特徴量
        df = self._create_pedigree_features(df)
        
        # その他特徴量
        df = self._create_other_features(df)
        
        return df
    
    def _create_past_performance_features(
        self, 
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """過去成績特徴量を生成"""
        # グループ化（馬ごと）
        grouped = df.groupby('horse_id')
        
        # 直近3走の平均速度
        df['recent_3_avg_speed'] = grouped['speed'].transform(
            lambda x: x.rolling(3, min_periods=1).mean()
        )
        
        # 直近3走の着順分散
        df['recent_3_finish_variance'] = grouped['finish_position'].transform(
            lambda x: x.rolling(3, min_periods=1).var()
        )
        
        # 速度トレンド（線形回帰の傾き）
        df['speed_trend_slope'] = grouped['speed'].transform(
            lambda x: self._calculate_trend_slope(x)
        )
        
        return df
    
    @staticmethod
    def _calculate_trend_slope(series: pd.Series) -> float:
        """トレンドの傾きを計算"""
        if len(series) < 2:
            return 0.0
        
        x = np.arange(len(series))
        y = series.values
        
        # 線形回帰
        slope = np.polyfit(x, y, 1)[0]
        return slope
```

## データ前処理パイプライン

### run_preprocessing.py

```bash
# 基本実行
python src/preprocessing/run_preprocessing.py \
    --input-dir data/raw \
    --output-dir data/processed

# 設定ファイル指定
python src/preprocessing/run_preprocessing.py \
    --input-dir data/raw \
    --output-dir data/processed \
    --config config/preprocessing_config.yaml
```

### 出力ファイル

```
data/processed/
├── training_data.csv         # 訓練データ
├── validation_data.csv       # 検証データ
├── test_data.csv             # テストデータ
├── feature_list.txt          # 特徴量リスト
└── preprocessing_report.json # 前処理レポート
```

## データ分割

### 時系列分割

```python
# 時系列順に分割（データリークを防ぐ）
train_ratio = 0.6
val_ratio = 0.2
test_ratio = 0.2

n = len(df)
train_end = int(n * train_ratio)
val_end = int(n * (train_ratio + val_ratio))

train_df = df[:train_end]
val_df = df[train_end:val_end]
test_df = df[val_end:]
```

## 正規化・標準化

```python
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()

# 訓練データでfitし、全データに適用
train_features = scaler.fit_transform(train_df[numeric_cols])
val_features = scaler.transform(val_df[numeric_cols])
test_features = scaler.transform(test_df[numeric_cols])
```

## テスト

```bash
# 前処理のテスト
pytest tests/test_preprocessing.py -v

# 特定のテストのみ
pytest tests/test_preprocessing.py::test_feature_engineering -v
```

## 成功基準

- ✅ 50個以上の特徴量生成
- ✅ 欠損値率 < 1%
- ✅ 全特徴量の型が正しい
- ✅ 訓練/検証/テストの分割が適切
- ✅ 全テストがパス

## EDA（探索的データ分析）

```python
# notebooks/eda.ipynb で実行

import matplotlib.pyplot as plt
import seaborn as sns

# 特徴量の分布確認
df['recent_3_avg_speed'].hist(bins=50)
plt.title('直近3走平均速度の分布')
plt.show()

# 相関行列
correlation = df[numeric_features].corr()
sns.heatmap(correlation, cmap='coolwarm')
plt.show()
```

## 次のステップ

Phase 2が完了したら、[Phase 3: 専門家AIモデル構築](phase3_agents.md) に進んでください。

## 参考資料

- [pandas ドキュメント](https://pandas.pydata.org/docs/)
- [scikit-learn 前処理](https://scikit-learn.org/stable/modules/preprocessing.html)
- [Feature Engineering for Machine Learning](https://www.oreilly.com/library/view/feature-engineering-for/9781491953235/)
