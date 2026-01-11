"""
モデル訓練コマンド
"""
import click
from pathlib import Path

from src.cli.utils.progress import create_progress


@click.command()
@click.option('--data', '-d', required=True,
              type=click.Path(exists=True), help='訓練データパス')
@click.option('--output', '-o', default='models/',
              type=click.Path(), help='モデル出力ディレクトリ')
@click.option('--agents', type=str, default=None,
              help='訓練対象エージェント（カンマ区切り）')
@click.option('--optimize', is_flag=True,
              help='ハイパーパラメータ最適化を実行')
@click.option('--cv-folds', default=5, type=int,
              help='Cross-Validation分割数（デフォルト: 5）')
@click.pass_context
def train(ctx, data, output, agents, optimize, cv_folds):
    """
    専門家AIモデルを訓練
    
    \b
    使用例:
        keiba-ai train --data data/processed/training_data.csv
        keiba-ai train --data data/processed/training_data.csv --agents past_performance,distance
        keiba-ai train --data data/processed/training_data.csv --optimize
    """
    from src.training.train_agents import AgentTrainer
    import pandas as pd
    
    click.echo(f"🧠 モデル訓練開始")
    click.echo(f"   データ: {data}")
    click.echo(f"   出力先: {output}")
    
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # エージェントリスト
    all_agents = [
        'past_performance', 'distance', 'track_condition',
        'jockey_trainer', 'pace', 'pedigree',
        'weight', 'odds_analysis', 'class_level'
    ]
    
    if agents:
        target_agents = [a.strip() for a in agents.split(',')]
        invalid = set(target_agents) - set(all_agents)
        if invalid:
            click.echo(f"⚠️ 無効なエージェント: {invalid}", err=True)
            click.echo(f"   有効なエージェント: {', '.join(all_agents)}")
            raise click.Abort()
    else:
        target_agents = all_agents
    
    click.echo(f"   対象エージェント: {len(target_agents)} 個")
    
    try:
        # データ読み込み
        df = pd.read_csv(data)
        click.echo(f"   データサイズ: {len(df)} 行")
        
        # トレーナー初期化
        trainer = AgentTrainer(output_dir=str(output_path))
        
        with create_progress() as progress:
            task = progress.add_task("[cyan]訓練中...", total=len(target_agents))
            
            for agent_name in target_agents:
                trainer.train_single_agent(
                    agent_name=agent_name,
                    df=df,
                    optimize=optimize,
                    cv_folds=cv_folds
                )
                progress.advance(task)
        
        click.echo(f"✅ 訓練完了")
        click.echo(f"   モデル保存先: {output_path}")
        
    except Exception as e:
        click.echo(f"❌ エラー: {e}", err=True)
        raise click.Abort()
