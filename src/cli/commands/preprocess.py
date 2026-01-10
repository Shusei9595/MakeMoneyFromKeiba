"""
データ前処理コマンド
"""
import click
from pathlib import Path
import yaml

from src.cli.utils.progress import create_progress


@click.command()
@click.option('--input', '-i', 'input_dir', required=True,
              type=click.Path(exists=True), help='入力ディレクトリ')
@click.option('--output', '-o', default='data/processed/',
              type=click.Path(), help='出力ディレクトリ')
@click.option('--validate', is_flag=True, help='データ品質検証を実行')
@click.option('--export-stats', is_flag=True, help='統計サマリーをエクスポート')
@click.pass_context
def preprocess(ctx, input_dir, output, validate, export_stats):
    """
    収集したデータを前処理
    
    \b
    使用例:
        keiba-ai preprocess --input data/raw/ --output data/processed/
        keiba-ai preprocess --input data/raw/ --validate
    """
    from src.preprocessing.pipeline import DataPreprocessingPipeline
    import pandas as pd
    
    click.echo(f"🔧 前処理開始")
    click.echo(f"   入力: {input_dir}")
    click.echo(f"   出力: {output}")
    
    input_path = Path(input_dir)
    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 設定読み込み
    config_path = Path('config/preprocessing_config.yaml')
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
    else:
        config = {}
    
    try:
        # CSVファイルを読み込み
        csv_files = list(input_path.glob('*.csv'))
        if not csv_files:
            click.echo("⚠️ CSVファイルが見つかりません", err=True)
            raise click.Abort()
        
        click.echo(f"   対象ファイル: {len(csv_files)} 件")
        
        with create_progress() as progress:
            task = progress.add_task("[cyan]前処理中...", total=len(csv_files))
            
            all_dfs = []
            for csv_file in csv_files:
                df = pd.read_csv(csv_file)
                all_dfs.append(df)
                progress.advance(task)
            
            combined_df = pd.concat(all_dfs, ignore_index=True)
        
        # パイプライン実行
        pipeline = DataPreprocessingPipeline(config)
        processed_df = pipeline.fit_transform(combined_df)
        
        # 保存
        output_file = output_path / 'training_data.csv'
        processed_df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        click.echo(f"✅ 前処理完了")
        click.echo(f"   入力: {len(combined_df)} 行")
        click.echo(f"   出力: {len(processed_df)} 行, {len(processed_df.columns)} カラム")
        click.echo(f"   保存先: {output_file}")
        
        if export_stats:
            stats_file = output_path / 'data_stats.csv'
            processed_df.describe().to_csv(stats_file)
            click.echo(f"   統計: {stats_file}")
            
    except Exception as e:
        click.echo(f"❌ エラー: {e}", err=True)
        raise click.Abort()
