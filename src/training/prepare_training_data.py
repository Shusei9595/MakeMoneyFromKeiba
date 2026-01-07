"""
訓練データ準備スクリプト

Phase 2で前処理したデータから、エージェント訓練用のデータセットを生成する
"""
import click
import pandas as pd
import numpy as np
from pathlib import Path
from rich.console import Console
from rich.table import Table
import logging
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.base_agent import BaseAgent


console = Console()


def create_target_score(finish_position: int) -> float:
    """
    着順から10点満点の理想スコアを生成
    
    Args:
        finish_position: 着順（1〜18）
    
    Returns:
        10点満点のスコア
    """
    if pd.isna(finish_position) or finish_position <= 0:
        return 5.0  # 欠損値は中間スコア
    
    if finish_position == 1:
        return 10.0
    elif finish_position == 2:
        return 8.5
    elif finish_position == 3:
        return 7.0
    else:
        return max(1.0, 7.0 - (finish_position - 3) * 0.5)


@click.command()
@click.option('--input-file', required=True, help='入力CSVファイル（前処理済みデータ）')
@click.option('--output-dir', default='data/processed', help='出力先ディレクトリ')
@click.option('--train-ratio', default=0.6, help='訓練データの割合')
@click.option('--val-ratio', default=0.2, help='検証データの割合')
def prepare_training_data(input_file, output_dir, train_ratio, val_ratio):
    """
    訓練データを準備
    
    使用例:
    python prepare_training_data.py --input-file data/processed/processed_races.csv
    """
    console.print("[bold green]━━━ 訓練データ準備開始 ━━━[/bold green]")
    
    # データ読み込み
    console.print(f"📂 データ読み込み中: [cyan]{input_file}[/cyan]")
    try:
        df = pd.read_csv(input_file, encoding='utf-8-sig')
    except UnicodeDecodeError:
        df = pd.read_csv(input_file, encoding='utf-8')
    
    console.print(f"✓ 読み込み完了: [green]{len(df)}[/green] レコード")
    
    # ターゲットスコア生成
    console.print("🎯 ターゲットスコア生成中...")
    df['target_score'] = df['finish_position'].apply(create_target_score)
    
    # スコア分布表示
    score_stats = df['target_score'].describe()
    console.print(f"  スコア分布: mean={score_stats['mean']:.2f}, std={score_stats['std']:.2f}")
    
    # 日付順にソート
    if 'race_date' in df.columns:
        df = df.sort_values('race_date')
        console.print("📅 日付順にソート完了")
    
    # 訓練/検証/テスト分割
    n = len(df)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))
    
    df_train = df.iloc[:train_end]
    df_val = df.iloc[train_end:val_end]
    df_test = df.iloc[val_end:]
    
    # 保存
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    train_file = output_path / 'training_data.csv'
    val_file = output_path / 'validation_data.csv'
    test_file = output_path / 'test_data.csv'
    
    df_train.to_csv(train_file, index=False, encoding='utf-8-sig')
    df_val.to_csv(val_file, index=False, encoding='utf-8-sig')
    df_test.to_csv(test_file, index=False, encoding='utf-8-sig')
    
    # 結果サマリー表示
    table = Table(title="データ分割結果")
    table.add_column("データセット", style="cyan")
    table.add_column("レコード数", style="green")
    table.add_column("ファイル", style="yellow")
    
    table.add_row("訓練", str(len(df_train)), str(train_file))
    table.add_row("検証", str(len(df_val)), str(val_file))
    table.add_row("テスト", str(len(df_test)), str(test_file))
    
    console.print(table)
    console.print("[bold green]━━━ 完了！ ━━━[/bold green]")


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    prepare_training_data()
