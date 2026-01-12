import pandas as pd
import sys
import yaml
import json
from pathlib import Path
from datetime import datetime
import logging

# Add project root to sys.path
sys.path.insert(0, str(Path.cwd()))

from src.orchestrator.agent_manager import AgentManager
from src.orchestrator.weight_optimizer import WeightOptimizer
from src.orchestrator.prediction_orchestrator import PredictionOrchestrator
from src.orchestrator.ev_calculator import EVCalculator
from src.orchestrator.betting_recommender import BettingRecommender

def predict_0109():
    # Load data
    data_path = 'data/live_20260109.csv'
    if not Path(data_path).exists():
        print(f"Error: {data_path} not found")
        return
        
    df = pd.read_csv(data_path)
    
    # Init system
    agent_manager = AgentManager(model_dir='models')
    weight_optimizer = WeightOptimizer()
    orchestrator = PredictionOrchestrator(agent_manager=agent_manager, weight_optimizer=weight_optimizer)
    ev_calculator = EVCalculator(min_ev_threshold=0.05)
    recommender = BettingRecommender(total_budget=500) # 500 yen budget per race
    
    report_lines = []
    report_lines.append("# 2026/01/09 地方競馬予測レポート (フォワードテスト)")
    report_lines.append(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("\n## 使用コマンド")
    report_lines.append("```bash")
    report_lines.append("python3 collect_0109.py")
    report_lines.append("python3 predict_0109.py")
    report_lines.append("```\n")
    
    track_map = {
        '42': '浦和',
        '47': '笠松',
        '50': '園田',
        '65': '帯広(ば)'
    }
    
    # Group by race_id
    races = df['race_id'].unique()
    races.sort()
    
    for rid in races:
        race_df = df[df['race_id'] == rid].copy()
        rid_str = str(rid)
        track_code = rid_str[4:6]
        track_name = track_map.get(track_code, 'Unknown')
        race_num = rid_str[-2:]
        
        print(f"Predicting {track_name} {int(race_num)}R ({rid})...")
        
        # Ensure odds
        if 'odds' not in race_df.columns:
            if 'odds_win' in race_df.columns:
                race_df['odds'] = pd.to_numeric(race_df['odds_win'], errors='coerce')
        
        race_df['odds'] = race_df['odds'].fillna(10.0)
        
        try:
            predictions = orchestrator.predict_race(race_df)
            positive_ev_bets = ev_calculator.find_positive_ev_bets(predictions)
            recommendations = recommender.generate_recommendations(positive_ev_bets, strategy='balanced')
            
            report_lines.append(f"### {track_name} {int(race_num)}R")
            report_lines.append(recommender.format_output_text(recommendations))
            report_lines.append("\n---\n")
        except Exception as e:
            print(f"Failed to predict {rid}: {e}")
            import traceback
            traceback.print_exc()
            
    # Save report
    report_path = Path('reports/prediction_20260109.md')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
    print(f"Report saved to {report_path}")

if __name__ == '__main__':
    predict_0109()
