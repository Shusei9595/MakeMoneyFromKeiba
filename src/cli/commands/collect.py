"""
データ収集コマンド
"""
import click
from pathlib import Path
from datetime import datetime
import yaml

from src.cli.utils.validators import validate_date
from src.cli.utils.progress import create_progress


@click.command()
@click.option('--start-date', required=True, callback=validate_date,
              help='開始日（YYYY-MM-DD形式）')
@click.option('--end-date', required=True, callback=validate_date,
              help='終了日（YYYY-MM-DD形式）')
@click.option('--output', '-o', default='data/raw/',
              type=click.Path(), help='出力ディレクトリ')
@click.option('--parallel', default=1, type=int,
              help='並列実行数（デフォルト: 1）')
@click.option('--retry', default=3, type=int,
              help='リトライ回数（デフォルト: 3）')
@click.pass_context
def collect(ctx, start_date, end_date, output, parallel, retry):
    """
    netkeiba.comからレースデータを収集
    
    \b
    使用例:
        keiba-ai collect --start-date 2024-01-01 --end-date 2024-12-31
        keiba-ai collect --start-date 2024-01-01 --end-date 2024-01-31 --output data/raw/
    """
    from src.data_collection.netkeiba_scraper import RaceResultScraper
    
    click.echo(f"📊 データ収集開始")
    click.echo(f"   期間: {start_date.strftime('%Y-%m-%d')} ～ {end_date.strftime('%Y-%m-%d')}")
    click.echo(f"   出力先: {output}")
    
    # 設定読み込み
    config_path = Path('config/scraping_config.yaml')
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)
    else:
        config = {'base_url': 'https://db.netkeiba.com', 'request_interval': 1.0}
    
    # スクレイパー初期化
    scraper = RaceResultScraper(config)
    
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        with create_progress() as progress:
            task = progress.add_task("[cyan]収集中...", total=None)
            
            df = scraper.scrape_date_range(
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            progress.update(task, completed=True)
        
        if df is not None and not df.empty:
            output_file = output_dir / f"race_results_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            click.echo(f"✅ 収集完了: {len(df)} レコード")
            click.echo(f"   保存先: {output_file}")
        else:
            click.echo("⚠️ データが見つかりませんでした")
            
    except Exception as e:
        click.echo(f"❌ エラー: {e}", err=True)
        raise click.Abort()
