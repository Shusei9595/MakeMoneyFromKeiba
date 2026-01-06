# 競馬AI予測システム 🏇

マルチエージェント方式による高精度な競馬予測システム

## 特徴

- 🤖 9つの専門家AIによるアンサンブル予測
- 📊 データ収集から予測まで全自動化
- 💰 期待値(EV)ベースの投資戦略
- 📈 バックテストによる性能検証
- 🔧 使いやすいCLIツール

## システム構成

### 専門家AI（9つ）

1. **前走パフォーマンスAI** (25%) - 直近成績の分析
2. **距離・コース適性AI** (20%) - 距離とコースの相性
3. **騎手・調教師AI** (15%) - 人的要因の分析
4. **血統AI** (10%) - 血統からの適性判断
5. **レース展開AI** (10%) - ペース予測
6. **馬体・調教AI** (10%) - フィジカルコンディション
7. **オッズ分析AI** (5%) - 市場分析
8. **統計パターンAI** (3%) - 歴史的パターン
9. **異常値検出AI** (2%) - リスク検出

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/keiba-ai-prediction-system.git
cd keiba-ai-prediction-system
```

### 2. 仮想環境の作成

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 依存関係のインストール

```bash
pip install -e ".[dev]"
```

### 4. 設定ファイルの準備

```bash
cp config/config.example.yaml config/config.yaml
# config.yaml を編集
```

## 使い方

### データ収集

```bash
keiba-ai collect --date 2024-01-01
```

### データ前処理

```bash
keiba-ai preprocess
```

### モデル訓練

```bash
keiba-ai train
```

### 予測実行

```bash
keiba-ai predict <race_id>
```

### バックテスト

```bash
keiba-ai backtest --start-date 2024-01-01 --end-date 2024-12-31
```

## 開発

### テスト実行

```bash
pytest
```

### コードフォーマット

```bash
black src/ tests/
```

### 型チェック

```bash
mypy src/
```

## プロジェクト構造

```
keiba-ai-prediction-system/
├── src/              # ソースコード
├── tests/            # テスト
├── data/             # データ（Git除外）
├── models/           # モデル（Git除外）
├── config/           # 設定
└── notebooks/        # 実験用（Git除外）
```

## パフォーマンス目標

- 🎯 回収率: 105-115%
- 🎯 的中率: 40-50%
- 🎯 NDCG@3: 0.65以上

## ライセンス

MIT License

## 貢献

貢献は歓迎します！詳細は [CONTRIBUTING.md](CONTRIBUTING.md) を参照。
