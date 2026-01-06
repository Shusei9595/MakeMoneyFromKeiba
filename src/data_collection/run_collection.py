import click
from pathlib import Path
import yaml
from rich.console import Console
from rich.progress import Progress
from datetime import datetime
import logging
import sys

# srcモジュールへのパスを通す
sys.path.append(str(Path(__file__).parent.parent))

from data_collection.netkeiba_scraper import (
    RaceResultScraper,
    HorseInfoScraper,
    JockeyTrainerScraper,
    OddsDataScraper
)
from data_collection.data_validator import DataValidator


@click.command()
@click.option('--start-date', required=True, help='開始日 (YYYY-MM-DD)')
@click.option('--end-date', required=True, help='終了日 (YYYY-MM-DD)')
@click.option('--tracks', default=None, help='競馬場指定（カンマ区切り）')
@click.option('--output-dir', default='data/raw', help='出力先ディレクトリ')
@click.option('--validate', is_flag=True, help='データ検証を実行')
def collect_race_data(start_date, end_date, tracks, output_dir, validate):
    """
    レースデータを収集
    
    使用例:
    python run_collection.py --start-date 2024-01-01 --end-date 2024-01-31 --validate
    """
    console = Console()
    
    # 設定ファイル読み込み
    config_path = Path('config/scraping_config.yaml')
    if not config_path.exists():
         # 実行ディレクトリからの相対パスで探すか、プロジェクトルートからのパスを試す
         search_paths = [Path('config/scraping_config.yaml'), Path('../../config/scraping_config.yaml')]
         for p in search_paths:
             if p.exists():
                 config_path = p
                 break
    
    if not config_path.exists():
        console.print("[bold red]Configuration file not found![/bold red]")
        return

    with open(config_path, encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # スクレイパー初期化
    scraper = RaceResultScraper(config)
    
    console.print(f"[bold green]データ収集開始[/bold green]")
    console.print(f"期間: {start_date} ～ {end_date}")
    
    # データ収集
    try:
        with Progress() as progress:
            task = progress.add_task("[cyan]収集中...", total=100)
            
            df = scraper.scrape_date_range(
                start_date=start_date,
                end_date=end_date,
                tracks=tracks.split(',') if tracks else None
            )
            
            progress.update(task, advance=100)
    except Exception as e:
        console.print(f"[bold red]エラーが発生しました: {e}[/bold red]")
        logging.error(f"Scraping failed: {e}", exc_info=True)
        return

    if df.empty:
        console.print("[bold yellow]収集されたデータはありませんでした。[/bold yellow]")
        return
    
    # 保存
    output_path = Path(output_dir) / f"races_{start_date}_{end_date}.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    console.print(f"[bold green]✓[/bold green] 保存完了: {output_path}")
    console.print(f"レコード数: {len(df)}")
    
    # データ検証
    if validate:
        console.print("[bold yellow]データ検証中...[/bold yellow]")
        validator = DataValidator()
        result = validator.validate_race_data(df)
        
        if result['is_valid']:
            console.print("[bold green]✓ 検証成功[/bold green]")
        else:
            console.print("[bold red]✗ 検証エラー[/bold red]")
            for error in result['errors']:
                console.print(f"  - {error}")
            for warning in result['warnings']:
                 console.print(f"  - [yellow]{warning}[/yellow]")
    
    console.print("[bold green]完了！[/bold green]")


if __name__ == '__main__':
    # ログ設定
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'data_collection.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    collect_race_data()
