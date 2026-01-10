"""
プログレスバーユーティリティ
"""
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.console import Console
from contextlib import contextmanager

console = Console()


@contextmanager
def show_progress(desc: str = "処理中"):
    """プログレスバー表示"""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    ) as progress:
        task = progress.add_task(desc, total=None)
        yield progress
        progress.update(task, completed=True)


def create_progress():
    """カスタムプログレスバー作成"""
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console
    )
