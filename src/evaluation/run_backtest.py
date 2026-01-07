"""
Backtest CLI

バックテスト実行のコマンドラインツール
"""
import click
import json
from pathlib import Path
from datetime import datetime
import logging
import sys

import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.orchestrator.agent_manager import AgentManager
from src.orchestrator.weight_optimizer import WeightOptimizer
from src.orchestrator.prediction_orchestrator import PredictionOrchestrator
from src.orchestrator.ev_calculator import EVCalculator
from src.orchestrator.betting_recommender import BettingRecommender
from src.evaluation.backtester import Backtester
from src.evaluation.performance_evaluator import PerformanceEvaluator
from src.evaluation.report_generator import ReportGenerator, generate_text_summary


console = Console()


@click.command()
@click.option('--data', required=True, help='テストデータCSVファイル')
@click.option('--models', default='models', help='モデルディレクトリ')
@click.option('--strategy', default='balanced',
              type=click.Choice(['conservative', 'balanced', 'aggressive']),
              help='買い目戦略')
@click.option('--budget', default=100000, type=float, help='初期予算（円）')
@click.option('--output', default='reports', help='出力ディレクトリ')
@click.option('--min-ev', default=0.05, type=float, help='最小EV閾値')
def run_backtest(data, models, strategy, budget, output, min_ev):
    """
    バックテスト実行
    
    使用例:
    python run_backtest.py --data data/processed/test_data.csv --strategy balanced
    """
    console.print("[bold green]━━━ バックテスト実行 ━━━[/bold green]")
    
    # データ読み込み
    console.print(f"📂 データ読み込み中: [cyan]{data}[/cyan]")
    try:
        df = pd.read_csv(data, encoding='utf-8-sig')
    except UnicodeDecodeError:
        df = pd.read_csv(data, encoding='utf-8')
    
    console.print(f"✓ 読み込み完了: [green]{len(df)}[/green] レコード")
    
    # レースID数を確認
    n_races = df['race_id'].nunique() if 'race_id' in df.columns else 0
    console.print(f"✓ レース数: [green]{n_races}[/green]")
    
    # 初期化
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]システム初期化中...", total=None)
        
        agent_manager = AgentManager(model_dir=models)
        weight_optimizer = WeightOptimizer()
        orchestrator = PredictionOrchestrator(
            agent_manager=agent_manager,
            weight_optimizer=weight_optimizer
        )
        ev_calculator = EVCalculator(min_ev_threshold=min_ev)
        recommender = BettingRecommender(total_budget=budget)
        
        backtester = Backtester(
            orchestrator=orchestrator,
            ev_calculator=ev_calculator,
            recommender=recommender,
            initial_budget=budget
        )
        
        progress.update(task, completed=True)
    
    console.print(f"✓ 初期化完了")
    console.print(f"  戦略: [yellow]{strategy}[/yellow]")
    console.print(f"  初期予算: [yellow]¥{budget:,.0f}[/yellow]")
    
    # バックテスト実行
    console.print("\n[bold yellow]バックテスト実行中...[/bold yellow]")
    
    results = backtester.run_backtest(df, strategy=strategy)
    
    console.print(f"✓ 処理完了: {results['summary'].get('total_races', 0)} レース")
    
    # パフォーマンス評価
    evaluator = PerformanceEvaluator(results)
    metrics = evaluator.calculate_all_metrics()
    
    # テキストサマリー出力
    console.print("\n")
    console.print(generate_text_summary(metrics, strategy))
    
    # レポート生成
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # HTMLレポート
    generator = ReportGenerator(results, metrics)
    html_file = output_dir / f"backtest_{timestamp}.html"
    generator.generate_html_report(str(html_file))
    
    # JSONデータ
    json_file = output_dir / f"backtest_{timestamp}_data.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'metrics': metrics,
            'summary': results['summary'],
            'strategy': strategy,
            'initial_budget': budget,
            'final_budget': results.get('final_budget', 0)
        }, f, ensure_ascii=False, indent=2, default=str)
    
    # テキストサマリー
    txt_file = output_dir / f"backtest_{timestamp}_summary.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(generate_text_summary(metrics, strategy))
    
    console.print(f"\n✓ HTMLレポート: [cyan]{html_file}[/cyan]")
    console.print(f"✓ JSONデータ: [cyan]{json_file}[/cyan]")
    console.print(f"✓ テキストサマリー: [cyan]{txt_file}[/cyan]")
    console.print("[bold green]━━━ 完了！ ━━━[/bold green]")


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    run_backtest()
