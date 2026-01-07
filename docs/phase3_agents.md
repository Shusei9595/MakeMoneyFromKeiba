# Phase 3: 専門家AIモデル構築

## 概要

9つの専門家AIモデルを構築し、それぞれが馬を10点満点で評価するシステムを実装します。

## 目標

- ✅ 9つの専門家AIクラスの実装
- ✅ BaseAgentの実装（共通インターフェース）
- ✅ 各エージェントの訓練
- ✅ 性能評価（RMSE < 1.5, R² > 0.4）
- ✅ エージェント比較レポート生成

## 9つの専門家AI

| # | エージェント名 | 重み | 責任範囲 |
|---|--------------|------|---------|
| 1 | PastPerformanceAgent | 20% | 過去成績分析 |
| 2 | DistanceAdaptabilityAgent | 15% | 距離適性分析 |
| 3 | JockeyTrainerAgent | 15% | 騎手・調教師分析 |
| 4 | PedigreeAgent | 10% | 血統分析 |
| 5 | RacePaceAgent | 12% | レースペース分析 |
| 6 | PhysicalConditionAgent | 8% | 馬体・コンディション分析 |
| 7 | TrackConditionAgent | 10% | 馬場・天候適性分析 |
| 8 | StatisticalPatternAgent | 5% | 統計パターン分析 |
| 9 | OddsAnalysisAgent | 5% | オッズ分析 |

## 実装構造

```
src/agents/
├── __init__.py
├── base_agent.py                     # 基底クラス
├── past_performance_agent.py         # 1. 過去成績AI
├── distance_adaptability_agent.py    # 2. 距離適性AI
├── jockey_trainer_agent.py           # 3. 騎手・調教師AI
├── pedigree_agent.py                 # 4. 血統AI
├── race_pace_agent.py                # 5. レースペースAI
├── physical_condition_agent.py       # 6. 馬体・コンディションAI
├── track_condition_agent.py          # 7. 馬場・天候適性AI
├── statistical_pattern_agent.py      # 8. 統計パターンAI
└── odds_analysis_agent.py            # 9. オッズ分析AI
```

## BaseAgent（基底クラス）

### 設計思想

- ABC（抽象基底クラス）による共通インターフェース
- LightGBM Regressorによる10点満点スコア予測
- TimeSeriesSplitによる時系列交差検証
- モデルの保存・読み込み機能

### base_agent.py

```python
"""
Base Agent Module
全ての専門家AIの基底クラス
"""
from abc import ABC, abstractmethod
import lightgbm as lgb


class BaseAgent(ABC):
    """全エージェントの基底クラス"""
    
    @abstractmethod
    def _get_feature_list(self) -> List[str]:
        """使用する特徴量リストを返す"""
        pass
    
    @staticmethod
    def create_target_score(finish_position: int) -> float:
        """
        着順から10点満点の理想スコアを生成
        
        Args:
            finish_position: 着順（1〜18）
        
        Returns:
            10点満点のスコア
        """
        if finish_position == 1:
            return 10.0
        elif finish_position == 2:
            return 8.5
        elif finish_position == 3:
            return 7.0
        else:
            return max(1.0, 7.0 - (finish_position - 3) * 0.5)
    
    def train(self, X, y, groups=None, n_folds=5):
        """モデルを訓練（TimeSeriesSplit）"""
        pass
    
    def predict(self, X):
        """予測を実行（1.0〜10.0にクリップ）"""
        pass
    
    def save_model(self, output_dir):
        """モデルを保存"""
        pass
    
    def load_model(self, filepath):
        """モデルを読み込み"""
        pass
```

## 各エージェントの特徴量

### 1. PastPerformanceAgent

```python
features = [
    'recent_3_avg_speed',
    'recent_3_finish_variance',
    'last_race_position',
    'recent_3_win_count',
    'recent_5_avg_odds',
    'speed_trend_slope',
    'consistency_score',
    'days_since_last_race',
    'career_win_rate',
    'career_place_rate'
]
```

### 2. DistanceAdaptabilityAgent

```python
features = [
    'optimal_distance',
    'distance_deviation',
    'distance_category_win_rate',
    'short_distance_performance',
    'middle_distance_performance',
    'long_distance_performance',
    'distance_versatility',
    'distance_preference_index'
]
```

### 3. JockeyTrainerAgent

