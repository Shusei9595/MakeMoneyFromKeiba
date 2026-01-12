"""
バックテストコマンド
"""
import click
from pathlib import Path
from datetime import datetime

from src.cli.utils.validators import validate_date
from src.cli.utils.progress import create_progress


@click.command()
@click.option('--start-date', required=True, callback=validate_date,
              help='開始日（YYYY-MM-DD形式）')
@click.option('--end-date', required=True, callback=validate_date,
              help='終了日（YYYY-MM-DD形式）')
@click.option('--strategies', default='balanced',
              help='戦略リスト（カンマ区切り）')
@click.option('--budget', type=int, default=100000,
              help='初期資金（デフォルト: 100,000円）')
@click.option('--output', '-o', type=click.Path(),
              help='レポート出力パス')
@click.option('--benchmark', type=str, default=None,
              help='ベンチマーク追加（single_favorite等）')
@click.pass_context
def backtest(ctx, start_date, end_date, strategies, budget, output, benchmark):
    """
    過去データでバックテストを実行
    
    \b
    使用例:
        keiba-ai backtest --start-date 2024-01-01 --end-date 2024-12-31
        keiba-ai backtest --start-date 2024-01-01 --end-date 2024-12-31 --strategies conservative,balanced,aggressive
    """
    from src.evaluation.backtester import Backtester
    import pandas as pd
    
    click.echo(f"📈 バックテスト開始")
    click.echo(f"   期間: {start_date.strftime('%Y-%m-%d')} ～ {end_date.strftime('%Y-%m-%d')}")
    click.echo(f"   初期資金: {budget:,}円")
    
    strategy_list = [s.strip() for s in strategies.split(',')]
    click.echo(f"   戦略: {', '.join(strategy_list)}")
    
    if not output:
        output = f"reports/backtest_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.html"
    
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # データ読み込み
        data_path = Path('data/processed/training_data.csv')
        if not data_path.exists():
            click.echo(f"⚠️ データが見つかりません: {data_path}")
            click.echo("   先に前処理を実行してください")
            raise click.Abort()
        
        df = pd.read_csv(data_path)
        
        # 日付フィルタ
        if 'race_date' in df.columns:
            df['race_date'] = pd.to_datetime(df['race_date'])
            df = df[(df['race_date'] >= start_date) & (df['race_date'] <= end_date)]
        
        click.echo(f"   対象データ: {len(df)} 行")
        
        with create_progress() as progress:
            task = progress.add_task("[cyan]バックテスト中...", total=len(strategy_list))
            
            results = {}
            for strategy in strategy_list:
                # 依存関係を初期化
                from src.orchestrator.agent_manager import AgentManager
                from src.orchestrator.prediction_orchestrator import PredictionOrchestrator
                from src.orchestrator.weight_optimizer import WeightOptimizer
                from src.orchestrator.ev_calculator import EVCalculator
                from src.orchestrator.betting_recommender import BettingRecommender
                
                agent_manager = AgentManager(model_dir='models')
                weight_optimizer = WeightOptimizer()
                orchestrator = PredictionOrchestrator(agent_manager, weight_optimizer)
                ev_calculator = EVCalculator()
                recommender = BettingRecommender(total_budget=budget)
                
                backtester = Backtester(
                    orchestrator=orchestrator,
                    ev_calculator=ev_calculator,
                    recommender=recommender,
                    initial_budget=budget
                )
                result = backtester.run_backtest(df, strategy=strategy)
                results[strategy] = result
                progress.advance(task)

        
        # レポート生成
        report_lines = [
            "<!DOCTYPE html>",
            "<html><head><meta charset='utf-8'>",
            "<title>バックテストレポート</title>",
            "<style>body{font-family:sans-serif;margin:20px;} table{border-collapse:collapse;} th,td{border:1px solid #ddd;padding:8px;}</style>",
            "</head><body>",
            f"<h1>バックテストレポート</h1>",
            f"<p>期間: {start_date.strftime('%Y-%m-%d')} ～ {end_date.strftime('%Y-%m-%d')}</p>",
            f"<p>初期資金: {budget:,}円</p>",
            "<table><tr><th>戦略</th><th>最終資金</th><th>ROI</th><th>的中率</th></tr>"
        ]
        
        for strategy, result in results.items():
            summary = result.get('summary', {})
            final_budget = result.get('final_budget', budget)
            roi = (final_budget / budget - 1) * 100
            hit_rate = summary.get('hit_rate', 0)
            report_lines.append(
                f"<tr><td>{strategy}</td><td>{final_budget:,.0f}円</td>"
                f"<td>{roi:+.1f}%</td><td>{hit_rate:.1f}%</td></tr>"
            )
        
        report_lines.extend(["</table>", "</body></html>"])
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        click.echo(f"✅ バックテスト完了")
        click.echo(f"   レポート: {output_path}")
        
        # サマリー表示
        for strategy, result in results.items():
            roi = (result.get('final_budget', budget) / budget - 1) * 100
            click.echo(f"   [{strategy}] ROI: {roi:+.1f}%")
        
    except Exception as e:
        click.echo(f"❌ エラー: {e}", err=True)
        raise click.Abort()
