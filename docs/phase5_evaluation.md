# Phase 5: バックテスト・評価

## 概要

過去データでシステムの性能を検証し、回収率・的中率・リスク指標を算出します。

## 目標

- ✅ バックテストエンジンの実装
- ✅ パフォーマンス評価システムの構築
- ✅ 戦略比較（Conservative/Balanced/Aggressive）
- ✅ HTMLレポート生成
- ✅ 回収率 > 100%の達成

## 実装構造

```
src/evaluation/
├── __init__.py
├── backtester.py                # バックテストエンジン
├── performance_evaluator.py     # パフォーマンス評価
├── strategy_comparator.py       # 戦略比較
├── report_generator.py          # レポート生成
├── benchmark.py                 # ベンチマーク比較
└── run_backtest.py              # 実行スクリプト
```

## 評価指標

### 収益性指標

| 指標 | 計算式 | 目標 |
|------|--------|------|
| **回収率** | `払戻額 / 投資額 × 100` | > 105% |
| **ROI** | `(払戻額 - 投資額) / 投資額 × 100` | > 5% |
| **純利益** | `払戻額 - 投資額` | プラス |
| **平均利益/レース** | `純利益 / レース数` | プラス |

### 的中率指標

| 指標 | 説明 | 目標 |
|------|------|------|
| **的中率** | `的中数 / 購入数 × 100` | > 30% |
| **券種別的中率** | 各券種の個別的中率 | - |

### リスク指標

| 指標 | 説明 | 目標 |
|------|------|------|
| **最大ドローダウン** | 最大の資産減少率 | < 20% |
| **シャープレシオ** | `(平均リターン - 無リスク金利) / 標準偏差` | > 1.0 |
| **ソルティノレシオ** | 下方リスクのみを考慮 | > 1.5 |
| **勝率** | 利益が出たレースの割合 | > 50% |
| **ペイオフレシオ** | `平均利益 / 平均損失` | > 1.5 |

## Backtester（バックテストエンジン）

### 処理フロー

```
1. 日付範囲内の全レースを時系列順に処理
   ↓
2. 各レースで予測実行
   ↓
3. EV > 閾値の馬券を購入
   ↓
4. 結果確認・払戻計算
   ↓
5. 日次・月次・累積収支を記録
```

### backtester.py

```python
"""
Backtester Module
過去データでシステムを検証
"""
class Backtester:
    def __init__(
        self,
        orchestrator: PredictionOrchestrator,
        ev_calculator: EVCalculator,
        recommender: BettingRecommender,
        initial_budget: float = 100000
    ):
        self.orchestrator = orchestrator
        self.ev_calculator = ev_calculator
        self.recommender = recommender
        self.initial_budget = initial_budget
    
    def run_backtest(
        self,
        start_date: str,
        end_date: str,
        strategy: str = 'balanced'
    ) -> Dict[str, Any]:
        """
        バックテスト実行
        
        Returns:
            {
                'summary': {...},
                'daily_results': [...],
                'monthly_results': [...],
                'race_results': [...],
                'betting_history': [...]
            }
        """
        current_budget = self.initial_budget
        race_results = []
        
        # 日付範囲内の全レースを取得
        races = self._get_races_in_range(start_date, end_date)
        
        for race in tqdm(races):
            # 予測実行
            predictions = self.orchestrator.predict_race(
                race['race_data'], 
                race['horse_data']
            )
            
            # EV計算
            positive_ev_bets = self.ev_calculator.find_positive_ev_bets(
                predictions, 
                race['odds_data']
            )
            
            # 買い目生成
            recommendations = self.recommender.generate_recommendations(
                positive_ev_bets, 
                strategy=strategy
            )
            
            # 購入・払戻計算
            race_result = self._process_race(
                race, 
                recommendations, 
                current_budget
            )
            
            race_results.append(race_result)
            current_budget = race_result['budget_after']
        
        # 結果集計
        summary = self._aggregate_results(race_results)
        
        return {
            'summary': summary,
            'race_results': race_results,
            ...
        }
```

