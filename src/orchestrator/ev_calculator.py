"""
EV Calculator Module

券種別に期待値（Expected Value）を計算する
"""
from typing import Dict, List, Tuple, Any, Optional
import logging
from itertools import combinations

import numpy as np
import pandas as pd


class EVCalculator:
    """
    期待値計算クラス
    
    対応券種:
    - 単勝（Win）
    - 複勝（Place）
    - ワイド（Wide）
    - 馬連（Quinella）
    - 3連複（Trifecta）
    """
    
    # EVランク分類閾値
    EV_RANKS = {
        'S': 0.20,  # 20%以上
        'A': 0.15,  # 15%以上
        'B': 0.10,  # 10%以上
        'C': 0.05   # 5%以上
    }
    
    def __init__(self, min_ev_threshold: float = 0.05):
        """
        Args:
            min_ev_threshold: 最小EV閾値（デフォルト5%）
        """
        self.min_ev_threshold = min_ev_threshold
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def calculate_win_ev(
        self, 
        win_probability: float, 
        odds: float
    ) -> float:
        """
        単勝EVを計算
        
        EV = 勝率 × オッズ - 1
        
        Args:
            win_probability: 勝率
            odds: 単勝オッズ
        
        Returns:
            期待値（-1〜∞）
        """
        if pd.isna(odds) or odds <= 0:
            return -1.0
        return win_probability * odds - 1.0
    
    def calculate_place_ev(
        self, 
        place_probability: float, 
        place_odds: float
    ) -> float:
        """
        複勝EVを計算
        
        Args:
            place_probability: 3着内率
            place_odds: 複勝オッズ（平均）
        
        Returns:
            期待値
        """
        if pd.isna(place_odds) or place_odds <= 0:
            return -1.0
        return place_probability * place_odds - 1.0
    
    def calculate_wide_ev(
        self, 
        place_prob_1: float,
        place_prob_2: float,
        wide_odds: float,
        correlation_factor: float = 1.2
    ) -> float:
        """
        ワイドEVを計算
        
        P(両馬が3着内) ≈ place_prob_1 × place_prob_2 × correction_factor
        
        Args:
            place_prob_1: 馬1の3着内率
            place_prob_2: 馬2の3着内率
            wide_odds: ワイドオッズ
            correlation_factor: 相関補正係数
        
        Returns:
            期待値
        """
        if pd.isna(wide_odds) or wide_odds <= 0:
            return -1.0
        
        # 両馬が3着内に入る確率（独立性仮定 + 補正）
        joint_prob = place_prob_1 * place_prob_2 * correlation_factor
        joint_prob = min(joint_prob, 0.9)  # 上限設定
        
        return joint_prob * wide_odds - 1.0
    
    def calculate_quinella_ev(
        self, 
        win_prob_1: float,
        win_prob_2: float,
        quinella_odds: float
    ) -> float:
        """
        馬連EVを計算
        
        P(2頭が1-2着) ≈ 2 × win_prob_1 × win_prob_2 × adjustment
        
        Args:
            win_prob_1: 馬1の勝率
            win_prob_2: 馬2の勝率
            quinella_odds: 馬連オッズ
        
        Returns:
            期待値
        """
        if pd.isna(quinella_odds) or quinella_odds <= 0:
            return -1.0
        
        # 1-2着の確率（順不同）
        joint_prob = 2 * win_prob_1 * win_prob_2 * 1.5  # 調整係数
        joint_prob = min(joint_prob, 0.5)
        
        return joint_prob * quinella_odds - 1.0
    
    def calculate_trifecta_ev(
        self, 
        win_probs: List[float],
        trifecta_odds: float
    ) -> float:
        """
        3連複EVを計算
        
        Args:
            win_probs: 3頭の勝率リスト
            trifecta_odds: 3連複オッズ
        
        Returns:
            期待値
        """
        if pd.isna(trifecta_odds) or trifecta_odds <= 0:
            return -1.0
        
        if len(win_probs) != 3:
            return -1.0
        
        # 3頭が1-2-3着に入る確率（順不同）
        joint_prob = 6 * np.prod(win_probs) * 2.0  # 調整係数
        joint_prob = min(joint_prob, 0.3)
        
        return joint_prob * trifecta_odds - 1.0
    
    def get_ev_rank(self, ev: float) -> str:
        """EVランクを取得"""
        if ev >= self.EV_RANKS['S']:
            return 'S'
        elif ev >= self.EV_RANKS['A']:
            return 'A'
        elif ev >= self.EV_RANKS['B']:
            return 'B'
        elif ev >= self.EV_RANKS['C']:
            return 'C'
        else:
            return '-'
    
    def find_positive_ev_bets(
        self, 
        predictions: pd.DataFrame,
        odds_data: Optional[pd.DataFrame] = None
    ) -> List[Dict[str, Any]]:
        """
        全券種でEV > min_ev_thresholdの馬券を抽出
        
        Args:
            predictions: 予測結果DataFrame
            odds_data: オッズデータDataFrame（オプション）
        
        Returns:
            EV > 0の馬券リスト
        """
        positive_bets = []
        
        # オッズカラムがある場合はそれを使用
        if 'odds' in predictions.columns:
            odds_col = 'odds'
        else:
            self.logger.warning("No odds column found")
            return positive_bets
        
        # 単勝EVを計算
        for idx, row in predictions.iterrows():
            if pd.isna(row.get(odds_col)):
                continue
            
            win_ev = self.calculate_win_ev(
                row['win_probability'], 
                row[odds_col]
            )
            
            if win_ev >= self.min_ev_threshold:
                positive_bets.append({
                    'bet_type': 'win',
                    'horses': [int(row.get('horse_number', idx))],
                    'horse_names': [row.get('horse_name', 'Unknown')],
                    'odds': float(row[odds_col]),
                    'probability': float(row['win_probability']),
                    'ev': float(win_ev),
                    'ev_rank': self.get_ev_rank(win_ev),
                    'confidence': float(row['integrated_score'] / 10.0)
                })
            
            # 複勝EV（オッズ推定）
            place_odds_est = max(1.1, row[odds_col] * 0.35)
            place_ev = self.calculate_place_ev(
                row['place_probability'],
                place_odds_est
            )
            
            if place_ev >= self.min_ev_threshold:
                positive_bets.append({
                    'bet_type': 'place',
                    'horses': [int(row.get('horse_number', idx))],
                    'horse_names': [row.get('horse_name', 'Unknown')],
                    'odds': float(place_odds_est),
                    'probability': float(row['place_probability']),
                    'ev': float(place_ev),
                    'ev_rank': self.get_ev_rank(place_ev),
                    'confidence': float(row['integrated_score'] / 10.0)
                })
        
        # ワイドEVを計算（上位5頭の組み合わせ）
        top_horses = predictions.head(5)
        for (idx1, row1), (idx2, row2) in combinations(top_horses.iterrows(), 2):
            # ワイドオッズを推定
            odds1 = row1.get(odds_col, 10)
            odds2 = row2.get(odds_col, 10)
            wide_odds_est = max(1.5, (odds1 * odds2) ** 0.5 * 0.8)
            
            wide_ev = self.calculate_wide_ev(
                row1['place_probability'],
                row2['place_probability'],
                wide_odds_est
            )
            
            if wide_ev >= self.min_ev_threshold:
                positive_bets.append({
                    'bet_type': 'wide',
                    'horses': [
                        int(row1.get('horse_number', idx1)),
                        int(row2.get('horse_number', idx2))
                    ],
                    'horse_names': [
                        row1.get('horse_name', 'Unknown'),
                        row2.get('horse_name', 'Unknown')
                    ],
                    'odds': float(wide_odds_est),
                    'probability': float(row1['place_probability'] * row2['place_probability'] * 1.2),
                    'ev': float(wide_ev),
                    'ev_rank': self.get_ev_rank(wide_ev),
                    'confidence': float((row1['integrated_score'] + row2['integrated_score']) / 20.0)
                })
        
        # 3連複EV（上位4頭の組み合わせ）
        top_horses_4 = predictions.head(4)
        for combo in combinations(top_horses_4.iterrows(), 3):
            rows = [c[1] for c in combo]
            win_probs = [r['win_probability'] for r in rows]
            
            # 3連複オッズを推定
            odds_product = np.prod([r.get(odds_col, 10) for r in rows])
            trifecta_odds_est = max(3.0, odds_product ** 0.4 * 2.0)
            
            trifecta_ev = self.calculate_trifecta_ev(win_probs, trifecta_odds_est)
            
            if trifecta_ev >= self.min_ev_threshold:
                positive_bets.append({
                    'bet_type': 'trifecta',
                    'horses': [int(r.get('horse_number', 0)) for r in rows],
                    'horse_names': [r.get('horse_name', 'Unknown') for r in rows],
                    'odds': float(trifecta_odds_est),
                    'probability': float(6 * np.prod(win_probs) * 2.0),
                    'ev': float(trifecta_ev),
                    'ev_rank': self.get_ev_rank(trifecta_ev),
                    'confidence': float(sum(r['integrated_score'] for r in rows) / 30.0)
                })
        
        # EVでソート（降順）
        positive_bets.sort(key=lambda x: x['ev'], reverse=True)
        
        return positive_bets
