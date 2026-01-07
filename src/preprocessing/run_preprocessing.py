"""
前処理実行CLIモジュール

コマンドラインから前処理パイプラインを実行するためのエントリーポイント
"""
import click
import pandas as pd
from pathlib import Path
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
import logging
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.preprocessing.pipeline import DataPreprocessingPipeline


console = Console()


@click.command()
@click.option('--input-file', required=True, help='入力CSVファイル')
@click.option('--output-dir', default='data/processed', help='出力先ディレクトリ')
@click.option('--save-pipeline', is_flag=True, help='パイプラインを保存')
@click.option('--config-file', default='config/config.yaml', help='設定ファイル')
def run_preprocessing(input_file, output_dir, save_pipeline, config_file):
    """
    データ前処理を実行
    
    使用例:
    python run_preprocessing.py --input-file data/raw/races_2024-01-06_2024-01-06.csv --save-pipeline
    """
    console.print("[bold green]━━━ データ前処理開始 ━━━[/bold green]")
    
    # 設定ファイル読み込み
    config_path = Path(config_file)
    if config_path.exists():
        with open(config_path) as f:
            full_config = yaml.safe_load(f)
            config = full_config.get('preprocessing', {})
    else:
        console.print(f"[yellow]警告: 設定ファイルが見つかりません。デフォルト設定を使用します。[/yellow]")
        config = {
            'missing_value_strategy': 'median',
            'outlier_threshold': 3.0,
            'normalization': 'standard'
        }
    
    # データ読み込み
    console.print(f"📂 データ読み込み中: [cyan]{input_file}[/cyan]")
    try:
        df = pd.read_csv(input_file, encoding='utf-8-sig')
    except UnicodeDecodeError:
        df = pd.read_csv(input_file, encoding='utf-8')
    
    # race_dateを日付型に変換
    if 'race_date' in df.columns:
        df['race_date'] = pd.to_datetime(df['race_date'], errors='coerce')
    
    console.print(f"✓ 読み込み完了: [green]{len(df)}[/green] レコード, [green]{len(df.columns)}[/green] カラム")
    
    # パイプライン実行
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]前処理中...", total=None)
        
        pipeline = DataPreprocessingPipeline(config)
        df_processed = pipeline.fit_transform(df)
        
        progress.update(task, completed=True)
    
    # 保存
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    input_stem = Path(input_file).stem
    output_file = output_path / f"processed_{input_stem}.csv"
    df_processed.to_csv(output_file, index=False, encoding='utf-8-sig')
    
    console.print(f"[bold green]✓[/bold green] 保存完了: [cyan]{output_file}[/cyan]")
    
    # 結果サマリー表示
    table = Table(title="処理結果サマリー")
    table.add_column("項目", style="cyan")
    table.add_column("値", style="green")
    
    table.add_row("入力レコード数", str(len(df)))
    table.add_row("出力レコード数", str(len(df_processed)))
    table.add_row("入力カラム数", str(len(df.columns)))
    table.add_row("出力カラム数", str(len(df_processed.columns)))
    table.add_row("追加特徴量数", str(len(df_processed.columns) - len(df.columns)))
    
    console.print(table)
    
    # 特徴量統計
    console.print("\n[bold yellow]特徴量統計 (欠損率順):[/bold yellow]")
    feature_stats = pipeline.feature_engineer.get_feature_importance_ranking(df_processed)
    
    stats_table = Table()
    stats_table.add_column("特徴量", style="cyan")
    stats_table.add_column("平均", style="green")
    stats_table.add_column("標準偏差", style="green")
    stats_table.add_column("欠損率", style="yellow")
    
    for _, row in feature_stats.head(10).iterrows():
        stats_table.add_row(
            str(row['feature'])[:30],
            f"{row['mean']:.4f}" if pd.notna(row['mean']) else "N/A",
            f"{row['std']:.4f}" if pd.notna(row['std']) else "N/A",
            f"{row['missing_ratio']:.2%}"
        )
    
    console.print(stats_table)
    
    # パイプライン保存
    if save_pipeline:
        pipeline_dir = Path('models/preprocessing')
        pipeline.save(pipeline_dir)
        console.print(f"[bold green]✓[/bold green] パイプライン保存: [cyan]{pipeline_dir}[/cyan]")
    
    console.print("[bold green]━━━ 完了！ ━━━[/bold green]")


if __name__ == '__main__':
    # ログ設定
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/preprocessing.log'),
            logging.StreamHandler()
        ]
    )
    
    run_preprocessing()
