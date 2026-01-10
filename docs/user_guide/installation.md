# インストールガイド

競馬AI予測システムの詳細なインストール手順です。

## 動作環境

- **OS**: macOS, Linux, Windows
- **Python**: 3.10以上
- **メモリ**: 8GB以上推奨
- **ディスク**: 5GB以上の空き容量

## インストール方法

### 1. リポジトリのクローン

```bash
git clone https://github.com/Shusei9595/MakeMoneyFromKeiba.git
cd MakeMoneyFromKeiba
```

### 2. 仮想環境の作成

#### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

#### Windows

```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. 依存関係のインストール

```bash
# 基本インストール
pip install -e .

# 開発用（テスト・リンター含む）
pip install -e ".[dev]"
```

### 4. 設定ファイルの準備

```bash
# 設定ウィザードを使用（推奨）
keiba-ai config wizard

# または手動でコピー
cp config/config.example.yaml config/config.yaml
```

### 5. インストール確認

```bash
keiba-ai --version
# keiba-ai, version 1.0.0

keiba-ai --help
# コマンド一覧が表示されれば成功
```

## Docker を使用する場合

Docker を使用すれば、Python環境を構築せずに利用できます。

### 前提条件

- Docker
- Docker Compose

### インストール

```bash
cd docker
docker-compose build
```

### 動作確認

```bash
docker-compose run keiba-ai keiba-ai --help
```

## トラブルシューティング

### `pip install` でエラーが出る

```bash
# pip を最新版に更新
pip install --upgrade pip

# 再度インストール
pip install -e .
```

### `keiba-ai` コマンドが見つからない

```bash
# 仮想環境がアクティブか確認
which python

# 再インストール
pip install -e .
```

### LightGBM のインストールに失敗する (macOS)

```bash
brew install libomp
pip install lightgbm
```

## 次のステップ

- [クイックスタート](quickstart.md) - 基本的な使い方
- [CLIリファレンス](cli_reference.md) - 全コマンド詳細