## PerformanceEvaluator（性能評価）

### performance_evaluator.py

```python
class PerformanceEvaluator:
    def calculate_all_metrics(self) -> Dict[str, Any]:
        """全評価指標を一括計算"""
        return {
            'recovery_rate': self.calculate_recovery_rate(),
            'roi': self.calculate_roi(),
            'net_profit': self.calculate_net_profit(),
            'hit_rate': self.calculate_hit_rate(),
            'max_drawdown': self.calculate_max_drawdown(),
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'sortino_ratio': self.calculate_sortino_ratio(),
            'win_rate': self.calculate_win_rate(),
            'payoff_ratio': self.calculate_payoff_ratio(),
            'monthly_win_rate': self.calculate_monthly_win_rate(),
            'longest_winning_streak': self.get_longest_winning_streak(),
            'longest_losing_streak': self.get_longest_losing_streak()
        }
    
    def calculate_sharpe_ratio(
        self, 
        risk_free_rate: float = 0.0
    ) -> float:
        """
        シャープレシオを計算
        
        Sharpe = (平均リターン - 無リスク金利) / 標準偏差
        """
        returns = self._calculate_daily_returns()
        avg_return = returns.mean()
        std_return = returns.std()
        
        if std_return == 0:
            return 0.0
        
        # 年率換算
        sharpe = (avg_return - risk_free_rate / 365) / std_return * np.sqrt(365)
        return sharpe
```

## 戦略別目標

### Conservative戦略

```python
{
    'min_ev': 0.15,
    'kelly_multiplier': 0.25,
    'max_single_bet': 0.20,
    'prefer_bet_types': ['place', 'wide'],
    'target': {
        'recovery_rate': '105-110%',
        'sharpe_ratio': '> 1.0',
        'max_drawdown': '< 10%',
        'monthly_win_rate': '> 70%'
    }
}
```

### Balanced戦略

```python
{
    'min_ev': 0.10,
    'kelly_multiplier': 0.50,
    'max_single_bet': 0.30,
    'prefer_bet_types': ['wide', 'win', 'trifecta'],
    'target': {
        'recovery_rate': '110-120%',
        'sharpe_ratio': '> 1.2',
        'max_drawdown': '< 15%',
        'monthly_win_rate': '> 60%'
    }
}
```

### Aggressive戦略

```python
{
    'min_ev': 0.05,
    'kelly_multiplier': 0.75,
    'max_single_bet': 0.40,
    'prefer_bet_types': ['trifecta', 'trio', 'wide'],
    'target': {
        'recovery_rate': '120-140%',
        'sharpe_ratio': '> 0.8',
        'max_drawdown': '< 25%',
        'monthly_win_rate': '> 50%'
    }
}
```

## HTMLレポート生成

### report_generator.py

```python
class ReportGenerator:
    def generate_html_report(self, output_path: str):
        """HTML形式のレポートを生成"""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>バックテストレポート</title>
        </head>
        <body>
            <h1>競馬予測AI - バックテストレポート</h1>
            
            <!-- エグゼクティブサマリー -->
            <section>
                <h2>エグゼクティブサマリー</h2>
                <div class="summary-box">
                    <div class="metric">
                        <h3>回収率</h3>
                        <p>{self.metrics['recovery_rate']}%</p>
                    </div>
                    <!-- 他の指標 -->
                </div>
            </section>
            
            <!-- 資産曲線グラフ -->
            <section>
                <h2>資産曲線</h2>
                <img src="data:image/png;base64,{equity_curve_img}" />
            </section>
            
            <!-- 月次パフォーマンスグラフ -->
            <!-- ドローダウングラフ -->
            <!-- 取引履歴テーブル -->
        </body>
        </html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
```

### レポート内容

1. **エグゼクティブサマリー**
   - 主要4指標（回収率、純利益、シャープレシオ、最大DD）

2. **資産曲線グラフ**
   - 初期資金からの推移

3. **月次パフォーマンス**
   - 月ごとの収支

