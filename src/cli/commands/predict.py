"""
予測コマンド
"""
import click
from pathlib import Path
from datetime import datetime

from src.cli.utils.validators import validate_date, validate_race_id, validate_strategy
from src.cli.utils.progress import create_progress


@click.command()
@click.option('--race-id', type=str, help='レースID（例: 202401050811）')
@click.option('--date', callback=validate_date, help='日付（YYYY-MM-DD形式）')
@click.option('--strategy', type=click.Choice(['conservative', 'balanced', 'aggressive']),
              required=True, help='戦略')
@click.option('--budget', type=int, required=True, help='予算（円）')
@click.option('--models', type=click.Path(exists=True), default='models/',
              help='モデルディレクトリ')
@click.option('--output', '-o', type=click.Path(), default='results/',
              help='出力先')
@click.option('--format', 'output_format', type=click.Choice(['text', 'json', 'html']),
              default='text', help='出力形式')
@click.pass_context
def predict(ctx, race_id, date, strategy, budget, models, output, output_format):
    """
    レース予測を実行
    
    \b
    使用例:
        keiba-ai predict --race-id 202401050811 --strategy balanced --budget 10000
        keiba-ai predict --date 2024-12-31 --strategy aggressive --budget 50000
    """
    import pandas as pd
    from src.orchestrator.agent_manager import AgentManager
    from src.orchestrator.weight_optimizer import WeightOptimizer
    from src.orchestrator.prediction_orchestrator import PredictionOrchestrator
    from src.orchestrator.ev_calculator import EVCalculator
    from src.orchestrator.betting_recommender import BettingRecommender
    
    # 入力検証
    if not race_id and not date:
        raise click.UsageError('--race-id または --date のいずれかを指定してください')
    
    if race_id and date:
        raise click.UsageError('--race-id と --date は同時に指定できません')
    
    if race_id:
        validate_race_id(race_id)
    
    click.echo(f"🎯 予測開始")
    click.echo(f"   戦略: {strategy}")
    click.echo(f"   予算: {budget:,}円")
    
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        # モデル読み込み
        agent_manager = AgentManager(model_dir=models)
        weight_optimizer = WeightOptimizer()
        orchestrator = PredictionOrchestrator(
            agent_manager=agent_manager,
            weight_optimizer=weight_optimizer
        )
        ev_calculator = EVCalculator(min_ev_threshold=0.05)
        recommender = BettingRecommender(total_budget=budget)
        
        with create_progress() as progress:
            task = progress.add_task("[cyan]予測中...", total=None)
            
            if race_id:
                # 単一レース予測（簡易版）
                click.echo(f"   レースID: {race_id}")
                # TODO: 単一レース用データ取得
                click.echo("⚠️ 単一レース予測は未実装です。--date オプションを使用してください。")
                return
            else:
                # 日付指定予測
                date_str = date.strftime('%Y-%m-%d')
                click.echo(f"   日付: {date_str}")
                
                # データ読み込み（存在する場合）
                data_file = Path(f'data/live_{date.strftime("%Y%m%d")}.csv')
                if not data_file.exists():
                    click.echo(f"⚠️ データが見つかりません: {data_file}")
                    click.echo("   先にデータ収集を実行してください")
                    raise click.Abort()
                
                df = pd.read_csv(data_file)
                races = df['race_id'].unique()
                
                results = []
                for rid in races:
                    race_df = df[df['race_id'] == rid].copy()
                    predictions = orchestrator.predict_race(race_df)
                    positive_ev = ev_calculator.find_positive_ev_bets(predictions)
                    recommendations = recommender.generate_recommendations(positive_ev, strategy=strategy)
                    results.append({
                        'race_id': rid,
                        'recommendations': recommendations
                    })
                
                progress.update(task, completed=True)
        
        # 結果保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = output_path / f'prediction_{date.strftime("%Y%m%d")}_{timestamp}.txt'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"予測結果: {date_str}\n")
            f.write(f"戦略: {strategy}, 予算: {budget:,}円\n")
            f.write("=" * 50 + "\n\n")
            
            for r in results:
                f.write(f"レース: {r['race_id']}\n")
                f.write(recommender.format_output_text(r['recommendations']))
                f.write("\n")
        
        click.echo(f"✅ 予測完了")
        click.echo(f"   対象レース: {len(races)} 件")
        click.echo(f"   結果保存先: {output_file}")
        
    except Exception as e:
        click.echo(f"❌ エラー: {e}", err=True)
        raise click.Abort()
