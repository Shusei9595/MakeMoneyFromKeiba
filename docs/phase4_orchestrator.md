# Phase 4: オーケストレーター構築

## 概要

9つの専門家AIのスコアを統合し、最終的な勝率予測・EV計算・買い目生成を行うシステムを構築します。

## 目標

- ✅ エージェント管理システム（並列実行）
- ✅ 重み付けシステム（静的・動的）
- ✅ 予測オーケストレーター（統合スコア算出）
- ✅ EV計算エンジン（全券種対応）
- ✅ 買い目推奨システム（ケリー基準）

## システムアーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│              PredictionOrchestrator                 │
│  (中央制御・エージェント統合・勝率予測)                │
└─────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
┌───────────────┐ ┌──────────────┐ ┌──────────────┐
│ Agent Manager │ │ Weight       │ │ EV Calculator│
│ (並列実行)     │ │ Optimizer    │ │ (券種別計算)  │
└───────────────┘ └──────────────┘ └──────────────┘
        ↓               ↓               ↓
┌─────────────────────────────────────────────────────┐
│              BettingRecommender                     │
│  (買い目生成・資金配分・出力フォーマット)              │
└─────────────────────────────────────────────────────┘
```

## 実装構造

```
src/orchestrator/
├── __init__.py
├── agent_manager.py              # エージェント管理
├── weight_optimizer.py           # 重み最適化
├── prediction_orchestrator.py    # 予測統合
├── ev_calculator.py              # EV計算
├── betting_recommender.py        # 買い目推奨
└── run_prediction.py             # 実行スクリプト
```

## AgentManager（エージェント管理）

### 責任

- 9つのエージェントをロード
- 並列実行でスコアを収集（ThreadPoolExecutor）
- エラーハンドリング
- キャッシュ機構

### agent_manager.py

```python
"""
Agent Manager Module
9つのエージェントを管理・並列実行
"""
from concurrent.futures import ThreadPoolExecutor
from typing import Dict


class AgentManager:
    """エージェント管理クラス"""
    
    def __init__(self, model_dir: str):
        self.model_dir = model_dir
        self.agents = self.load_agents()
    
    def load_agents(self) -> Dict[str, BaseAgent]:
        """全エージェントをロード"""
        agents = {}
        
        agent_classes = [
            ('past_performance_agent', PastPerformanceAgent),
            ('distance_adaptability_agent', DistanceAdaptabilityAgent),
            # ... 他7つ
        ]
        
        for name, AgentClass in agent_classes:
            agent = AgentClass()
            model_path = f"{self.model_dir}/{name}_v1.pkl"
            agent.load_model(model_path)
            agents[name] = agent
        
        return agents
    
    def predict_parallel(
        self, 
        race_data: pd.DataFrame, 
        horse_data: pd.DataFrame
    ) -> Dict[str, Dict[int, float]]:
        """
        並列でエージェントのスコアを取得
        
        Returns:
            {
                'past_performance_agent': {horse_id_1: 7.5, ...},
                'distance_adaptability_agent': {horse_id_1: 8.2, ...},
                ...
            }
        """
        with ThreadPoolExecutor(max_workers=9) as executor:
            futures = {
                name: executor.submit(agent.predict, horse_data)
                for name, agent in self.agents.items()
            }
            
            results = {}
            for name, future in futures.items():
                try:
                    results[name] = future.result()
                except Exception as e:
                    self.logger.error(f"Error in {name}: {e}")
                    results[name] = None
            
            return results
```

## WeightOptimizer（重み最適化）

### 静的重み

```python
STATIC_WEIGHTS = {
    'past_performance_agent': 0.20,
    'distance_adaptability_agent': 0.15,
    'jockey_trainer_agent': 0.15,
    'pedigree_agent': 0.10,
    'race_pace_agent': 0.12,
    'physical_condition_agent': 0.08,
    'track_condition_agent': 0.10,
    'statistical_pattern_agent': 0.05,
    'odds_analysis_agent': 0.05
}
```

### 動的重み（Meta学習）

レース条件に応じて重みを動的に調整（オプション機能）。

```python
# Meta学習モデル（XGBoost）
# 入力: [距離, 馬場, 天候, ...] + 各エージェントの平均スコア
# 出力: 9つのエージェントの重み（合計=1.0）
```

## PredictionOrchestrator（予測統合）

### 統合スコア計算

```python
def calculate_integrated_score(
    agent_scores: Dict[str, Dict[int, float]],
    weights: Dict[str, float]
) -> Dict[int, float]:
    """
    加重平均で統合スコアを計算
    
    integrated_score = Σ(weight[i] × agent_score[i])
    """
    integrated_scores = {}
    
    for horse_id in agent_scores[list(agent_scores.keys())[0]].keys():
        score = sum(
            weights[agent_name] * agent_scores[agent_name][horse_id]
            for agent_name in weights.keys()
        )
        integrated_scores[horse_id] = score
    
    return integrated_scores
```

### スコア→勝率変換

```python
def score_to_probability(scores: Dict[int, float]) -> Dict[int, float]:
    """
    Softmax正規化で勝率を計算
    
    win_probability = exp(score) / Σ(exp(score))
    """
    score_values = np.array(list(scores.values()))
    exp_scores = np.exp(score_values - np.max(score_values))
    probabilities = exp_scores / exp_scores.sum()
    
    return dict(zip(scores.keys(), probabilities))
