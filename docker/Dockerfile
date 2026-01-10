FROM python:3.10-slim

# 作業ディレクトリ
WORKDIR /app

# システム依存パッケージ
RUN apt-get update && apt-get install -y \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Python依存関係をインストール
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# アプリケーションコードをコピー
COPY . .

# CLIを再インストール（editable mode）
RUN pip install -e .

# 環境変数
ENV PYTHONUNBUFFERED=1
ENV KEIBA_CONFIG=/app/config/config.yaml

# ボリュームマウント用ディレクトリ
VOLUME ["/app/data", "/app/models", "/app/results", "/app/reports"]

# エントリーポイント
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]

# デフォルトコマンド
CMD ["keiba-ai", "--help"]
