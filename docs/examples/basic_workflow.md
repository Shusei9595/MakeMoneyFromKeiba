# 基本ワークフロー

このガイドでは、競馬AI予測システムの基本的な使い方を説明します。

## 概要

```
データ収集 → 前処理 → モデル訓練 → 予測実行 → 結果確認
```

---

## Step 1: データ収集

netkeiba.comからレースデータを収集します。

```bash
# 2024年のデータを収集（約30分～1時間）
keiba-ai collect \
    --start-date 2024-01-01 \
    --end-date 2024-12-31 \
    --output data/raw/
```

### オプション

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `--start-date` | 開始日 | 必須 |
| `--end-date` | 終了日 | 必須 |
| `--output` | 出力先 | `data/raw/` |
| `--parallel` | 並列数 | `1` |
| `--retry` | リトライ回数 | `3` |

### 出力ファイル

```
data/raw/
└── race_results_20240101_20241231.csv
```

---

## Step 2: データ前処理

収集したデータをモデル訓練用に加工します。

```bash
keiba-ai preprocess \
    --input data/raw/ \
    --output data/processed/
```

### 処理内容

1. 欠損値処理
2. カテゴリエンコーディング
3. 特徴量エンジニアリング
4. 正規化・スケーリング

### 出力ファイル

```
data/processed/
└── training_data.csv
```

---

## Step 3: モデル訓練

9つの専門家AIを訓練します。

```bash
# 全エージェントを訓練（約30分～1時間）
keiba-ai train \
    --data data/processed/training_data.csv \
    --output models/
```

### 特定エージェントのみ訓練

```bash
keiba-ai train \
    --data data/processed/training_data.csv \
    --agents past_performance,distance \
    --output models/
```

### ハイパーパラメータ最適化

```bash
keiba-ai train \
    --data data/processed/training_data.csv \
    --optimize \
    --cv-folds 10
```

### 出力ファイル

```
models/
├── past_performance_agent.pkl
├── distance_agent.pkl
├── jockey_trainer_agent.pkl
├── pedigree_agent.pkl
├── pace_agent.pkl
├── physical_agent.pkl
├── track_condition_agent.pkl
├── statistical_agent.pkl
└── odds_agent.pkl
```

---

## Step 4: 予測実行

レース予測を実行します。

```bash
keiba-ai predict \
    --date 2025-01-11 \
    --strategy balanced \
    --budget 10000 \
    --output results/
```

### 戦略の選択

| 戦略 | 説明 | EV閾値 |
|------|------|--------|
| `conservative` | 保守的（低リスク） | +10%以上 |
| `balanced` | バランス型 | +5%以上 |
| `aggressive` | 積極的（高リスク） | +0%以上 |

### 出力例

```
🎯 予測結果: 2025-01-11
戦略: balanced, 予算: 10,000円

レース: 中山1R
  ✅ 推奨: 単勝 3番 (EV: +12.5%)
  ✅ 推奨: 複勝 3番 (EV: +8.2%)
  💰 投資額: 1,500円

レース: 中山2R
  ✅ 推奨: ワイド 2-5 (EV: +15.3%)
  💰 投資額: 2,000円
...
```

---

## Step 5: バックテスト

過去データで戦略を検証します。

```bash
keiba-ai backtest \
    --start-date 2024-01-01 \
    --end-date 2024-12-31 \
    --strategies conservative,balanced,aggressive \
    --budget 100000 \
    --output reports/backtest_2024.html
```

### 出力レポート

- HTML形式のインタラクティブレポート
- 回収率、的中率、シャープレシオなどの指標
- 資金推移グラフ

---

## 完全なワークフロー例

```bash
# 1. 設定初期化
keiba-ai config wizard

# 2. データ収集
keiba-ai collect --start-date 2024-01-01 --end-date 2024-12-31

# 3. 前処理
keiba-ai preprocess --input data/raw/ --output data/processed/

# 4. 訓練
keiba-ai train --data data/processed/training_data.csv

# 5. バックテスト（検証）
keiba-ai backtest --start-date 2024-10-01 --end-date 2024-12-31 --strategies balanced

# 6. 本番予測
keiba-ai predict --date 2025-01-11 --strategy balanced --budget 10000
```

---

## Web UIを使う場合

ブラウザベースのインターフェースも利用可能です。

```bash
streamlit run src/web/app.py
# http://localhost:8501 にアクセス
```

**利点**:
- 視覚的なインターフェース
- リアルタイムのプログレス表示
- グラフによる結果可視化

---

## 次のステップ

- [CLIリファレンス](../user_guide/cli_reference.md) - 全コマンドの詳細
- [設定ガイド](../user_guide/configuration.md) - カスタマイズ方法
- [トラブルシューティング](../user_guide/troubleshooting.md) - 問題解決
