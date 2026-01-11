# クイックスタート

競馬AI予測システムを素早く始めるためのガイドです。

## 1. インストール

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

## 2. 初期設定

```bash
# 対話的設定ウィザード
keiba-ai config wizard
```

または手動で設定ファイルをコピー:
```bash
cp config/config.example.yaml config/config.yaml
```

## 3. データ収集

```bash
# 2024年のデータを収集（約30分）
keiba-ai collect --start-date 2024-01-01 --end-date 2024-12-31 --output data/raw/
```

## 4. データ前処理

```bash
# 収集データを前処理（約10分）
keiba-ai preprocess --input data/raw/ --output data/processed/
```

## 5. モデル訓練

```bash
# 全エージェントを訓練（約60分）
keiba-ai train --data data/processed/training_data.csv --output models/
```

## 6. 予測実行

```bash
# 明日のレースを予測
keiba-ai predict --date 2025-01-12 --strategy balanced --budget 10000
```

## 7. バックテスト

```bash
# 2024年のバックテスト
keiba-ai backtest --start-date 2024-01-01 --end-date 2024-12-31 \
    --strategies balanced --budget 100000 --output reports/backtest_2024.html
```

## 8. Web UI（オプション）

```bash
# ブラウザインターフェースを起動
streamlit run src/web/app.py
# http://localhost:8501 にアクセス
```

## Docker を使用する場合

```bash
cd docker
docker-compose build
docker-compose run keiba-ai keiba-ai predict --date 2025-01-12 --strategy balanced --budget 10000
```

## 次のステップ

- [CLIリファレンス](cli_reference.md) - 全コマンドの詳細
- [トラブルシューティング](troubleshooting.md) - よくある問題と解決策
