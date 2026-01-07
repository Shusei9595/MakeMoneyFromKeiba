"""
エージェント訓練スクリプト

全9つの専門家AIを訓練する
"""
import click
import pandas as pd
import numpy as np
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
import logging
import sys
import json

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.past_performance_agent import PastPerformanceAgent
from src.agents.distance_adaptability_agent import DistanceAdaptabilityAgent
from src.agents.jockey_trainer_agent import JockeyTrainerAgent
from src.agents.pedigree_agent import PedigreeAgent
from src.agents.race_pace_agent import RacePaceAgent
from src.agents.physical_condition_agent import PhysicalConditionAgent
from src.agents.track_condition_agent import TrackConditionAgent
from src.agents.statistical_pattern_agent import StatisticalPatternAgent
from src.agents.odds_analysis_agent import OddsAnalysisAgent


console = Console()


def get_all_agents():
    """全エージェントのインスタンスを取得"""
    return [
        PastPerformanceAgent(),
        DistanceAdaptabilityAgent(),
        JockeyTrainerAgent(),
        PedigreeAgent(),
        RacePaceAgent(),
        PhysicalConditionAgent(),
        TrackConditionAgent(),
        StatisticalPatternAgent(),
        OddsAnalysisAgent()
    ]


@click.command()
@click.option('--data', required=True, help='訓練データCSVファイル')
@click.option('--validation', default=None, help='検証データCSVファイル（オプション）')
@click.option('--output', default='models', help='モデル保存先ディレクトリ')
@click.option('--n-folds', default=5, help='交差検証のフォールド数')
def train_agents(data, validation, output, n_folds):
    """
    全エージェントを訓練
    
    使用例:
    python train_agents.py --data data/processed/training_data.csv --output models/
    """
    console.print("[bold green]━━━ エージェント訓練開始 ━━━[/bold green]")
    
    # データ読み込み
    console.print(f"📂 訓練データ読み込み中: [cyan]{data}[/cyan]")
    try:
        df_train = pd.read_csv(data, encoding='utf-8-sig')
    except UnicodeDecodeError:
        df_train = pd.read_csv(data, encoding='utf-8')
    
    console.print(f"✓ 読み込み完了: [green]{len(df_train)}[/green] レコード")
    
    # ターゲット確認
    if 'target_score' not in df_train.columns:
        if 'finish_position' in df_train.columns:
            console.print("🎯 ターゲットスコア生成中...")
            from src.agents.base_agent import BaseAgent
            df_train['target_score'] = df_train['finish_position'].apply(
                BaseAgent.create_target_score
            )
        else:
            console.print("[red]エラー: target_score または finish_position が必要です[/red]")
            return
    
    y = df_train['target_score']
    
    # グループ（レースID）
    groups = df_train['race_id'] if 'race_id' in df_train.columns else None
    
    # 全エージェントを取得
    agents = get_all_agents()
    console.print(f"\n📋 訓練対象エージェント: {len(agents)}個")
    
    # 結果を格納
    results = []
    
    # 各エージェントを訓練
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        for agent in agents:
            task = progress.add_task(f"[cyan]{agent.name}...", total=None)
            
            try:
                # 訓練
                metrics = agent.train(df_train, y, groups, n_folds)
                
                # モデル保存
                model_path = agent.save_model(output_dir)
                
                # 結果記録
                results.append({
                    'agent': agent.name,
                    'rmse': metrics['rmse'],
                    'mae': metrics['mae'],
                    'r2': metrics['r2'],
                    'status': '✅ 成功'
                })
                
            except Exception as e:
                console.print(f"[red]エラー: {agent.name} - {e}[/red]")
                results.append({
                    'agent': agent.name,
                    'rmse': None,
                    'mae': None,
                    'r2': None,
                    'status': f'❌ {str(e)[:30]}'
                })
            
            progress.update(task, completed=True)
    
    # 結果サマリー表示
    console.print("\n")
    table = Table(title="訓練結果サマリー")
    table.add_column("エージェント", style="cyan")
    table.add_column("RMSE", style="green")
    table.add_column("MAE", style="green")
    table.add_column("R²", style="green")
    table.add_column("状態", style="yellow")
    
    for r in results:
        table.add_row(
            r['agent'],
            f"{r['rmse']:.4f}" if r['rmse'] else "N/A",
            f"{r['mae']:.4f}" if r['mae'] else "N/A",
            f"{r['r2']:.4f}" if r['r2'] else "N/A",
            r['status']
        )
    
    console.print(table)
    
    # 結果をJSONで保存
    results_file = output_dir / 'training_results.json'
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    console.print(f"\n✓ 結果保存: {results_file}")
    console.print("[bold green]━━━ 完了！ ━━━[/bold green]")


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    train_agents()
