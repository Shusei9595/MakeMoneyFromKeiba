"""
Backtester Module

過去データでシステムを検証するバックテストエンジン
"""
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime, timedelta
import logging
import sys

import pandas as pd
import numpy as np

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.orchestrator.prediction_orchestrator import PredictionOrchestrator
from src.orchestrator.ev_calculator import EVCalculator
from src.orchestrator.betting_recommender import BettingRecommender


class Backtester:
    """
    バックテストエンジン
    
    責任:
    - 過去データでオーケストレーターを実行
    - 買い目を仮想購入
    - 払戻を記録
    - 日次・月次・累積収支を計算
    """
    
    def __init__(
        self,
        orchestrator: PredictionOrchestrator,
        ev_calculator: EVCalculator,
        recommender: BettingRecommender,
        initial_budget: float = 100000
    ):
        """
        Args:
            orchestrator: 予測オーケストレーター
            ev_calculator: EV計算機
            recommender: 買い目推奨システム
            initial_budget: 初期予算
        """
        self.orchestrator = orchestrator
        self.ev_calculator = ev_calculator
        self.recommender = recommender
        self.initial_budget = initial_budget
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def run_backtest(
        self,
        data: pd.DataFrame,
        strategy: str = 'balanced'
    ) -> Dict[str, Any]:
        """
        バックテスト実行
        
        Args:
            data: 前処理済みデータ（全レース分）
            strategy: 'conservative', 'balanced', 'aggressive'
        
        Returns:
            バックテスト結果
        """
        self.logger.info(f"Starting backtest with strategy: {strategy}")
        
        # レースIDでグループ化
        if 'race_id' not in data.columns:
            raise ValueError("Data must contain 'race_id' column")
        
        race_ids = data['race_id'].unique()
        self.logger.info(f"Processing {len(race_ids)} races")
        
        current_budget = self.initial_budget
        race_results = []
        betting_history = []
        
        for race_id in race_ids:
            race_data = data[data['race_id'] == race_id].copy()
            
            if len(race_data) < 3:
                continue
            
            try:
                result = self.process_race(
                    race_id=str(race_id),
                    race_data=race_data,
                    current_budget=current_budget,
                    strategy=strategy
                )
                
                if result:
                    race_results.append(result)
                    betting_history.extend(result.get('bets_placed', []))
                    current_budget = result['budget_after']
                    
            except Exception as e:
                self.logger.warning(f"Error processing race {race_id}: {e}")
                continue
        
        # 結果集計
        summary = self.aggregate_results(race_results)
        
        return {
            'summary': summary,
            'race_results': race_results,
            'betting_history': betting_history,
            'final_budget': current_budget,
            'strategy': strategy
        }
    
    def process_race(
        self,
        race_id: str,
        race_data: pd.DataFrame,
        current_budget: float,
        strategy: str
    ) -> Optional[Dict[str, Any]]:
        """1レースを処理"""
        
        # 予算が最低購入額未満なら終了
        if current_budget < self.recommender.min_bet_amount:
            return None
        
        # 予測実行
        predictions = self.orchestrator.predict_race(race_data)
        
        # EV計算
        positive_ev_bets = self.ev_calculator.find_positive_ev_bets(predictions)
        
        # 買い目推奨
        self.recommender.total_budget = current_budget
        recommendations = self.recommender.generate_recommendations(
            positive_ev_bets,
            strategy=strategy
        )
        
        bets_placed = recommendations.get('recommendations', [])
        
        if not bets_placed:
            return {
                'race_id': race_id,
                'race_date': str(race_data['race_date'].iloc[0]) if 'race_date' in race_data.columns else '',
                'bets_placed': [],
                'hits': [],
                'investment': 0,
                'payout': 0,
                'profit': 0,
                'roi': 0,
                'budget_after': current_budget
            }
        
        # 的中判定と払戻計算
        total_investment = sum(bet['bet_amount'] for bet in bets_placed)
        total_payout = 0
        hits = []
        
        for bet in bets_placed:
            payout = self.calculate_payout(bet, race_data)
            if payout > 0:
                hits.append({**bet, 'payout': payout})
                total_payout += payout
        
        profit = total_payout - total_investment
        roi = (profit / total_investment) if total_investment > 0 else 0
        
        return {
            'race_id': race_id,
            'race_date': str(race_data['race_date'].iloc[0]) if 'race_date' in race_data.columns else '',
            'bets_placed': bets_placed,
            'hits': hits,
            'investment': total_investment,
            'payout': total_payout,
            'profit': profit,
            'roi': roi,
            'budget_after': current_budget - total_investment + total_payout
        }
    
    def calculate_payout(
        self,
        bet: Dict[str, Any],
        race_data: pd.DataFrame
    ) -> float:
        """購入した馬券の払戻額を計算"""
        
        bet_type = bet.get('bet_type', '')
        bet_horses = bet.get('horses', [])
        bet_amount = bet.get('bet_amount', 0)
        bet_odds = bet.get('odds', 1.0)
        
        if 'finish_position' not in race_data.columns:
            return 0
        
        # 着順を取得
        horse_positions = {}
        for _, row in race_data.iterrows():
            horse_num = int(row.get('horse_number', 0))
            finish_pos = int(row.get('finish_position', 99))
            horse_positions[horse_num] = finish_pos
        
        # 的中判定
        is_hit = False
        
        if bet_type == 'win':
            # 単勝: 1着のみ
            if len(bet_horses) == 1:
                is_hit = horse_positions.get(bet_horses[0], 99) == 1
        
        elif bet_type == 'place':
            # 複勝: 3着以内
            if len(bet_horses) == 1:
                is_hit = horse_positions.get(bet_horses[0], 99) <= 3
        
        elif bet_type == 'wide':
            # ワイド: 2頭とも3着以内
            if len(bet_horses) == 2:
                pos1 = horse_positions.get(bet_horses[0], 99)
                pos2 = horse_positions.get(bet_horses[1], 99)
                is_hit = pos1 <= 3 and pos2 <= 3
        
        elif bet_type == 'quinella':
            # 馬連: 2頭が1-2着（順不同）
            if len(bet_horses) == 2:
                pos1 = horse_positions.get(bet_horses[0], 99)
                pos2 = horse_positions.get(bet_horses[1], 99)
                is_hit = {pos1, pos2} == {1, 2}
        
        elif bet_type == 'trifecta':
            # 3連複: 3頭が1-2-3着（順不同）
            if len(bet_horses) == 3:
                positions = [horse_positions.get(h, 99) for h in bet_horses]
                is_hit = set(positions) == {1, 2, 3}
        
        if is_hit:
            return bet_amount * bet_odds
        
        return 0
    
    def aggregate_results(
        self,
        race_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """全レース結果を集計"""
        
        if not race_results:
            return {
                'total_races': 0,
                'total_investment': 0,
                'total_payout': 0,
                'net_profit': 0,
                'recovery_rate': 0,
                'roi': 0
            }
        
        total_investment = sum(r['investment'] for r in race_results)
        total_payout = sum(r['payout'] for r in race_results)
        net_profit = total_payout - total_investment
        
        recovery_rate = (total_payout / total_investment * 100) if total_investment > 0 else 0
        roi = (net_profit / total_investment * 100) if total_investment > 0 else 0
        
        total_bets = sum(len(r['bets_placed']) for r in race_results)
        total_hits = sum(len(r['hits']) for r in race_results)
        hit_rate = (total_hits / total_bets * 100) if total_bets > 0 else 0
        
        return {
            'total_races': len(race_results),
            'total_bets': total_bets,
            'total_hits': total_hits,
            'hit_rate': round(hit_rate, 2),
            'total_investment': round(total_investment, 0),
            'total_payout': round(total_payout, 0),
            'net_profit': round(net_profit, 0),
            'recovery_rate': round(recovery_rate, 2),
            'roi': round(roi, 2)
        }
