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

def evaluate():
    # Load data
    data_path = 'data/live_20260108.csv'
    results_path = 'data/results_20260108.json'
    
    if not Path(data_path).exists():
        print(f"Error: {data_path} not found")
        return
    if not Path(results_path).exists():
        print(f"Error: {results_path} not found")
        return
        
    df = pd.read_csv(data_path)
    with open(results_path, 'r', encoding='utf-8') as f:
        results_data = json.load(f)
    
    # Init system
    agent_manager = AgentManager(model_dir='models')
    weight_optimizer = WeightOptimizer()
    orchestrator = PredictionOrchestrator(agent_manager=agent_manager, weight_optimizer=weight_optimizer)
    ev_calculator = EVCalculator(min_ev_threshold=0.05)
    recommender = BettingRecommender(total_budget=500)
    
    total_invested = 0
    total_payout = 0
    total_hits = 0
    total_bets = 0
    
    race_results = []
    
    track_map = {
        '42': '浦和',
        '47': '笠松',
        '50': '園田',
        '65': '帯広(ば)'
    }
    
    races = df['race_id'].unique()
    races.sort()
    
    for rid in races:
        rid_str = str(rid)
        race_df = df[df['race_id'] == rid].copy()
        track_code = rid_str[4:6]
        track_name = track_map.get(track_code, 'Unknown')
        race_num = rid_str[-2:]
        
        print(f"Evaluating {track_name} {race_num}R ({rid})...")
        
        # Ensure odds
        if 'odds' not in race_df.columns:
            if 'odds_win' in race_df.columns:
                race_df['odds'] = pd.to_numeric(race_df['odds_win'], errors='coerce')
            else:
                race_df['odds'] = 10.0
        race_df['odds'] = race_df['odds'].fillna(10.0)
        
        actual_results = results_data.get(rid_str, {})
        if not actual_results:
            print(f"  No actual results found for {rid}")
            continue
            
        try:
            predictions = orchestrator.predict_race(race_df)
            positive_ev_bets = ev_calculator.find_positive_ev_bets(predictions)
            recommendations = recommender.generate_recommendations(positive_ev_bets, strategy='balanced')
            
            race_invested = recommendations['allocated_budget']
            race_payout = 0
            race_hits = 0
            
            bet_details = []
            
            # 券種ごとの順序制約
            unordered_bets = ['quinella', 'wide', 'trio', 'trifecta_trio', 'bracket_quinella']

            for bet in recommendations['recommendations']:
                total_bets += 1
                
                # Check hit
                bet_type = bet['bet_type'] # 'win', 'place', etc.
                
                # 推奨の馬番リストを正規化
                pred_horses = [str(h) for h in bet['horses']]
                if bet_type in unordered_bets:
                    pred_horses.sort()
                pred_key = '-'.join(pred_horses)
                
                hit = False
                payout_amount = 0
                
                actual_payouts = actual_results.get('payouts', {}).get(bet_type, {})
                if actual_payouts:
                    combinations = actual_payouts.get('combinations', [])
                    payout_amounts = actual_payouts.get('payouts', [])
                    
                    for idx, comb in enumerate(combinations):
                        # 実績の組み合わせもソートして比較
                        actual_horses = comb.split('-')
                        if bet_type in unordered_bets:
                            actual_horses.sort()
                        actual_key = '-'.join(actual_horses)
                        
                        if actual_key == pred_key:
                            hit = True
                            payout_amount = (payout_amounts[idx] * bet['bet_amount']) // 100
                            break
                
                if hit:
                    race_hits += 1
                    race_payout += payout_amount
                    total_hits += 1
                
                bet_details.append({
                    'type': bet_type,
                    'horses': pred_key,
                    'amount': bet['bet_amount'],
                    'hit': hit,
                    'payout': payout_amount
                })
            
            total_invested += race_invested
            total_payout += race_payout
            
            race_results.append({
                'race_id': rid_str,
                'track': track_name,
                'num': race_num,
                'invested': race_invested,
                'payout': race_payout,
                'profit': race_payout - race_invested,
                'hits': race_hits,
                'bets': len(recommendations['recommendations']),
                'details': bet_details
            })
            
        except Exception as e:
            print(f"Error evaluating {rid}: {e}")

    # Generate Report
    report_lines = []
    report_lines.append("# 2026/01/08 予測パフォーマンス評価レポート")
    report_lines.append(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("\n## 総括")
    
    roi = (total_payout / total_invested * 100) if total_invested > 0 else 0
    hit_rate = (total_hits / total_bets * 100) if total_bets > 0 else 0
    
    report_lines.append(f"- **総投資額**: {total_invested:,}円")
    report_lines.append(f"- **総払戻額**: {total_payout:,}円")
    report_lines.append(f"- **純利益**: {total_payout - total_invested:,}円")
    report_lines.append(f"- **回収率 (ROI)**: {roi:.1f}%")
    report_lines.append(f"- **的中率**: {hit_rate:.1f}% ({total_hits}/{total_bets})")
    
    report_lines.append("\n## レース別詳細")
    report_lines.append("| レース | 投資 | 払戻 | 利益 | 的中数/購入数 |")
    report_lines.append("| :--- | :---: | :---: | :---: | :---: |")
    
    for r in race_results:
        report_lines.append(f"| {r['track']} {int(r['num'])}R | {r['invested']}円 | {r['payout']}円 | {r['profit']}円 | {r['hits']}/{r['bets']} |")
    
    report_path = Path('reports/evaluation_20260108.md')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
    
    print(f"Evaluation finished. ROI: {roi:.1f}%. Report saved to {report_path}")

if __name__ == '__main__':
    evaluate()
