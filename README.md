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
```

### 基本的な使い方

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
keiba-ai predict --date 2025-01-12 --strategy balanced --budget 10000

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

## システム構成

### 専門家AI（9つ）

| エージェント | 重み | 責務 |
|-------------|------|------|
| 前走パフォーマンスAI | 20% | 直近成績の分析 |
| 距離・コース適性AI | 15% | 距離とコースの相性 |
| 騎手・調教師AI | 15% | 人的要因の分析 |
| 血統AI | 10% | 血統からの適性判断 |
| レース展開AI | 12% | ペース予測 |
| 馬体・調教AI | 8% | フィジカルコンディション |
| 馬場・天候AI | 10% | 馬場状態の分析 |
| 統計パターンAI | 5% | 歴史的パターン |
| オッズ分析AI | 5% | 市場分析 |

## プロジェクト構造

```
MakeMoneyFromKeiba/
├── src/
│   ├── agents/           # 9つの専門家AI
│   ├── cli/              # CLIツール
│   ├── data_collection/  # データ収集
│   ├── evaluation/       # 評価・バックテスト
│   ├── monitoring/       # 監視・運用
│   ├── orchestrator/     # 予測統合
│   ├── preprocessing/    # データ前処理
│   ├── training/         # モデル訓練
│   └── web/              # Web UI (Streamlit)
├── config/               # 設定ファイル
├── data/                 # データ（Git除外）
├── docker/               # Docker設定
├── docs/                 # ドキュメント
├── models/               # 訓練済みモデル（Git除外）
├── reports/              # レポート出力
├── results/              # 予測結果
└── tests/                # テスト
```

## ドキュメント

- [クイックスタート](docs/user_guide/quickstart.md)
- [CLIリファレンス](docs/user_guide/cli_reference.md)
- [トラブルシューティング](docs/user_guide/troubleshooting.md)
- [設計書](docs/DESIGN.md)

## パフォーマンス目標

- 🎯 回収率: 105-115%
- 🎯 的中率: 40-50%
- 🎯 NDCG@3: 0.65以上

## 開発

### テスト実行

```bash
pytest tests/ -v
```

### コードフォーマット

```bash
black src/ tests/
```

### 型チェック

```bash
mypy src/
```

## ライセンス

MIT License

## 貢献

貢献は歓迎します！詳細は [CONTRIBUTING.md](CONTRIBUTING.md) を参照。

---

*最終更新: 2026-01-10*
