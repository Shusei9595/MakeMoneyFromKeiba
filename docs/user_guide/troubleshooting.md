# トラブルシューティング

よくある問題と解決策をまとめています。

---

## データ収集

### Q1: 403エラーが出る

**原因**: netkeiba.comへのアクセスが制限されている

**対処法**:
1. クロール間隔を増やす
   ```bash
   keiba-ai config set scraping.crawl_delay 3.0
   ```
2. 時間を置いて再実行（1時間程度）
3. 一度に収集する期間を短くする

### Q2: データが0件になる

**原因**: 指定した期間にレースがない、またはネットワークエラー

**対処法**:
1. 日付指定を確認（開催日かどうか）
2. `--verbose` オプションで詳細ログを確認
3. ネットワーク接続を確認

---

## 訓練

### Q3: メモリエラーが発生

**原因**: データサイズが大きすぎる

**対処法**:
1. CV分割数を減らす
   ```bash
   keiba-ai train --data data.csv --cv-folds 3
   ```
2. 特定エージェントのみ訓練
   ```bash
   keiba-ai train --data data.csv --agents past_performance,distance
   ```

### Q4: 訓練が途中で止まる

**原因**: モデルの収束に時間がかかっている

**対処法**:
1. `--verbose` で進捗確認
2. データ量を減らしてテスト
3. CPUリソースの確認

---

## 予測

### Q5: 予測結果が表示されない

**原因**: モデルファイルが見つからない

**対処法**:
1. モデルディレクトリを確認
   ```bash
   ls -la models/
   ```
2. 訓練を再実行
   ```bash
   keiba-ai train --data data/processed/training_data.csv
   ```
3. モデルパスを明示
   ```bash
   keiba-ai predict --models /full/path/to/models/ ...
   ```

### Q6: 「データが見つかりません」エラー

**原因**: 予測日のデータが収集されていない

**対処法**:
1. 先にデータを収集
   ```bash
   keiba-ai collect --start-date 2025-01-12 --end-date 2025-01-12
   ```
2. または既存のライブデータファイルを確認
   ```bash
   ls data/live_*.csv
   ```

---

## Docker

### Q7: Docker起動が遅い

**原因**: 初回ビルドに時間がかかる

**対処法**:
- 2回目以降はキャッシュが使われるため高速化
- `docker-compose up -d` でバックグラウンド起動

### Q8: Dockerでボリュームが認識されない

**原因**: パーミッションの問題

**対処法**:
```bash
chmod -R 755 data/ models/ results/
```

---

## Web UI

### Q9: Streamlitが起動しない

**原因**: streamlitがインストールされていない

**対処法**:
```bash
pip install streamlit
streamlit run src/web/app.py
```

### Q10: ページ遷移でエラー

**原因**: pagesディレクトリの構造問題

**対処法**:
- `src/web/pages/` ディレクトリが存在することを確認
- ファイル名が数字で始まっていることを確認

---

## その他

### Q11: ログが多すぎる

**対処法**:
`--verbose` オプションを外す、または設定でログレベルを変更

### Q12: 依存関係のエラー

**対処法**:
```bash
pip install -e ".[dev]" --upgrade
```

---

## サポート

問題が解決しない場合は、GitHubのIssueを作成してください。
その際、以下の情報を含めてください:
- エラーメッセージ（全文）
- 実行したコマンド
- Pythonバージョン (`python --version`)
- OS情報
