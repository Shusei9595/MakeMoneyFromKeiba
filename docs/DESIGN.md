# 競馬AI予測システム 設計書

## 1. システム概要

本システムは、マルチエージェント方式による競馬予測システムです。9つの専門家AIがそれぞれの観点から分析を行い、アンサンブル予測により高精度な予測を実現します。

## 2. アーキテクチャ

### 2.1 全体構成

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLI Interface                            │
│                      (keiba-ai command)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Orchestrator Layer                          │
│              (データフロー管理・実行制御)                         │
└─────────────────────────────────────────────────────────────────┘
           │              │              │              │
           ▼              ▼              ▼              ▼
    ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐
    │  Data    │   │ Feature  │   │  Multi-  │   │  Result  │
    │Collection│   │Engineering│   │  Agent   │   │Aggregator│
    │  Module  │   │  Module  │   │  System  │   │  Module  │
    └──────────┘   └──────────┘   └──────────┘   └──────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
             ┌──────────┐       ┌──────────┐       ┌──────────┐
             │ Agent 1  │  ...  │ Agent 5  │  ...  │ Agent 9  │
             │(前走分析)│       │(展開予測)│       │(異常検出)│
             └──────────┘       └──────────┘       └──────────┘
```

### 2.2 コンポーネント詳細

#### データ収集モジュール (Data Collection Module)
- **責務**: 外部データソースからのデータ取得
- **機能**:
  - レース情報の取得
  - 馬の過去成績取得
  - オッズ情報の取得
  - 天候・馬場状態の取得

#### 特徴量エンジニアリングモジュール (Feature Engineering Module)
- **責務**: 生データから機械学習用特徴量への変換
- **機能**:
  - 数値特徴量の正規化
  - カテゴリ特徴量のエンコーディング
  - 時系列特徴量の生成
  - 欠損値処理

#### マルチエージェントシステム (Multi-Agent System)
- **責務**: 9つの専門家AIによる予測生成
- **実装**: `src/agents/` ディレクトリ
- **構成**:

| エージェント | ファイル | 重み | 責務 |
|-------------|---------|------|------|
| 前走パフォーマンスAI | `past_performance_agent.py` | 20% | 直近レース成績の分析 |
| 距離・コース適性AI | `distance_adaptability_agent.py` | 15% | 距離・コース相性の評価 |
| 騎手・調教師AI | `jockey_trainer_agent.py` | 15% | 人的要因の分析 |
| 血統AI | `pedigree_agent.py` | 10% | 血統からの適性判断 |
| レース展開AI | `race_pace_agent.py` | 12% | ペース・展開予測 |
| 馬体・調教AI | `physical_condition_agent.py` | 8% | コンディション評価 |
| 馬場・天候AI | `track_condition_agent.py` | 10% | 馬場状態の分析 |
| 統計パターンAI | `statistical_pattern_agent.py` | 5% | 歴史的パターン認識 |
| オッズ分析AI | `odds_analysis_agent.py` | 5% | 市場情報の分析 |

- **基底クラス**: `base_agent.py` - LightGBM Regressorで10点満点スコアを予測

#### オーケストレーター (Orchestrator)
- **責務**: エージェント統合・勝率予測・EV計算・買い目生成
- **実装**: `src/orchestrator/` ディレクトリ
- **構成**:

| モジュール | ファイル | 責務 |
|-----------|---------|------|
| エージェント管理 | `agent_manager.py` | 9エージェントの並列実行 |
| 重み最適化 | `weight_optimizer.py` | 静的/動的重み付け |
| 予測統合 | `prediction_orchestrator.py` | スコア統合・勝率算出 |
| EV計算 | `ev_calculator.py` | 券種別期待値計算 |
| 買い目推奨 | `betting_recommender.py` | ケリー基準で資金配分 |

#### 結果集約モジュール (Result Aggregator Module)
- **責務**: 各エージェントの予測を統合
- **機能**:
  - 重み付けアンサンブル（Softmax正規化）
  - 期待値(EV)計算（単勝/複勝/ワイド/馬連/3連複）
  - 推奨ベット戦略生成（conservative/balanced/aggressive）

## 3. データフロー

### 3.1 予測フロー

```
[外部データソース]
        │
        ▼ (1) データ収集 (src/data_collection/)
[Raw Data] → data/raw/
        │
        ▼ (2) 前処理・特徴量生成 (src/preprocessing/)
[Feature Matrix] → data/processed/
        │
        ▼ (3) 各エージェントで予測 (src/agents/)
