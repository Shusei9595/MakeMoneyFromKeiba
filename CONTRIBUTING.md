# 貢献ガイド

競馬AI予測システムへの貢献をお考えいただきありがとうございます！

## 開発環境のセットアップ

```bash
# リポジトリをフォーク後、クローン
git clone https://github.com/YOUR_USERNAME/MakeMoneyFromKeiba.git
cd MakeMoneyFromKeiba

# 仮想環境を作成
python -m venv venv
source venv/bin/activate

# 開発用依存関係をインストール
pip install -e ".[dev]"
```

## コーディング規約

- **フォーマット**: Black（line-length: 100）
- **型ヒント**: mypy でチェック
- **ドキュメント**: Docstring必須（Google Style）

## プルリクエストの手順

1. 新しいブランチを作成
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. 変更をコミット
   ```bash
   git commit -m "feat: 機能の説明"
   ```

3. テストを実行
   ```bash
   pytest tests/ -v
   ```

4. プッシュしてPRを作成
   ```bash
   git push origin feature/your-feature-name
   ```

## コミットメッセージ規約

| プレフィックス | 用途 |
|---------------|------|
| `feat:` | 新機能 |
| `fix:` | バグ修正 |
| `docs:` | ドキュメント |
| `refactor:` | リファクタリング |
| `test:` | テスト追加 |

## Issue報告

バグ報告や機能要望は GitHub Issue でお願いします。

テンプレートに従って以下を記載してください：
- 問題の詳細
- 再現手順
- 期待される動作
- 環境情報
