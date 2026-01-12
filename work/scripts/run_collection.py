"""
データ収集実行スクリプト
CLIからデータ収集を実行するためのツール
"""

import click
from pathlib import Path
import yaml
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table
from datetime import datetime
import logging
import sys

# パスを追加してモジュールをインポート
sys.path.insert(0, str(Path(__file__).parent.parent))

from data_collection.netkeiba_scraper import (
    RaceResultScraper,
    HorseInfoScraper,
    JockeyTrainerScraper,
    OddsDataScraper,
    LiveRaceScraper
)
from data_collection.data_validator import DataValidator


def setup_logging(log_dir: str = 'logs'):
    """ログ設定を初期化"""
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    log_file = log_path / f"data_collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)


@click.group()
def cli():
    """競馬データ収集ツール"""
    pass


@cli.command()
@click.option('--start-date', required=True, help='開始日 (YYYY-MM-DD)')
@click.option('--end-date', required=True, help='終了日 (YYYY-MM-DD)')
@click.option('--tracks', default=None, help='競馬場指定（カンマ区切り）')
@click.option('--output-dir', default='data/raw', help='出力先ディレクトリ')
@click.option('--config', default='config/scraping_config.yaml', help='設定ファイルパス')
@click.option('--validate', is_flag=True, help='データ検証を実行')
@click.option('--log-dir', default='logs', help='ログディレクトリ')
def collect_races(start_date, end_date, tracks, output_dir, config, validate, log_dir):
    """
    レースデータを収集
    
    使用例:
    python run_collection.py collect-races --start-date 2024-01-01 --end-date 2024-01-31 --validate
    """
    console = Console()
    logger = setup_logging(log_dir)
    
    console.print("\n[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]")
    console.print("[bold blue]  競馬データ収集システム - レース結果[/bold blue]")
    console.print("[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]\n")
    
    try:
        # 設定ファイル読み込み
        config_path = Path(config)
        if not config_path.exists():
            console.print(f"[bold red]❌ 設定ファイルが見つかりません: {config}[/bold red]")
            return
        
        with open(config_path) as f:
            config_data = yaml.safe_load(f)
        
        logger.info(f"Configuration loaded from {config}")
        
        # スクレイパー初期化
        scraper = RaceResultScraper(config_data)
        
        # 収集情報の表示
        info_table = Table(show_header=False, box=None)
        info_table.add_row("[cyan]期間[/cyan]", f"{start_date} ～ {end_date}")
        info_table.add_row("[cyan]競馬場[/cyan]", tracks if tracks else "全競馬場")
        info_table.add_row("[cyan]出力先[/cyan]", output_dir)
        console.print(info_table)
        console.print()
        
        # データ収集
        console.print("[bold green]📥 データ収集開始...[/bold green]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]収集中...", total=100)
            
            df = scraper.scrape_date_range(
                start_date=start_date,
                end_date=end_date,
                tracks=tracks.split(',') if tracks else None
            )
            
            progress.update(task, completed=100)
        
        if df.empty:
            console.print("[bold yellow]⚠️ データが取得できませんでした[/bold yellow]")
            logger.warning("No data collected")
            return
        
        # 統計情報の表示
        stats_table = Table(title="収集結果", show_header=True)
        stats_table.add_column("項目", style="cyan")
        stats_table.add_column("値", style="green")
        
        stats_table.add_row("レコード数", str(len(df)))
        stats_table.add_row("ユニークレース数", str(df['race_id'].nunique() if 'race_id' in df.columns else 'N/A'))
        stats_table.add_row("競馬場数", str(df['track_name'].nunique() if 'track_name' in df.columns else 'N/A'))
        stats_table.add_row("カラム数", str(len(df.columns)))
        
        console.print()
        console.print(stats_table)
        
        # 保存
        output_path = Path(output_dir) / f"races_{start_date}_{end_date}.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        console.print(f"\n[bold green]✓ 保存完了:[/bold green] {output_path}")
        logger.info(f"Saved {len(df)} records to {output_path}")
        
        # データ検証
        if validate:
            console.print("\n[bold yellow]🔍 データ検証中...[/bold yellow]")
            validator = DataValidator()
            result = validator.validate_race_data(df)
            
            # 検証結果の表示
            if result['is_valid']:
                console.print("[bold green]✓ 検証成功[/bold green]")
            else:
                console.print("[bold red]✗ 検証エラー[/bold red]")
                
                if result['errors']:
                    console.print("\n[bold red]エラー:[/bold red]")
                    for error in result['errors']:
                        console.print(f"  ❌ {error}")
                
                if result['warnings']:
                    console.print("\n[bold yellow]警告:[/bold yellow]")
                    for warning in result['warnings']:
                        console.print(f"  ⚠️ {warning}")
            
            # 欠損値の表示
            if result['missing_values']:
                console.print("\n[bold cyan]欠損値:[/bold cyan]")
                missing_table = Table(show_header=True)
                missing_table.add_column("カラム", style="cyan")
                missing_table.add_column("欠損数", style="yellow")
                missing_table.add_column("割合", style="yellow")
                
                for col, count in result['missing_values'].items():
                    pct = (count / len(df)) * 100
                    missing_table.add_row(col, str(count), f"{pct:.2f}%")
                
                console.print(missing_table)
            
            # レポート保存
            report = validator.generate_report([result])
            report_path = output_path.parent / f"validation_report_{start_date}_{end_date}.md"
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            console.print(f"\n[bold green]✓ 検証レポート保存:[/bold green] {report_path}")
        
        console.print("\n[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]")
        console.print("[bold green]      完了！[/bold green]")
        console.print("[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]\n")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ エラーが発生しました: {e}[/bold red]")
        logger.error(f"Error during collection: {e}", exc_info=True)
        raise