[9つの予測スコア]
        │
        ▼ (4) オーケストレーター統合 (src/orchestrator/)
[最終予測・期待値]
        │
        ▼ (5) 買い目推奨 (betting_recommender.py)
[推奨アクション] → results/
```


### 3.2 学習フロー

```
[過去レースデータ]
        │
        ▼ (1) データ収集・クリーニング
[Training Dataset]
        │
        ▼ (2) 特徴量エンジニアリング
[Feature Matrix + Labels]
        │
        ▼ (3) 各エージェント学習
[9つの学習済みモデル]
        │
        ▼ (4) バックテスト・評価
[Performance Metrics]
```

## 4. データモデル

### 4.1 コアエンティティ

#### Race (レース)
```python
class Race:
    race_id: str           # レース識別子
    race_name: str         # レース名
    date: datetime         # 開催日
    venue: str             # 競馬場
    course_type: str       # 芝/ダート
    distance: int          # 距離(m)
    track_condition: str   # 馬場状態
    weather: str           # 天候
    grade: str             # グレード
```

#### Horse (馬)
```python
class Horse:
    horse_id: str          # 馬識別子
    name: str              # 馬名
    age: int               # 年齢
    sex: str               # 性別
    weight: float          # 馬体重
    father: str            # 父馬
    mother: str            # 母馬
    trainer: str           # 調教師
```

#### Entry (出走情報)
```python
class Entry:
    race_id: str           # レースID
    horse_id: str          # 馬ID
    post_position: int     # 枠番
    horse_number: int      # 馬番
    jockey: str            # 騎手
    weight_carried: float  # 斤量
    odds: float            # オッズ
    popularity: int        # 人気順
```

#### Prediction (予測)
```python
class Prediction:
    race_id: str           # レースID
    horse_id: str          # 馬ID
    win_probability: float # 勝率予測
    place_probability: float # 複勝率予測
    expected_value: float  # 期待値
    confidence: float      # 信頼度
    agent_scores: dict     # 各エージェントのスコア
```

## 5. 技術スタック

### 5.1 言語・フレームワーク
- **Python 3.10+**: メイン言語
- **scikit-learn**: 機械学習基盤
- **LightGBM/XGBoost**: 勾配ブースティング
- **pandas/numpy**: データ処理
- **Click**: CLIフレームワーク

### 5.2 データストレージ
- **SQLite/PostgreSQL**: 構造化データ
- **Parquet**: 大規模データセット
- **YAML**: 設定ファイル

### 5.3 品質管理
- **pytest**: テストフレームワーク
- **black**: コードフォーマッター
- **mypy**: 型チェック
- **ruff**: リンター

## 6. セキュリティ考慮事項

### 6.1 データ保護
- 認証情報は環境変数または暗号化設定ファイルで管理
- センシティブデータのログ出力禁止
- データバックアップの定期実行

### 6.2 API利用
- レート制限の遵守
- エラーハンドリングとリトライ機構
- タイムアウト設定

## 7. パフォーマンス要件

### 7.1 予測精度
- 回収率: 105-115%
- 的中率: 40-50%
- NDCG@3: 0.65以上

### 7.2 処理性能
- 単一レース予測: < 5秒
- 1日分データ収集: < 30分
- モデル学習 (1年分): < 2時間

## 8. Phase 6: 運用・デプロイメント

### 8.1 CLIツール

`keiba-ai` コマンドで全機能を実行可能:

```bash
keiba-ai collect     # データ収集
keiba-ai preprocess  # 前処理
keiba-ai train       # 訓練
keiba-ai predict     # 予測
keiba-ai backtest    # バックテスト
keiba-ai report      # レポート生成
keiba-ai config      # 設定管理
```

### 8.2 Docker

環境非依存の実行環境を提供:

```bash
docker-compose run keiba-ai keiba-ai predict --date 2025-01-12 --strategy balanced --budget 10000
```

### 8.3 Web UI

Streamlitによるブラウザインターフェース:

```bash
streamlit run src/web/app.py
```

### 8.4 監視・運用

- **メトリクス収集**: `src/monitoring/metrics.py`
- **アラート送信**: `src/monitoring/alerts.py`
- **定期実行**: `src/monitoring/scheduler.py`

## 9. 今後の拡張計画

1. **リアルタイム予測**: ライブオッズ連携
2. **深層学習エージェント**: Transformer系モデルの導入
3. **自動ベッティング**: API連携による自動投票
4. **クラウドデプロイ**: AWS/GCP対応

---

*最終更新: 2026-01-10*
*バージョン: 1.0*
