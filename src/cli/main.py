"""
keiba-ai CLIツール

競馬AI予測システムのコマンドラインインターフェース
"""
import click
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.cli.commands import collect, preprocess, train, predict, backtest, report, config
from src.cli.utils.logger import setup_cli_logger


@click.group()
@click.version_option(version='1.0.0', prog_name='keiba-ai')
@click.option('--verbose', '-v', is_flag=True, help='詳細ログ出力')
@click.pass_context
def cli(ctx, verbose):
    """
    🐴 競馬AI予測システム - CLIツール
    
    \b
    使用例:
        keiba-ai collect --start-date 2024-01-01 --end-date 2024-12-31
        keiba-ai train --data data/processed/training_data.csv
        keiba-ai predict --date 2024-12-31 --strategy balanced --budget 10000
        keiba-ai backtest --start-date 2024-01-01 --end-date 2024-12-31
    
    各コマンドの詳細は `keiba-ai <command> --help` で確認できます。
    """
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    setup_cli_logger(verbose=verbose)


# コマンド登録
cli.add_command(collect.collect)
cli.add_command(preprocess.preprocess)
cli.add_command(train.train)
cli.add_command(predict.predict)
cli.add_command(backtest.backtest)
cli.add_command(report.report)
cli.add_command(config.config)


def main():
    """エントリーポイント"""
    try:
        cli()
    except KeyboardInterrupt:
        click.echo("\n中断されました", err=True)
        sys.exit(130)
    except Exception as e:
        click.echo(f"エラー: {str(e)}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