4. **券種別分析**
   - 単勝、複勝、ワイド等の成績比較

5. **ドローダウン分析**
   - 資産減少期間の可視化

6. **リターン分布**
   - ヒストグラムで確率分布を表示

7. **詳細取引履歴**
   - 全購入・的中記録

## バックテスト実行

### コマンド例

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

# ベンチマーク比較付き
python src/evaluation/run_backtest.py \
    --start-date 2024-01-01 \
    --end-date 2024-12-31 \
    --strategy balanced \
    --include-benchmarks \
    --budget 100000 \
    --output reports/full_evaluation_2024.html
```

### 実行結果例

```
=================================================
       バックテスト実行中
=================================================
期間: 2024-01-01 〜 2024-12-31
戦略: balanced
初期予算: ¥100,000

処理中: [████████████████████] 500/500 レース (100%)

-------------------------------------------------
【結果サマリー】
-------------------------------------------------
総レース数: 500
購入回数: 1,245
的中回数: 405
的中率: 32.5%

総投資額: ¥1,000,000
総払戻額: ¥1,085,000
純利益: ¥85,000
回収率: 108.5%
ROI: +8.5%

シャープレシオ: 1.45
ソルティノレシオ: 2.13
最大ドローダウン: -15.2% (2024-03-15 〜 2024-04-20)

勝率（利益レース）: 58.3%
ペイオフレシオ: 1.8
月次勝率: 75.0% (9勝3敗)

最大連勝: 12レース
最大連敗: 5レース

-------------------------------------------------
レポート生成中...
HTML レポート: reports/backtest_2024.html
JSON データ: reports/backtest_2024_data.json

✅ バックテスト完了！
=================================================
```

## テスト

```bash
# 評価システムのテスト
pytest tests/test_evaluation.py -v

# カバレッジ確認
pytest tests/test_evaluation.py --cov=src/evaluation
```

## 成功基準

- ✅ バックテストが正常に実行される
- ✅ 回収率が目標範囲内（Balanced: 110-120%）
- ✅ シャープレシオ > 1.0
- ✅ HTMLレポートが視覚的に分かりやすい
- ✅ 全テストがパス

## ベンチマーク比較

### ベースライン戦略

1. **ランダム購入**: ランダムに馬券を購入
2. **人気順**: 1番人気の単勝を購入
3. **オッズ逆張り**: 高オッズの馬を購入
4. **全頭購入**: 全ての馬に均等に賭ける

### 統計的有意性検定

```python
from scipy import stats

def statistical_significance_test(
    ai_returns: List[float],
    baseline_returns: List[float]
) -> Dict[str, Any]:
    """t検定で統計的有意性を確認"""
    t_statistic, p_value = stats.ttest_ind(ai_returns, baseline_returns)
    
    return {
        't_statistic': t_statistic,
        'p_value': p_value,
        'is_significant': p_value < 0.05,
        'conclusion': 'AI戦略が統計的に有意に優れている' if p_value < 0.05 else '有意差なし'
    }
```

## トラブルシューティング

### バックテストが遅い

```bash
# レース数を制限
python run_backtest.py --max-races 100
```

### 回収率が低い

- EV閾値を上げる（0.10 → 0.15）
- 戦略をConservativeに変更
- 特定券種に絞る

## 次のステップ

Phase 5が完了したら、以下を実施してください：

1. **実データでの検証**
   - 実際のレースでシステムを運用
   - リアルタイムパフォーマンスの監視

2. **継続的な改善**
   - エージェントの再訓練
   - 特徴量の追加・削除
   - ハイパーパラメータの最適化

3. **Phase 6（運用準備）**
   - CLIツールの実装
   - ドキュメント整備
   - デプロイ準備

## 参考資料

- [Backtesting.py Documentation](https://kernc.github.io/backtesting.py/)
- [Quantitative Trading Strategies](https://www.quantstart.com/)
- [Risk Management in Trading](https://www.investopedia.com/articles/trading/09/risk-management.asp)
