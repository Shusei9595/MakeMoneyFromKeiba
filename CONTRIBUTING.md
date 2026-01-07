# 貢献ガイドライン

このプロジェクトへの貢献を歓迎します！

## 開発フロー

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## コーディング規約

- PEP 8に従う
- Black でフォーマット
- 型ヒントを使用
- Docstring を記述（Google Style）

## テスト

- 新機能には必ずテストを追加
- `pytest` で全テストが通ることを確認
- カバレッジ 80% 以上を目標

## コミットメッセージ

```
<type>: <subject>

<body>
```

Type:
- feat: 新機能
- fix: バグ修正
- docs: ドキュメント
- style: フォーマット
- refactor: リファクタリング
- test: テスト
- chore: その他