```python
features = [
    'jockey_win_rate',
    'jockey_top3_rate',
    'trainer_win_rate',
    'trainer_top3_rate',
    'jockey_trainer_combo_win_rate',
    'jockey_recent_form',
    'trainer_recent_form',
    'jockey_track_win_rate',
    'jockey_distance_win_rate',
    'jockey_prize_money_total'
]
```

## モデル訓練

### 訓練データ準備

```bash
# 着順から10点満点スコアを生成
python src/training/prepare_training_data.py \
    --input-file data/processed/processed_races.csv \
    --output-dir data/processed/
```

### エージェント訓練

```bash
# 全9エージェントを訓練
python src/training/train_agents.py \
    --data data/processed/training_data.csv \
    --validation data/processed/validation_data.csv \
    --output models/ \
    --n-folds 5
```

### LightGBMパラメータ

```python
model_params = {
    'objective': 'regression',
    'metric': 'rmse',
    'num_leaves': 31,
    'learning_rate': 0.05,
    'n_estimators': 500,
    'feature_fraction': 0.8,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'verbose': -1,
    'random_state': 42
}
```

## 評価指標

### エージェント性能目標

| 指標 | 目標値 | 説明 |
|------|--------|------|
| **RMSE** | < 1.5 | スコア予測の平均誤差が1.5点以内 |
| **MAE** | < 1.2 | 平均絶対誤差が1.2点以内 |
| **R²** | > 0.4 | モデルの説明力が40%以上 |
| **Top3 Accuracy** | > 30% | 上位3頭の予測精度が30%以上 |

### 評価スクリプト

```bash
# テストデータで評価
python src/training/evaluate_agents.py \
    --test-data data/processed/test_data.csv \
    --models models/ \
    --output reports/agent_evaluation.html
```

## エージェント比較

### agent_comparison.py

```bash
# 9エージェントの性能を比較
python src/analysis/agent_comparison.py \
    --test-data data/processed/test_data.csv \
    --models models/ \
    --output reports/agent_comparison_report.html
```

### 比較レポート内容

1. **性能比較表**
   - 各エージェントのRMSE, MAE, R²
   
2. **特徴量重要度ランキング**
   - 各エージェントのTop 10特徴量
   
3. **エージェント間相関ヒートマップ**
   - スコアの相関関係を可視化
   
4. **距離別・馬場別性能**
   - 条件別の予測精度

## テスト

```bash
# エージェントのテスト
pytest tests/test_agents.py -v

# カバレッジ確認
pytest tests/test_agents.py --cov=src/agents
```

### テスト内容

- ✅ インスタンス化テスト
- ✅ ダミーデータでの予測テスト（出力範囲確認）
- ✅ モデル保存・読み込みテスト
- ✅ 特徴量重要度取得テスト
- ✅ 訓練・評価の統合テスト

## 訓練結果の例

```
=================================================
         エージェント訓練結果
=================================================
1. PastPerformanceAgent
   - RMSE: 1.23
   - MAE: 0.98
   - R²: 0.52
   - 訓練時間: 45秒

2. DistanceAdaptabilityAgent
   - RMSE: 1.35
   - MAE: 1.08
   - R²: 0.46
   - 訓練時間: 38秒

...

9. OddsAnalysisAgent
   - RMSE: 1.48
   - MAE: 1.19
   - R²: 0.41
   - 訓練時間: 32秒

=================================================
全エージェント訓練完了！
モデル保存先: models/
=================================================
```

## 成功基準

- ✅ 9つのエージェント全てが実装されている
- ✅ 各エージェントのRMSE < 1.5, R² > 0.4を達成
- ✅ エージェント比較レポートが生成される
- ✅ 全テストがパス
- ✅ モデルファイルが`models/`に保存されている

## トラブルシューティング

### 訓練が遅い場合

```python
# n_estimatorsを減らす
'n_estimators': 300  # 500 → 300

# num_leavesを減らす
'num_leaves': 21  # 31 → 21
```

### メモリ不足の場合

```bash
# バッチ処理に切り替え
python src/training/train_agents.py --batch-size 1000
```

### 精度が低い場合

- 特徴量エンジニアリングの見直し
- ハイパーパラメータチューニング（Optuna使用）
- より多くの訓練データを収集

## 次のステップ

Phase 3が完了したら、[Phase 4: オーケストレーター構築](phase4_orchestrator.md) に進んでください。

## 参考資料

- [LightGBM ドキュメント](https://lightgbm.readthedocs.io/)
- [scikit-learn TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)
- [Ensemble Learning](https://en.wikipedia.org/wiki/Ensemble_learning)
