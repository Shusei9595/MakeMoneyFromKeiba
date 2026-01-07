# Architecture Decision Records (ADR)

このディレクトリには、競馬AI予測システムのアーキテクチャに関する重要な決定を記録しています。

## ADRとは

Architecture Decision Records (ADR) は、アーキテクチャ上の重要な決定を記録するためのドキュメントです。
各ADRは以下の要素を含みます：

- **コンテキスト**: 決定が必要になった背景
- **決定**: 採用した選択肢
- **ステータス**: 提案中/承認済み/非推奨/置換済み
- **結果**: 決定による影響

## ADR一覧

| ID | タイトル | ステータス | 日付 |
|----|---------|----------|------|
| [ADR-001](./001-multi-agent-architecture.md) | マルチエージェントアーキテクチャの採用 | 承認済み | 2026-01-07 |
| [ADR-002](./002-feature-engineering-strategy.md) | 特徴量エンジニアリング戦略 | 承認済み | 2026-01-07 |
| [ADR-003](./003-data-storage-selection.md) | データストレージの選択 | 承認済み | 2026-01-07 |

## 新しいADRの作成

新しいADRを作成する際は、以下のテンプレートを使用してください：

```markdown
# ADR-XXX: タイトル

## ステータス

提案中 / 承認済み / 非推奨 / 置換済み

## コンテキスト

決定が必要になった背景や問題点を記述

## 検討した選択肢

### 選択肢1
説明、メリット、デメリット

### 選択肢2
説明、メリット、デメリット

## 決定

採用した選択肢とその理由

## 結果

この決定による影響（ポジティブ・ネガティブ両方）
```

## 参考資料

- [ADR GitHub Organization](https://adr.github.io/)
- [Documenting Architecture Decisions - Michael Nygard](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