@cli.command()
@click.option('--horse-ids', required=True, help='馬ID（カンマ区切り）')
@click.option('--output-dir', default='data/raw', help='出力先ディレクトリ')
@click.option('--config', default='config/scraping_config.yaml', help='設定ファイルパス')
@click.option('--log-dir', default='logs', help='ログディレクトリ')
def collect_horses(horse_ids, output_dir, config, log_dir):
    """
    馬情報を収集
    
    使用例:
    python run_collection.py collect-horses --horse-ids 2020100101,2020100102
    """
    console = Console()
    logger = setup_logging(log_dir)
    
    console.print("\n[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]")
    console.print("[bold blue]  競馬データ収集システム - 馬情報[/bold blue]")
    console.print("[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]\n")
    
    try:
        # 設定ファイル読み込み
        with open(config) as f:
            config_data = yaml.safe_load(f)
        
        # スクレイパー初期化
        scraper = HorseInfoScraper(config_data)
        
        # IDリストの作成
        id_list = [hid.strip() for hid in horse_ids.split(',')]
        
        console.print(f"[cyan]収集対象:[/cyan] {len(id_list)}頭")
        console.print()
        
        # データ収集
        horses_data = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]収集中...", total=len(id_list))
            
            for horse_id in id_list:
                horse_info = scraper.scrape_horse(horse_id)
                if horse_info:
                    horses_data.append(horse_info)
                progress.advance(task)
        
        if not horses_data:
            console.print("[bold yellow]⚠️ データが取得できませんでした[/bold yellow]")
            return
        
        # DataFrame化して保存
        import pandas as pd
        df = pd.DataFrame(horses_data)
        
        output_path = Path(output_dir) / f"horses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        console.print(f"\n[bold green]✓ 保存完了:[/bold green] {output_path}")
        console.print(f"[green]収集件数: {len(horses_data)}頭[/green]\n")
        
        logger.info(f"Saved {len(horses_data)} horse records to {output_path}")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ エラーが発生しました: {e}[/bold red]")
        logger.error(f"Error during horse collection: {e}", exc_info=True)
        raise


