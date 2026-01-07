# ADR-005: オーケストレーター統合アーキテクチャ

## ステータス

採用

## コンテキスト

Phase 4で9つの専門家AIの予測を統合し、最終的な勝率予測とEV（期待値）計算を行うシステムを構築する必要があった。

要件:
- 9エージェントの並列実行（1秒以内で完了）
- エージェントごとの重み付け（静的/動的）
- スコアから勝率への変換
- 複数券種のEV計算（単勝/複勝/ワイド/馬連/3連複）
- 資金配分アルゴリズム

検討したオプション:
1. **単純平均** - 全エージェント同等の重み
2. **静的重み付け** - 事前定義された固定重み
3. **動的重み付け** - レース条件に応じて重みを調整（Meta学習）

## 決定

**静的重み付け + 将来の動的重み拡張** を採用する。

### 統合アーキテクチャ

```
AgentManager → WeightOptimizer → PredictionOrchestrator → EVCalculator → BettingRecommender
```

### 重み配分（静的）

| エージェント | 重み |
|-------------|------|
| past_performance | 20% |
| distance_adaptability | 15% |
| jockey_trainer | 15% |
| race_pace | 12% |
| pedigree | 10% |
| track_condition | 10% |
| physical_condition | 8% |
| statistical_pattern | 5% |
| odds_analysis | 5% |

### 勝率変換

Softmax正規化でスコアを確率に変換:
```python
win_prob[i] = exp(score[i]) / Σexp(score[j])
```

### 資金配分

ケリー基準（0.5×Kelly）を採用:
```python
kelly = (prob * odds - 1) / (odds - 1)
bet = budget * kelly * 0.5
```

## 影響

### ポジティブ
- 1レース1秒以内で予測完了（ThreadPoolExecutor並列）
- 重み調整による柔軟性
- EVベースの合理的な資金配分

### ネガティブ
- 静的重みは全レースで同一（動的重みで将来改善可能）
- ケリー基準は勝率推定の誤差に敏感

## 関連

- `src/orchestrator/` - 全モジュール
- ADR-004: LightGBMベースのスコア予測