```

## EVCalculator（期待値計算）

### 対応券種

| 券種 | EV計算式 |
|------|---------|
| **単勝** | `勝率 × オッズ - 1` |
| **複勝** | `3着内率 × 平均オッズ - 1` |
| **ワイド** | `P(両馬が3着内) × オッズ - 1` |
| **馬連** | `P(2頭が1-2着) × オッズ - 1` |
| **3連複** | `P(3頭が1-2-3着) × オッズ - 1` |
| **3連単** | `P(着順通り) × オッズ - 1` |

### EVランク分類

```python
def classify_ev_rank(ev: float) -> str:
    """EVをランク付け"""
    if ev >= 0.20:
        return 'S'  # 20%以上
    elif ev >= 0.15:
        return 'A'  # 15-20%
    elif ev >= 0.10:
        return 'B'  # 10-15%
    elif ev >= 0.05:
        return 'C'  # 5-10%
    else:
        return 'D'  # 5%未満
```

### ev_calculator.py

```python
class EVCalculator:
    def calculate_win_ev(
        self, 
        win_probability: float, 
        odds: float
    ) -> float:
        """単勝EVを計算"""
        return win_probability * odds - 1
    
    def find_positive_ev_bets(
        self, 
        predictions: pd.DataFrame,
        odds_data: pd.DataFrame
    ) -> List[Dict]:
        """EV > 0の馬券候補を抽出"""
        positive_ev_bets = []
        
        # 全券種でEV計算
        for bet_type in ['win', 'place', 'wide', 'exacta', 'trifecta']:
            ev = self._calculate_ev(bet_type, predictions, odds_data)
            if ev > self.min_ev_threshold:
                positive_ev_bets.append({
                    'bet_type': bet_type,
                    'horses': [...],
                    'odds': odds,
                    'ev': ev,
                    'ev_rank': self.classify_ev_rank(ev)
                })
        
        return positive_ev_bets
```

## BettingRecommender（買い目推奨）

### 3つの戦略

| 戦略 | min_ev | kelly_multiplier | 券種優先 | 目標ROI |
|------|--------|-----------------|---------|---------|
| **Conservative** | 0.15 | 0.25 | 複勝・ワイド | 105% |
| **Balanced** | 0.10 | 0.50 | ワイド・単勝・3連複 | 115% |
| **Aggressive** | 0.05 | 0.75 | 3連複・3連単・ワイド | 130% |

### ケリー基準

```python
def calculate_kelly_bet(
    probability: float, 
    odds: float,
    total_budget: float
) -> float:
    """
    ケリー基準で最適購入額を計算
    
    kelly_fraction = (probability × odds - 1) / (odds - 1)
    bet_amount = total_budget × kelly_fraction × kelly_multiplier
    """
    kelly_fraction = (probability * odds - 1) / (odds - 1)
    bet_amount = total_budget * kelly_fraction * self.kelly_multiplier
    
    # 制約を適用
    bet_amount = min(bet_amount, total_budget * self.max_bet_fraction)
    bet_amount = max(bet_amount, self.min_bet_amount)
    
    return bet_amount
```

## 予測実行

### run_prediction.py

```bash
# 単一レース予測
python src/orchestrator/run_prediction.py \
    --race-id 202401050811 \
    --strategy balanced \
    --budget 10000 \
    --output results/

# 出力例
=================================================
         競馬予測AI - 買い目推奨
=================================================
レース: 2024年1月5日 大井9R
予算: 10,000円
戦略: balanced

-------------------------------------------------
【推奨買い目】
-------------------------------------------------
1. ワイド 5-3
   オッズ: 8.5倍
   期待値: +47% (Sランク)
   購入額: 3,000円
   期待リターン: 4,410円
   信頼度: 82%

2. 3連複 5-3-12
   オッズ: 45.2倍
   期待値: +48% (Sランク)
   購入額: 2,500円
   期待リターン: 3,700円
   信頼度: 75%

-------------------------------------------------
【合計】
-------------------------------------------------
購入合計: 7,500円 (予算の75%)
期待リターン: 10,670円
期待利益: +3,170円
期待ROI: +42.3%
=================================================
```

## テスト

```bash
# オーケストレーターのテスト
pytest tests/test_orchestrator.py -v

# カバレッジ確認
pytest tests/test_orchestrator.py --cov=src/orchestrator
```

## 成功基準

- ✅ 9エージェントを並列実行し、1レース < 1秒で予測完了
- ✅ 勝率予測の精度: Top3 Accuracy > 40%
- ✅ EV計算が全券種に対応
- ✅ 買い目推奨が生成される
- ✅ 全テストがパス

## 次のステップ

Phase 4が完了したら、[Phase 5: バックテスト・評価](phase5_evaluation.md) に進んでください。

## 参考資料

- [Kelly Criterion](https://en.wikipedia.org/wiki/Kelly_criterion)
- [Softmax Function](https://en.wikipedia.org/wiki/Softmax_function)
- [Ensemble Methods](https://scikit-learn.org/stable/modules/ensemble.html)