@cli.command()
@click.option('--race-id', required=True, help='レースID')
@click.option('--odds-type', default='win', help='オッズ種類 (win, place, quinella, etc.)')
@click.option('--output-dir', default='data/raw', help='出力先ディレクトリ')
@click.option('--config', default='config/scraping_config.yaml', help='設定ファイルパス')
def collect_odds(race_id, odds_type, output_dir, config):
    """
    オッズデータを収集
    
    使用例:
    python run_collection.py collect-odds --race-id 202401010101 --odds-type win
    """
    console = Console()
    
    try:
        # 設定ファイル読み込み
        with open(config) as f:
            config_data = yaml.safe_load(f)
        
        # スクレイパー初期化
        scraper = OddsDataScraper(config_data)
        
        console.print(f"\n[cyan]レースID:[/cyan] {race_id}")
        console.print(f"[cyan]オッズ種類:[/cyan] {odds_type}\n")
        
        # データ収集
        odds_data = scraper.scrape_odds(race_id, odds_type)
        
        if not odds_data:
            console.print("[bold yellow]⚠️ データが取得できませんでした[/bold yellow]")
            return
        
        # 保存
        import json
        output_path = Path(output_dir) / f"odds_{race_id}_{odds_type}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(odds_data, f, ensure_ascii=False, indent=2)
        
        console.print(f"[bold green]✓ 保存完了:[/bold green] {output_path}\n")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ エラーが発生しました: {e}[/bold red]")
        raise


@cli.command()
@click.option('--date', required=True, help='対象日 (YYYYMMDD)')
@click.option('--output-dir', default='data/raw', help='出力先ディレクトリ')
@click.option('--config', default='config/scraping_config.yaml', help='設定ファイルパス')
@click.option('--log-dir', default='logs', help='ログディレクトリ')
def collect_live(date, output_dir, config, log_dir):
    """
    最新レース（ライブデータ）を収集
    
    使用例:
    python run_collection.py collect-live --date 20260107
    """
    console = Console()
    logger = setup_logging(log_dir)
    
    console.print("\n[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]")
    console.print("[bold blue]  競馬データ収集システム - ライブ収集[/bold blue]")
    console.print("[bold blue]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold blue]\n")
    
    try:
        with open(config) as f:
            config_data = yaml.safe_load(f)
        
        scraper = LiveRaceScraper(config_data)
        
        # レース一覧取得
        console.print(f"[cyan]📅 対象日:[/cyan] {date}")
        race_ids = scraper.scrape_race_list(date)
        
        if not race_ids:
            console.print("[bold yellow]⚠️ レースが見つかりませんでした[/bold yellow]")
            return
            
        console.print(f"✓ [green]{len(race_ids)}[/green] レース発見")
        
        all_live_data = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]出馬表収集中...", total=len(race_ids))
            
            for rid in race_ids:
                df_shutuba = scraper.scrape_shutuba(rid)
                if not df_shutuba.empty:
                    # 結果も取得（最新なので確定しているはず）
                    df_results = scraper.scrape_results(rid)
                    if not df_results.empty:
                        # 結合（簡易版）
                        df_merged = pd.merge(
                            df_shutuba, 
                            df_results[['horse_number', 'finish_position']], 
                            on='horse_number', 
                            how='left'
                        )
                        all_live_data.append(df_merged)
                progress.advance(task)
        
        if not all_live_data:
            console.print("[bold yellow]⚠️ 出馬表が取得できませんでした[/bold yellow]")
            return
            
        # 統合
        final_df = pd.concat(all_live_data, ignore_index=True)
        
        # 日付カラム追加
        import pandas as pd
        final_df['race_date'] = f"{date[:4]}-{date[4:6]}-{date[6:]}"
        
        # 保存
        output_path = Path(output_dir) / f"live_races_{date}.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        console.print(f"\n[bold green]✓ 保存完了:[/bold green] {output_path}")
        logger.info(f"Saved {len(final_df)} live race records to {output_path}")
        
    except Exception as e:
        console.print(f"\n[bold red]❌ エラーが発生しました: {e}[/bold red]")
        logger.error(f"Error during live collection: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    cli()
