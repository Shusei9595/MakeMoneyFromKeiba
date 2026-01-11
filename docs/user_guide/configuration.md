# 設定ガイド

競馬AI予測システムの設定ファイルについて説明します。

## 設定ファイル一覧

| ファイル | 説明 |
|---------|------|
| `config/config.yaml` | メイン設定 |
| `config/scraping_config.yaml` | スクレイピング設定 |
| `config/preprocessing_config.yaml` | 前処理設定 |
| `config/agent_config.yaml` | エージェント設定 |

## メイン設定 (`config.yaml`)

```yaml
# データディレクトリ
data:
  raw_dir: data/raw
  processed_dir: data/processed

# モデル設定
models:
  dir: models

# スクレイピング設定
scraping:
  crawl_delay: 1.0  # リクエスト間隔（秒）

# 予測設定
prediction:
  default_strategy: balanced
  default_budget: 10000
```

## CLIで設定を変更

```bash
# 設定表示
keiba-ai config show

# 設定変更
keiba-ai config set data.raw_dir /custom/path

# 対話的設定
keiba-ai config wizard
```

## 環境変数

以下の環境変数で設定を上書きできます：

| 変数名 | 説明 |
|--------|------|
| `KEIBA_CONFIG` | 設定ファイルパス |
| `KEIBA_DATA_DIR` | データディレクトリ |
| `KEIBA_MODELS_DIR` | モデルディレクトリ |

## スクレイピング設定

```yaml
# config/scraping_config.yaml
base_url: "https://db.netkeiba.com"
request_interval: 1.0  # 秒
timeout: 30
max_retries: 3

# エラーハンドリング
error_handling:
  retry_delay: 2.0
  exponential_backoff: true
  skip_on_error: true
```

## エージェント重み設定

```yaml
# config/agent_config.yaml
weights:
  past_performance: 0.20
  distance: 0.15
  jockey_trainer: 0.15
  pedigree: 0.10
  pace: 0.12
  physical: 0.08
  track_condition: 0.10
  statistical: 0.05
  odds: 0.05
```

## 戦略設定

| 戦略 | 説明 | EV閾値 |
|------|------|--------|
| `conservative` | 保守的 | +10%以上 |
| `balanced` | バランス型 | +5%以上 |
| `aggressive` | 積極的 | +0%以上 |
