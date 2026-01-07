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

1. **過去成績分析AI** (20%) - 直近成績の分析・調子トレンド
2. **距離適性分析AI** (15%) - 距離とコースの相性
3. **騎手・調教師分析AI** (15%) - 人的要因の分析・コンビネーション相性
4. **血統分析AI** (10%) - 血統からの適性判断
5. **レースペース分析AI** (12%) - ペース予測・展開予想
6. **馬体・コンディション分析AI** (8%) - フィジカルコンディション・馬体重
7. **馬場・天候適性分析AI** (10%) - 馬場状態・コース適性
8. **統計パターン分析AI** (5%) - 歴史的パターン・ラップタイム分析
9. **オッズ分析AI** (5%) - 市場分析・オッズの歪み検出

### アーキテクチャ

```
データ収集 → 前処理 → 9つの専門家AI → オーケストレーター → EV計算 → 買い目生成
```

**オーケストレーター**:
- 9つのエージェントのスコアを統合（加重平均）
- 動的重み付け（レース条件に応じた最適化）
- Softmax正規化で勝率・3着内率を算出
- 信頼区間の計算（ブートストラップ法）

**EV計算エンジン**:
- 単勝、複勝、ワイド、馬連、3連複、3連単の全券種対応
- EVランク分類（S: ≥20%, A: 15-20%, B: 10-15%, C: 5-10%）

**買い目推奨システム**:
- ケリー基準による最適購入額算出
- 3つの戦略（Conservative / Balanced / Aggressive）
- リスク分散・資金管理

## セットアップ

### 1. リポジトリのクローン

```bash
git clone https://github.com/Shusei9595/MakeMoneyFromKeiba.git
cd MakeMoneyFromKeiba
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
# config.yaml を編集（データソース、API設定など）
```

## 使い方

### データ収集

```bash
python src/data_collection/run_collection.py --start-date 2024-01-01 --end-date 2024-01-31
```

### データ前処理

```bash
python src/preprocessing/run_preprocessing.py --input-dir data/raw --output-dir data/processed
```

### エージェント訓練

```bash
# 訓練データ準備
python src/training/prepare_training_data.py --input-file data/processed/processed_races.csv

# 9エージェント訓練
python src/training/train_agents.py --data data/processed/training_data.csv --output models/

# エージェント比較レポート生成
python src/analysis/agent_comparison.py --test-data data/processed/test_data.csv --models models/ --output reports/
```

### 予測実行

```bash
# 単一レース予測
python src/orchestrator/run_prediction.py \
    --race-id 202401050811 \
    --strategy balanced \
    --budget 10000 \
    --output results/

# 戦略オプション: conservative / balanced / aggressive
```

### バックテスト

```bash
# 単一戦略のバックテスト
python src/evaluation/run_backtest.py \
    --start-date 2024-01-01 \
    --end-date 2024-12-31 \
    --strategy balanced \
    --budget 100000 \
    --output reports/backtest_2024.html

# 全戦略比較
python src/evaluation/run_backtest.py \
    --start-date 2024-01-01 \
    --end-date 2024-12-31 \
    --compare-strategies \
    --budget 100000 \
    --output reports/strategy_comparison_2024.html
```

### テスト実行

```bash
pytest tests/ -v
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

### カバレッジ確認

```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

## プロジェクト構造

```
MakeMoneyFromKeiba/
├── .github/
│   └── workflows/          # CI/CD設定
├── config/
│   ├── config.yaml         # メイン設定ファイル
│   └── config.example.yaml # 設定テンプレート
├── data/
│   ├── raw/                # 生データ（Git除外）
│   ├── processed/          # 前処理済みデータ（Git除外）
│   └── features/           # 特徴量データ（Git除外）
├── models/                 # 訓練済みモデル（Git除外）
├── reports/                # レポート・分析結果（Git除外）
├── src/
│   ├── agents/             # 9つの専門家AI
│   ├── orchestrator/       # 予測統合・EV計算・買い目生成
│   ├── data_collection/    # データ収集
│   ├── preprocessing/      # データ前処理
│   ├── training/           # モデル訓練
│   ├── evaluation/         # バックテスト・評価
│   └── analysis/           # 分析ツール
├── tests/                  # テストコード
├── notebooks/              # 実験用Notebook（Git除外）
├── logs/                   # ログファイル（Git除外）
└── docs/                   # ドキュメント
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

## ライセンス

MIT License

## 貢献

貢献は歓迎します！詳細は [CONTRIBUTING.md](CONTRIBUTING.md) を参照。

## 参考資料

- [Phase 0: プロジェクト初期設定](docs/phase0_setup.md)
- [Phase 1: データ収集](docs/phase1_data_collection.md)
- [Phase 2: データ前処理](docs/phase2_preprocessing.md)
- [Phase 3: 専門家AIモデル構築](docs/phase3_agents.md)
- [Phase 4: オーケストレーター構築](docs/phase4_orchestrator.md)
- [Phase 5: バックテスト・評価](docs/phase5_evaluation.md)

## お問い合わせ

ご質問・ご提案は [Issues](https://github.com/Shusei9595/MakeMoneyFromKeiba/issues) までお願いします。
