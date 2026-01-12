"""
エージェント比較分析スクリプト

9つのエージェントの性能を比較するレポートを生成
"""
import click
import pandas as pd
import numpy as np
from pathlib import Path
from rich.console import Console
from rich.table import Table
import logging
import sys
import json
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.past_performance_agent import PastPerformanceAgent
from src.agents.distance_adaptability_agent import DistanceAdaptabilityAgent
from src.agents.jockey_trainer_agent import JockeyTrainerAgent
from src.agents.pedigree_agent import PedigreeAgent
from src.agents.race_pace_agent import RacePaceAgent
from src.agents.physical_condition_agent import PhysicalConditionAgent
from src.agents.track_condition_agent import TrackConditionAgent
from src.agents.statistical_pattern_agent import StatisticalPatternAgent
from src.agents.odds_analysis_agent import OddsAnalysisAgent
from src.agents.base_agent import BaseAgent


console = Console()


def get_agent_classes():
    """エージェントクラスのリストを取得"""
    return [
        PastPerformanceAgent,
        DistanceAdaptabilityAgent,
        JockeyTrainerAgent,
        PedigreeAgent,
        RacePaceAgent,
        PhysicalConditionAgent,
        TrackConditionAgent,
        StatisticalPatternAgent,
        OddsAnalysisAgent
    ]


def generate_html_report(results: list, correlations: pd.DataFrame, output_path: Path):
    """HTMLレポートを生成"""
    html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>エージェント比較レポート</title>
    <style>
        body {{
            font-family: 'Hiragino Sans', sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        h1 {{
            color: #333;
            border-bottom: 2px solid #4CAF50;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #555;
            margin-top: 30px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #4CAF50;
            color: white;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .good {{
            color: #4CAF50;
            font-weight: bold;
        }}
        .bad {{
            color: #f44336;
        }}
        .timestamp {{
            color: #999;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <h1>🏇 エージェント比較レポート</h1>
    <p class="timestamp">生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <h2>📊 性能比較</h2>
    <table>
        <tr>
            <th>エージェント</th>
            <th>RMSE</th>
            <th>MAE</th>
            <th>R²</th>
            <th>状態</th>
        </tr>
"""
    
    for r in results:
        rmse_class = 'good' if r.get('rmse', 999) < 1.5 else 'bad'
        r2_class = 'good' if r.get('r2', 0) > 0.4 else 'bad'
        
        html += f"""
        <tr>
            <td>{r['agent']}</td>
            <td class="{rmse_class}">{r.get('rmse', 'N/A'):.4f if r.get('rmse') else 'N/A'}</td>
            <td>{r.get('mae', 'N/A'):.4f if r.get('mae') else 'N/A'}</td>
            <td class="{r2_class}">{r.get('r2', 'N/A'):.4f if r.get('r2') else 'N/A'}</td>
            <td>{r.get('status', 'Unknown')}</td>
        </tr>
"""
    
    html += """
    </table>
    
    <h2>📈 成功基準</h2>
    <ul>
        <li>RMSE &lt; 1.5: スコア予測の平均誤差が1.5点以内</li>
        <li>R² &gt; 0.4: モデルの説明力が40%以上</li>
    </ul>
    
</body>
</html>
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


@click.command()
@click.option('--test-data', required=True, help='テストデータCSVファイル')
@click.option('--models', default='models', help='モデルディレクトリ')
@click.option('--output', default='reports', help='レポート出力先ディレクトリ')
def agent_comparison(test_data, models, output):
    """
    エージェント比較レポートを生成
    
    使用例:
    python agent_comparison.py --test-data data/processed/test_data.csv --models models/
    """
    console.print("[bold green]━━━ エージェント比較分析開始 ━━━[/bold green]")
    
    # データ読み込み
    console.print(f"📂 テストデータ読み込み中: [cyan]{test_data}[/cyan]")
    try:
        df_test = pd.read_csv(test_data, encoding='utf-8-sig')
    except UnicodeDecodeError:
        df_test = pd.read_csv(test_data, encoding='utf-8')
    
    console.print(f"✓ 読み込み完了: [green]{len(df_test)}[/green] レコード")
    
    # ターゲット確認
    if 'target_score' not in df_test.columns:
        if 'finish_position' in df_test.columns:
            df_test['target_score'] = df_test['finish_position'].apply(
                BaseAgent.create_target_score
            )
    
    y_true = df_test['target_score']
    
    # モデルディレクトリ
    models_dir = Path(models)
    output_dir = Path(output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 全エージェントを評価
    results = []
    predictions_dict = {}
    
    agent_classes = get_agent_classes()
    
    for AgentClass in agent_classes:
        agent = AgentClass()
        model_path = models_dir / f"{agent.name}_v1.pkl"
        
        try:
            if model_path.exists():
                agent.load_model(model_path)
                
                # 予測
                predictions = agent.predict(df_test)
                predictions_dict[agent.name] = predictions
                
                # 評価
                metrics = agent.evaluate(df_test, y_true)
                
                results.append({
                    'agent': agent.name,
                    'rmse': metrics['rmse'],
                    'mae': metrics['mae'],
                    'r2': metrics['r2'],
                    'status': '✅ 評価完了'
                })
                
                console.print(f"✓ {agent.name}: RMSE={metrics['rmse']:.4f}, R²={metrics['r2']:.4f}")
            else:
                results.append({
                    'agent': agent.name,
                    'rmse': None,
                    'mae': None,
                    'r2': None,
                    'status': '⚠️ モデル未訓練'
                })
                console.print(f"⚠️ {agent.name}: モデルファイルが見つかりません")
        
        except Exception as e:
            results.append({
                'agent': agent.name,
                'rmse': None,
                'mae': None,
                'r2': None,
                'status': f'❌ {str(e)[:30]}'
            })
            console.print(f"❌ {agent.name}: {e}")
    
    # 相関分析
    if predictions_dict:
        correlations = pd.DataFrame(predictions_dict).corr()
    else:
        correlations = pd.DataFrame()
    
    # HTMLレポート生成
    report_path = output_dir / 'agent_comparison_report.html'
    generate_html_report(results, correlations, report_path)
    
    console.print(f"\n✓ レポート保存: {report_path}")
    console.print("[bold green]━━━ 完了！ ━━━[/bold green]")


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    agent_comparison()
