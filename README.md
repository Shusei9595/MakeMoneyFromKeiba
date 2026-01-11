# 競馬AI予測システム 🏇

マルチエージェント方式による高精度な競馬予測システム

## 特徴

- 🤖 9つの専門家AIによるアンサンブル予測
- 📊 データ収集から予測まで全自動化
- 💰 期待値(EV)ベースの投資戦略
- 📈 バックテストによる性能検証
- 🔧 使いやすいCLIツール `keiba-ai`
- 🌐 ブラウザベースのWeb UI (Streamlit)
- 🐳 Docker対応

### 専門家AI（9つ）

| エージェント | 重み | 責務 |
|-------------|------|------|
| **過去成績分析AI** | 20% | 直近成績の分析・調子トレンド |
| **距離適性分析AI** | 15% | 距離とコースの相性 |
| **騎手・調教師分析AI** | 15% | 人的要因の分析・コンビネーション相性 |
| **血統分析AI** | 10% | 血統からの適性判断 |
| **レースペース分析AI** | 12% | ペース予測・展開予想 |
| **馬体・コンディション分析AI** | 8% | フィジカルコンディション・馬体重 |
| **馬場・天候適性分析AI** | 10% | 馬場状態・コース適性 |
| **統計パターン分析AI** | 5% | 歴史的パターン・ラップタイム分析 |
| **オッズ分析AI** | 5% | 市場分析・オッズの歪み検出 |

### アーキテクチャ

```
データ収集 → 前処理 → 9つの専門家AI → オーケストレーター → EV計算 → 買い目生成
```

**オーケストレーター**:
- 9つのエージェントのスコアを統合（加重平均）
- 動的重み付け（レース条件に応じた最適化）
- Softmax正規化で勝率・3着内率を算出
- 信頼区間の計算（ブートストラップ法）

## クイックスタート

### インストール

```bash
# リポジトリをクローン
git clone https://github.com/Shusei9595/MakeMoneyFromKeiba.git
cd MakeMoneyFromKeiba

# 仮想環境を作成
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# パッケージをインストール
pip install -e ".[dev]"

# 設定の初期化
keiba-ai config wizard
```

### 基本的な使い方 (CLI)

```bash
# ヘルプ表示
keiba-ai --help

# データ収集
keiba-ai collect --start-date 2024-01-01 --end-date 2024-12-31

# データ前処理
keiba-ai preprocess --input data/raw/ --output data/processed/

# モデル訓練
keiba-ai train --data data/processed/training_data.csv

# 予測実行
keiba-ai predict --date 2025-01-11 --strategy balanced --budget 10000

# バックテスト
keiba-ai backtest --start-date 2024-01-01 --end-date 2024-12-31
```

### Web UI

```bash
streamlit run src/web/app.py
# ブラウザで http://localhost:8501 にアクセス
```

### Docker

```bash
cd docker
docker-compose build
docker-compose run keiba-ai keiba-ai --help
```

## プロジェクト構造

```
MakeMoneyFromKeiba/
├── src/
│   ├── agents/           # 9つの専門家AI
│   ├── cli/              # CLIツール
│   ├── data_collection/  # データ収集
│   ├── evaluation/       # 評価・バックテスト
│   ├── monitoring/       # 監視・運用
│   ├── orchestrator/     # 予測統合・EV計算
│   ├── preprocessing/    # データ前処理
│   ├── training/         # モデル訓練
│   ├── analysis/         # 分析ツール
│   └── web/              # Web UI (Streamlit)
├── config/               # 設定
├── data/                 # データ（Git除外）
├── docker/               # Docker設定
├── docs/                 # ドキュメント
├── models/               # 訓練済みモデル（Git除外）
├── reports/              # レポート出力
├── results/              # 予測結果
└── tests/                # テスト
```

## パフォーマンス目標

### 戦略別目標

| 戦略 | 回収率 | シャープレシオ | 最大DD | 月次勝率 |
|------|--------|--------------|--------|----------|
| **Conservative** | 105-110% | > 1.0 | < 10% | > 70% |
| **Balanced** | 110-120% | > 1.2 | < 15% | > 60% |
| **Aggressive** | 120-140% | > 0.8 | < 25% | > 50% |

### エージェント性能目標

- 🎯 各エージェントのRMSE < 1.5（スコア予測誤差1.5点以内）
- 🎯 R² > 0.4（モデルの説明力40%以上）
- 🎯 Top3 Accuracy > 30%（上位3頭の予測精度30%以上）

## ドキュメント

- [クイックスタート](docs/user_guide/quickstart.md)
- [CLIリファレンス](docs/user_guide/cli_reference.md)
- [トラブルシューティング](docs/user_guide/troubleshooting.md)
- [設計書](docs/DESIGN.md)
- [インストールガイド](docs/user_guide/installation.md)
- [設定ガイド](docs/user_guide/configuration.md)

## 開発

### テスト実行

```bash
pytest tests/ -v
# カバレッジ確認
pytest --cov=src --cov-report=html
```

### コードフォーマット/チェック

```bash
black src/ tests/
mypy src/
```

## ライセンス

MIT License

## 貢献

貢献は歓迎します！詳細は [CONTRIBUTING.md](CONTRIBUTING.md) を参照。

---

*最終更新: 2026-01-11*
