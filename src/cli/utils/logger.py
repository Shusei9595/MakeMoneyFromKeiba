"""
CLIロガー設定
"""
import logging
import sys
from rich.logging import RichHandler
from rich.console import Console

console = Console()


def setup_cli_logger(verbose: bool = False):
    """CLIロガーをセットアップ"""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(console=console, rich_tracebacks=True)]
    )
    
    # 外部ライブラリのログを抑制
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
