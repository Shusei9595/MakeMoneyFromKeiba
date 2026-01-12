"""
Prediction CLI

コマンドラインから予測を実行するエントリーポイント
"""
import click
import json
from pathlib import Path
from datetime import datetime
import logging
import sys

import pandas as pd
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.orchestrator.agent_manager import AgentManager
from src.orchestrator.weight_optimizer import WeightOptimizer
from src.orchestrator.prediction_orchestrator import PredictionOrchestrator
from src.orchestrator.ev_calculator import EVCalculator
from src.orchestrator.betting_recommender import BettingRecommender


console = Console()


@click.command()
@click.option('--data', required=True, help='入力データCSVファイル')
@click.option('--models', default='models', help='モデルディレクトリ')
@click.option('--strategy', default='balanced', 
              type=click.Choice(['conservative', 'balanced', 'aggressive']),
              help='買い目戦略')
@click.option('--budget', default=10000, type=float, help='予算（円）')
@click.option('--output', default='results', help='出力ディレクトリ')
@click.option('--min-ev', default=0.05, type=float, help='最小EV閾値')
def run_prediction(data, models, strategy, budget, output, min_ev):
    """
    レース予測を実行
    
    使用例:
    python run_prediction.py --data data/processed/test_data.csv --strategy balanced
    """
    console.print("[bold green]━━━ 競馬予測AI ━━━[/bold green]")
    
    # データ読み込み
    console.print(f"📂 データ読み込み中: [cyan]{data}[/cyan]")
    try:
        df = pd.read_csv(data, encoding='utf-8-sig')
    except UnicodeDecodeError:
        df = pd.read_csv(data, encoding='utf-8')
    
    console.print(f"✓ 読み込み完了: [green]{len(df)}[/green] レコード")
    
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
        
        progress.update(task, completed=True)
    
    console.print(f"✓ {len(agent_manager.agents)} エージェントをロード")
    
    # 予測実行
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]予測中...", total=None)
        
        predictions = orchestrator.predict_race(df)
        
        progress.update(task, completed=True)
    
    console.print(f"✓ 予測完了")
    
    # 上位馬表示
    table = Table(title="予測結果 (上位5頭)")
    table.add_column("順位", style="cyan")
    table.add_column("馬番", style="green")
    table.add_column("馬名", style="white")
    table.add_column("スコア", style="yellow")
    table.add_column("勝率", style="green")
    table.add_column("オッズ", style="white")
    
    for i, (_, row) in enumerate(predictions.head(5).iterrows(), 1):
        table.add_row(
            str(i),
            str(int(row.get('horse_number', 0))),
            str(row.get('horse_name', 'Unknown'))[:10],
            f"{row['integrated_score']:.2f}",
            f"{row['win_probability']*100:.1f}%",
            f"{row.get('odds', 0):.1f}"
        )
    
    console.print(table)
    
    # EV計算
    console.print("\n[bold yellow]EV計算中...[/bold yellow]")
    positive_ev_bets = ev_calculator.find_positive_ev_bets(predictions)
    console.print(f"✓ EV > {min_ev*100:.0f}%: [green]{len(positive_ev_bets)}[/green] 件")
    
    # 買い目推奨
    recommendations = recommender.generate_recommendations(
        positive_ev_bets,
        strategy=strategy
    )
    
    # 結果出力
    console.print("\n")
    console.print(recommender.format_output_text(recommendations))
    
    # ファイル保存
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # JSON保存
    json_file = output_dir / f"prediction_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            'predictions': predictions.to_dict('records'),
            'positive_ev_bets': positive_ev_bets,
            'recommendations': recommendations
        }, f, ensure_ascii=False, indent=2, default=str)
    
    # テキスト保存
    txt_file = output_dir / f"betting_{timestamp}.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(recommender.format_output_text(recommendations))
    
    console.print(f"\n✓ 結果保存: [cyan]{json_file}[/cyan]")
    console.print(f"✓ 結果保存: [cyan]{txt_file}[/cyan]")
    console.print("[bold green]━━━ 完了！ ━━━[/bold green]")


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    run_prediction()
