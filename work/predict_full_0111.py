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

def predict_full():
    data_path = 'data/live_20260111.csv'
    if not Path(data_path).exists():
        print(f"Error: {data_path} not found. Please run collect_full_0111.py first.")
        return
        
    df = pd.read_csv(data_path)
    
    # Init system
    agent_manager = AgentManager(model_dir='models')
    weight_optimizer = WeightOptimizer()
    orchestrator = PredictionOrchestrator(agent_manager=agent_manager, weight_optimizer=weight_optimizer)
    ev_calculator = EVCalculator(min_ev_threshold=0.05)
    recommender = BettingRecommender(total_budget=500)
    
    report_lines = []
    report_lines.append("# 2026/01/11 全レース予測レポート (JRA & NAR)")
    report_lines.append(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("\n## 対象競馬場")
    report_lines.append("- **JRA**: 中山, 京都")
    report_lines.append("- **NAR**: 高知, 佐賀")
    report_lines.append("\n## 使用データ")
    report_lines.append("各出走馬の直近5走データを反映させた高精度特徴量を使用しています。")
    report_lines.append("\n---\n")
    
    track_map = {
        '06': '中山',
        '08': '京都',
        '54': '高知',
        '55': '佐賀'
    }
    
    races = df['race_id'].unique()
    races.sort()
    
    print(f"Starting predictions for {len(races)} races...")
    
    for rid in races:
        rid_str = str(rid)
        # JRA ID: 2026 06 01 04 01 (12 digits)
        # NAR ID: 2026 54 01 11 01 (12 digits)
        track_code = rid_str[4:6]
        track_name = track_map.get(track_code, f'Track({track_code})')
        race_num = rid_str[-2:]
        
        print(f"Predicting {track_name} {int(race_num)}R...")
        
        race_df = df[df['race_id'] == rid].copy()
        
        try:
            predictions = orchestrator.predict_race(race_df)
            positive_ev_bets = ev_calculator.find_positive_ev_bets(predictions)
            recommendations = recommender.generate_recommendations(positive_ev_bets, strategy='balanced')
            
            report_lines.append(f"### {track_name} {int(race_num)}R")
            report_lines.append(recommender.format_output_text(recommendations))
            report_lines.append("\n---\n")
        except Exception as e:
            print(f"  Failed for {rid}: {e}")
            
    report_path = Path('reports/prediction_20260111.md')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
    print(f"SUCCESS: Report saved to {report_path}")

if __name__ == '__main__':
    predict_full()
