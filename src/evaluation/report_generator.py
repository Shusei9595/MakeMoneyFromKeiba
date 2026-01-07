"""
Report Generator Module

HTMLレポートを生成する
"""
from typing import Dict, List, Any
from pathlib import Path
from datetime import datetime
import logging
import base64
import io

import numpy as np
import pandas as pd

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class ReportGenerator:
    """
    レポート生成クラス
    
    責任:
    - HTML形式の詳細レポート生成
    - グラフ・チャートの可視化
    """
    
    def __init__(
        self,
        backtest_results: Dict[str, Any],
        performance_metrics: Dict[str, Any]
    ):
        """
        Args:
            backtest_results: バックテスト結果
            performance_metrics: パフォーマンス指標
        """
        self.results = backtest_results
        self.metrics = performance_metrics
        self.race_results = backtest_results.get('race_results', [])
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def generate_html_report(self, output_path: str) -> None:
        """HTML形式のレポートを生成"""
        
        html = self._build_html()
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        self.logger.info(f"Report generated: {output_path}")
    
    def _build_html(self) -> str:
        """HTMLを構築"""
        
        equity_chart = self.plot_equity_curve() if HAS_MATPLOTLIB else ""
        monthly_chart = self.plot_monthly_performance() if HAS_MATPLOTLIB else ""
        
        html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>競馬予測AI - バックテストレポート</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Hiragino Sans', 'Meiryo', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #eee;
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        h1 {{
            font-size: 2rem;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .subtitle {{ color: #888; margin-bottom: 30px; }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        .metric-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .metric-card h3 {{ color: #888; font-size: 0.9rem; margin-bottom: 10px; }}
        .metric-card .value {{
            font-size: 2rem;
            font-weight: bold;
            background: linear-gradient(90deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .metric-card.positive .value {{ color: #00ff88; -webkit-text-fill-color: #00ff88; }}
        .metric-card.negative .value {{ color: #ff4466; -webkit-text-fill-color: #ff4466; }}
        section {{
            background: rgba(255,255,255,0.03);
            border-radius: 15px;
            padding: 25px;
            margin-bottom: 30px;
            border: 1px solid rgba(255,255,255,0.05);
        }}
        section h2 {{
            font-size: 1.3rem;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        th {{ color: #888; font-weight: normal; }}
        .chart {{ margin: 20px 0; text-align: center; }}
        .chart img {{ max-width: 100%; border-radius: 10px; }}
        .footer {{ text-align: center; color: #666; margin-top: 40px; font-size: 0.9rem; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏇 競馬予測AI - バックテストレポート</h1>
        <p class="subtitle">
            生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
            戦略: {self.results.get('strategy', 'balanced')}
        </p>
        
        <div class="summary-grid">
            <div class="metric-card {'positive' if self.metrics.get('roi', 0) >= 0 else 'negative'}">
                <h3>回収率</h3>
                <p class="value">{self.metrics.get('recovery_rate', 0):.1f}%</p>
            </div>
            <div class="metric-card {'positive' if self.metrics.get('net_profit', 0) >= 0 else 'negative'}">
                <h3>純利益</h3>
                <p class="value">¥{self.metrics.get('net_profit', 0):,.0f}</p>
            </div>
            <div class="metric-card">
                <h3>シャープレシオ</h3>
                <p class="value">{self.metrics.get('sharpe_ratio', 0):.2f}</p>
            </div>
            <div class="metric-card">
                <h3>最大DD</h3>
                <p class="value">{self.metrics.get('max_drawdown', 0):.1f}%</p>
            </div>
        </div>
        
        <section>
            <h2>📊 パフォーマンス指標</h2>
            <table>
                <tr><th>指標</th><th>値</th></tr>
                <tr><td>総レース数</td><td>{self.metrics.get('total_races', 0)}</td></tr>
                <tr><td>総購入数</td><td>{self.metrics.get('total_bets', 0)}</td></tr>
                <tr><td>総的中数</td><td>{self.metrics.get('total_hits', 0)}</td></tr>
                <tr><td>的中率</td><td>{self.metrics.get('hit_rate', 0):.1f}%</td></tr>
                <tr><td>勝率（利益レース）</td><td>{self.metrics.get('win_rate', 0):.1f}%</td></tr>
                <tr><td>ペイオフレシオ</td><td>{self.metrics.get('payoff_ratio', 0):.2f}</td></tr>
                <tr><td>最大連勝</td><td>{self.metrics.get('longest_winning_streak', 0)}</td></tr>
                <tr><td>最大連敗</td><td>{self.metrics.get('longest_losing_streak', 0)}</td></tr>
            </table>
        </section>
        
        {f'<section><h2>📈 資産曲線</h2><div class="chart"><img src="data:image/png;base64,{equity_chart}" /></div></section>' if equity_chart else ''}
        
        {f'<section><h2>📅 月次パフォーマンス</h2><div class="chart"><img src="data:image/png;base64,{monthly_chart}" /></div></section>' if monthly_chart else ''}
        
        <section>
            <h2>💰 収支サマリー</h2>
            <table>
                <tr><th>項目</th><th>金額</th></tr>
                <tr><td>総投資額</td><td>¥{self.metrics.get('total_investment', 0):,.0f}</td></tr>
                <tr><td>総払戻額</td><td>¥{self.metrics.get('total_payout', 0):,.0f}</td></tr>
                <tr><td>純利益</td><td>¥{self.metrics.get('net_profit', 0):,.0f}</td></tr>
                <tr><td>ROI</td><td>{self.metrics.get('roi', 0):.1f}%</td></tr>
            </table>
        </section>
        
        <p class="footer">Generated by MakeMoneyFromKeiba AI System</p>
    </div>
</body>
</html>
"""
        return html
    
    def plot_equity_curve(self) -> str:
        """資産曲線をプロット"""
        if not HAS_MATPLOTLIB or not self.race_results:
            return ""
        
        equity = [0]
        for race in self.race_results:
            equity.append(equity[-1] + race.get('profit', 0))
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(equity, color='#00d4ff', linewidth=2)
        ax.fill_between(range(len(equity)), equity, alpha=0.3, color='#00d4ff')
        ax.axhline(y=0, color='#888', linestyle='--', alpha=0.5)
        ax.set_xlabel('Race', color='#888')
        ax.set_ylabel('Cumulative Profit (¥)', color='#888')
        ax.set_title('Equity Curve', color='#eee')
        ax.set_facecolor('#1a1a2e')
        fig.patch.set_facecolor('#1a1a2e')
        ax.tick_params(colors='#888')
        ax.spines['bottom'].set_color('#444')
        ax.spines['left'].set_color('#444')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='#1a1a2e')
        plt.close(fig)
        buf.seek(0)
        
        return base64.b64encode(buf.getvalue()).decode('utf-8')
    
    def plot_monthly_performance(self) -> str:
        """月次パフォーマンスをプロット"""
        if not HAS_MATPLOTLIB or not self.race_results:
            return ""
        
        # 月次集計
        monthly = {}
        for race in self.race_results:
            date_str = race.get('race_date', '')
            if date_str:
                month = date_str[:7]  # YYYY-MM
                monthly[month] = monthly.get(month, 0) + race.get('profit', 0)
        
        if not monthly:
            return ""
        
        months = sorted(monthly.keys())
        profits = [monthly[m] for m in months]
        colors = ['#00ff88' if p >= 0 else '#ff4466' for p in profits]
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.bar(range(len(months)), profits, color=colors, alpha=0.8)
        ax.axhline(y=0, color='#888', linestyle='--', alpha=0.5)
        ax.set_xticks(range(len(months)))
        ax.set_xticklabels([m[5:] for m in months], rotation=45)
        ax.set_xlabel('Month', color='#888')
        ax.set_ylabel('Profit (¥)', color='#888')
        ax.set_title('Monthly Performance', color='#eee')
        ax.set_facecolor('#1a1a2e')
        fig.patch.set_facecolor('#1a1a2e')
        ax.tick_params(colors='#888')
        ax.spines['bottom'].set_color('#444')
        ax.spines['left'].set_color('#444')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='#1a1a2e')
        plt.close(fig)
        buf.seek(0)
        
        return base64.b64encode(buf.getvalue()).decode('utf-8')


def generate_text_summary(metrics: Dict[str, Any], strategy: str) -> str:
    """テキスト形式のサマリーを生成"""
    lines = [
        "=" * 50,
        "       競馬予測AI - バックテスト結果",
        "=" * 50,
        f"戦略: {strategy}",
        "",
        "-" * 50,
        "【パフォーマンス】",
        "-" * 50,
        f"回収率: {metrics.get('recovery_rate', 0):.1f}%",
        f"ROI: {metrics.get('roi', 0):+.1f}%",
        f"純利益: ¥{metrics.get('net_profit', 0):,.0f}",
        "",
        f"的中率: {metrics.get('hit_rate', 0):.1f}%",
        f"勝率: {metrics.get('win_rate', 0):.1f}%",
        "",
        "-" * 50,
        "【リスク指標】",
        "-" * 50,
        f"シャープレシオ: {metrics.get('sharpe_ratio', 0):.2f}",
        f"ソルティノレシオ: {metrics.get('sortino_ratio', 0):.2f}",
        f"最大ドローダウン: {metrics.get('max_drawdown', 0):.1f}%",
        "",
        "-" * 50,
        "【統計】",
        "-" * 50,
        f"総レース数: {metrics.get('total_races', 0)}",
        f"総購入数: {metrics.get('total_bets', 0)}",
        f"総的中数: {metrics.get('total_hits', 0)}",
        f"最大連勝: {metrics.get('longest_winning_streak', 0)}",
        f"最大連敗: {metrics.get('longest_losing_streak', 0)}",
        "=" * 50
    ]
    
    return '\n'.join(lines)
