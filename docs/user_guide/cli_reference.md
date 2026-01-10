# CLIコマンドリファレンス

`keiba-ai` CLIツールの全コマンド仕様です。

## グローバルオプション

```bash
keiba-ai [OPTIONS] COMMAND [ARGS]...
```

| オプション | 説明 |
|-----------|------|
| `--version` | バージョン表示 |
| `-v, --verbose` | 詳細ログ出力 |
| `--help` | ヘルプ表示 |

---

## `keiba-ai collect`

netkeiba.comからレースデータを収集します。

```bash
keiba-ai collect --start-date 2024-01-01 --end-date 2024-12-31 --output data/raw/
```

### オプション

| オプション | 必須 | 説明 | デフォルト |
|-----------|------|------|-----------|
| `--start-date` | ✅ | 開始日（YYYY-MM-DD） | - |
| `--end-date` | ✅ | 終了日（YYYY-MM-DD） | - |
| `-o, --output` | - | 出力ディレクトリ | `data/raw/` |
| `--parallel` | - | 並列実行数 | `1` |
| `--retry` | - | リトライ回数 | `3` |

---

## `keiba-ai preprocess`

収集したデータを前処理します。

```bash
keiba-ai preprocess --input data/raw/ --output data/processed/
```

### オプション

| オプション | 必須 | 説明 | デフォルト |
|-----------|------|------|-----------|
| `-i, --input` | ✅ | 入力ディレクトリ | - |
| `-o, --output` | - | 出力ディレクトリ | `data/processed/` |
| `--validate` | - | データ品質検証 | `False` |
| `--export-stats` | - | 統計エクスポート | `False` |

---

## `keiba-ai train`

専門家AIモデルを訓練します。

```bash
keiba-ai train --data data/processed/training_data.csv --output models/
```

### オプション

| オプション | 必須 | 説明 | デフォルト |
|-----------|------|------|-----------|
| `-d, --data` | ✅ | 訓練データパス | - |
| `-o, --output` | - | モデル出力先 | `models/` |
| `--agents` | - | 対象エージェント（カンマ区切り） | 全9エージェント |
| `--optimize` | - | ハイパーパラメータ最適化 | `False` |
| `--cv-folds` | - | CV分割数 | `5` |

### 対応エージェント

`past_performance`, `distance`, `track_condition`, `jockey_trainer`, `pace`, `pedigree`, `weight`, `odds_analysis`, `class_level`

---

## `keiba-ai predict`

レース予測を実行します。

```bash
keiba-ai predict --date 2024-12-31 --strategy balanced --budget 10000
```

### オプション

| オプション | 必須 | 説明 | デフォルト |
|-----------|------|------|-----------|
| `--race-id` | △ | レースID（12桁） | - |
| `--date` | △ | 日付（YYYY-MM-DD） | - |
| `--strategy` | ✅ | 戦略 | - |
| `--budget` | ✅ | 予算（円） | - |
| `--models` | - | モデルディレクトリ | `models/` |
| `-o, --output` | - | 出力先 | `results/` |
| `--format` | - | 出力形式 | `text` |

※ `--race-id` または `--date` のいずれかが必須

### 戦略

- `conservative`: 保守的（回収率105-110%目標）
- `balanced`: バランス型（回収率110-120%目標）
- `aggressive`: 積極的（回収率120-140%目標）

---

## `keiba-ai backtest`

過去データでバックテストを実行します。

```bash
keiba-ai backtest --start-date 2024-01-01 --end-date 2024-12-31 --strategies balanced
```

### オプション

| オプション | 必須 | 説明 | デフォルト |
|-----------|------|------|-----------|
| `--start-date` | ✅ | 開始日 | - |
| `--end-date` | ✅ | 終了日 | - |
| `--strategies` | - | 戦略リスト | `balanced` |
| `--budget` | - | 初期資金 | `100000` |
| `-o, --output` | - | レポート出力先 | 自動生成 |
| `--benchmark` | - | ベンチマーク | - |

---

## `keiba-ai report`

レポートを生成します。

```bash
keiba-ai report --backtest-results reports/backtest.json --output reports/summary.html
```

### オプション

| オプション | 説明 |
|-----------|------|
| `--backtest-results` | バックテスト結果ファイル |
| `-o, --output` | 出力パス |
| `--auto-monthly` | 月次レポート自動生成 |
| `--year` | 対象年 |

---

## `keiba-ai config`

設定を管理します。

### サブコマンド

```bash
# 設定表示
keiba-ai config show

# 設定変更
keiba-ai config set data.raw_dir /custom/path

# 設定ウィザード
keiba-ai config wizard
```
