# Phase 0: プロジェクト初期設定

## 概要

競馬AI予測システム「MakeMoneyFromKeiba」の開発環境とプロジェクト構造を構築します。

## 目標

- ✅ プロジェクト構造の確立
- ✅ GitHub連携の設定
- ✅ CI/CDパイプラインの構築
- ✅ 開発環境の標準化

## プロジェクト構造

```
MakeMoneyFromKeiba/
├── .github/
│   └── workflows/
│       ├── ci.yml              # CI/CD設定
│       └── test.yml            # テスト実行
├── config/
│   ├── config.yaml             # メイン設定ファイル
│   ├── config.example.yaml     # 設定テンプレート
│   └── scraping_config.yaml    # データ収集設定
├── data/
│   ├── raw/                    # 生データ（Git除外）
│   ├── processed/              # 前処理済み（Git除外）
│   └── features/               # 特徴量（Git除外）
├── models/
│   └── .gitkeep                # モデルファイル保存先
├── src/
│   ├── agents/                 # 専門家AIモジュール
│   ├── orchestrator/           # 予測統合システム
│   ├── data_collection/        # データ収集
│   ├── preprocessing/          # 前処理
│   ├── training/               # モデル訓練
│   ├── evaluation/             # バックテスト
│   └── analysis/               # 分析ツール
├── tests/                      # テストコード
├── notebooks/                  # Jupyter Notebook（Git除外）
├── logs/                       # ログファイル（Git除外）
├── reports/                    # レポート出力（Git除外）
├── docs/                       # ドキュメント
├── .gitignore                  # Git除外設定
├── .gitattributes              # Git属性設定
├── pyproject.toml              # プロジェクト設定
├── requirements.txt            # 依存関係
├── setup.py                    # セットアップスクリプト
├── README.md                   # プロジェクト説明
├── CONTRIBUTING.md             # 貢献ガイド
└── LICENSE                     # ライセンス
```

## 技術スタック

### 言語・フレームワーク
- **Python 3.11+**: メイン開発言語
- **pandas, numpy**: データ処理
- **scikit-learn**: 機械学習基盤
- **LightGBM, XGBoost**: 勾配ブースティング

### データ収集
- **requests, beautifulsoup4**: Webスクレイピング
- **selenium**: 動的コンテンツ取得

### 開発ツール
- **pytest**: テストフレームワーク
- **black**: コードフォーマッター
- **mypy**: 型チェック
- **pre-commit**: Git フック

### 可視化
- **matplotlib, seaborn**: グラフ作成
- **plotly**: インタラクティブグラフ

## セットアップ手順

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
# 開発環境（テスト・フォーマッター含む）
pip install -e ".[dev]"

# 本番環境（最小限）
pip install -e .
```

### 4. 設定ファイルの準備

```bash
# 設定テンプレートをコピー
cp config/config.example.yaml config/config.yaml

# 設定を編集
vim config/config.yaml
```

### 5. Git設定

```bash
# pre-commit フックのインストール
pre-commit install

# Git ユーザー設定
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

## 設定ファイルの構造

### config/config.yaml

```yaml
# データソース設定
data_source:
  url: "https://db.netkeiba.com/"
  api_key: "YOUR_API_KEY"  # 必要に応じて設定

# データベース設定
database:
  type: "sqlite"  # sqlite / postgresql
  path: "data/keiba.db"

# 前処理設定
preprocessing:
  missing_value_strategy: "median"
  outlier_threshold: 3.0
  normalization: "standard"

# エージェント設定
agents:
  past_performance:
    weight: 0.20
    model_type: "lightgbm"
  distance_adaptability:
    weight: 0.15
    model_type: "lightgbm"
  # ... 他のエージェント

# オーケストレーター設定
orchestrator:
  parallel_execution: true
  max_workers: 9
  cache_enabled: true
  cache_ttl: 3600

# 買い目生成設定
betting:
  min_ev: 0.05
  kelly_fraction: 0.5
  max_bet_fraction: 0.3
  min_bet_amount: 100

# ログ設定
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "logs/app.log"
```

## CI/CD設定

### .github/workflows/ci.yml

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -e ".[dev]"
    
    - name: Run tests
      run: |
        pytest tests/ -v --cov=src --cov-report=xml
    
    - name: Code formatting check
      run: |
        black --check src/ tests/
    
    - name: Type check
      run: |
        mypy src/
```

## 開発ワークフロー

### ブランチ戦略

- **main**: 本番環境（安定版）
- **develop**: 開発環境（統合テスト）
- **feature/**: 機能開発ブランチ
- **hotfix/**: 緊急修正ブランチ

### コミットメッセージ規約

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `style`: フォーマット
- `refactor`: リファクタリング
- `test`: テスト追加
- `chore`: ビルド・設定

**例**:
```
feat(agents): Add PastPerformanceAgent implementation

- Implement BaseAgent abstract class
- Add LightGBM regression model
- Add 10-point scoring system
```

## 開発ツールの使い方

### テスト実行

```bash
# 全テスト実行
pytest

# 詳細出力
pytest -v

# カバレッジ付き
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

### コードフォーマット

```bash
# 自動フォーマット
black src/ tests/

# チェックのみ
black --check src/ tests/
```

### 型チェック

```bash
mypy src/
```

### Linting

```bash
flake8 src/ tests/
```

## トラブルシューティング

### 依存関係のインストールエラー

```bash
# pipのアップグレード
pip install --upgrade pip

# キャッシュクリア
pip cache purge

# 再インストール
pip install -e ".[dev]" --force-reinstall
```

### 仮想環境のリセット

```bash
deactivate
rm -rf venv/
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

## 次のステップ

Phase 0が完了したら、[Phase 1: データ収集](phase1_data_collection.md) に進んでください。

## 参考資料

- [Python 公式ドキュメント](https://docs.python.org/3/)
- [pytest ドキュメント](https://docs.pytest.org/)
- [black ドキュメント](https://black.readthedocs.io/)
- [GitHub Actions ドキュメント](https://docs.github.com/en/actions)
