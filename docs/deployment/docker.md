# Dockerデプロイメントガイド

本ドキュメントでは、競馬AI予測システムをDockerで実行する方法を説明します。

## 前提条件

- Docker 20.10以上
- Docker Compose 2.0以上

## クイックスタート

### 1. イメージのビルド

```bash
cd docker
docker-compose build
```

### 2. CLIの実行

```bash
# ヘルプ表示
docker-compose run keiba-ai keiba-ai --help

# データ収集
docker-compose run keiba-ai keiba-ai collect \
    --start-date 2024-01-01 \
    --end-date 2024-12-31

# 予測実行
docker-compose run keiba-ai keiba-ai predict \
    --date 2025-01-11 \
    --strategy balanced \
    --budget 10000
```

### 3. Web UIの起動

```bash
# Web UIを起動
docker-compose up web-ui

# ブラウザで http://localhost:8501 にアクセス
```

## ディレクトリ構成

```
docker/
├── Dockerfile          # CLI用Dockerfile
├── Dockerfile.web      # Web UI用Dockerfile
├── docker-compose.yml  # オーケストレーション
├── .dockerignore       # ビルド除外ファイル
└── entrypoint.sh       # 起動スクリプト
```

## docker-compose.yml 解説

```yaml
version: '3.8'

services:
  keiba-ai:
    build:
      context: ..
      dockerfile: docker/Dockerfile
    volumes:
      - ../data:/app/data       # データ永続化
      - ../models:/app/models   # モデル永続化
      - ../results:/app/results # 結果永続化
      - ../config:/app/config   # 設定ファイル

  web-ui:
    build:
      context: ..
      dockerfile: docker/Dockerfile.web
    ports:
      - "8501:8501"
    volumes:
      - ../data:/app/data
      - ../models:/app/models
```

## ボリュームマウント

| ホスト | コンテナ | 説明 |
|--------|---------|------|
| `data/` | `/app/data` | レースデータ |
| `models/` | `/app/models` | 訓練済みモデル |
| `results/` | `/app/results` | 予測結果 |
| `reports/` | `/app/reports` | レポート |
| `config/` | `/app/config` | 設定ファイル |

## 環境変数

| 変数 | 説明 | デフォルト |
|------|------|-----------|
| `KEIBA_CONFIG` | 設定ファイルパス | `/app/config/config.yaml` |
| `PYTHONUNBUFFERED` | 出力バッファリング | `1` |

## よくある操作

### コンテナに入る

```bash
docker-compose run keiba-ai /bin/bash
```

### ログ確認

```bash
docker-compose logs web-ui
docker-compose logs -f web-ui  # リアルタイム
```

### クリーンアップ

```bash
# 停止
docker-compose down

# イメージ削除
docker-compose down --rmi all

# ボリューム削除（注意: データが消えます）
docker-compose down -v
```

## トラブルシューティング

### ビルドが遅い

`.dockerignore` で大容量ファイルを除外していることを確認してください。

### ポートが使用中

```bash
# 別のポートで起動
docker-compose run -p 8502:8501 web-ui
```

### 権限エラー

```bash
# ホスト側のディレクトリに書き込み権限を付与
chmod -R 777 data/ models/ results/
```

## 本番環境向け設定

### セキュリティ

1. 非rootユーザーでの実行
2. 読み取り専用マウントの活用
3. ネットワークの分離

### パフォーマンス

1. マルチステージビルドでイメージ軽量化
2. レイヤーキャッシュの活用
3. 軽量ベースイメージ（-slim）の使用
