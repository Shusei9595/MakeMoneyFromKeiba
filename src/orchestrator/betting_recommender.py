"""
Betting Recommender Module

EV計算結果から最適な買い目を提案し、資金配分を行う
"""
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

import numpy as np


class BettingRecommender:
    """
    買い目推奨システム
    
    責任:
    - EV計算結果から最適な買い目を提案
    - ケリー基準による資金配分
    - リスク分散戦略
    - 出力フォーマット整形
    """
    
    # 戦略別設定
    STRATEGIES = {
        'conservative': {
            'min_ev': 0.15,
            'kelly_multiplier': 0.25,
            'max_single_bet': 0.20,
            'prefer_bet_types': ['place', 'wide'],
            'target_roi': 1.05
        },
        'balanced': {
            'min_ev': 0.10,
            'kelly_multiplier': 0.50,
            'max_single_bet': 0.30,
            'prefer_bet_types': ['wide', 'win', 'trifecta'],
            'target_roi': 1.15
        },
        'aggressive': {
            'min_ev': 0.05,
            'kelly_multiplier': 0.75,
            'max_single_bet': 0.40,
            'prefer_bet_types': ['trifecta', 'win', 'wide'],
            'target_roi': 1.30
        }
    }
    
    def __init__(
        self, 
        total_budget: float = 10000,
        min_bet_amount: float = 100
    ):
        """
        Args:
            total_budget: 総予算
            min_bet_amount: 最小購入額
        """
        self.total_budget = total_budget
        self.min_bet_amount = min_bet_amount
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def generate_recommendations(
        self, 
        positive_ev_bets: List[Dict[str, Any]],
        strategy: str = 'balanced'
    ) -> Dict[str, Any]:
        """
        買い目推奨を生成
        
        Args:
            positive_ev_bets: EV > 0の馬券リスト
            strategy: 戦略（conservative/balanced/aggressive）
        
        Returns:
            推奨結果
        """
        if strategy not in self.STRATEGIES:
            strategy = 'balanced'
        
        config = self.STRATEGIES[strategy]
        
        # 戦略に応じてフィルタリング
        filtered_bets = self.apply_strategy(positive_ev_bets, config)
        
        if not filtered_bets:
            return {
                'total_budget': self.total_budget,
                'allocated_budget': 0,
                'expected_return': 0,
                'expected_profit': 0,
                'roi': 0.0,
                'recommendations': [],
                'risk_level': 'none',
                'strategy_used': strategy
            }
        
        # 資金配分を計算
        recommendations = self.allocate_budget(filtered_bets, config)
        
        # 集計
        allocated = sum(r['bet_amount'] for r in recommendations)
        expected_return = sum(
            r['bet_amount'] * (1 + r['ev']) for r in recommendations
        )
        
        return {
            'total_budget': self.total_budget,
            'allocated_budget': allocated,
            'expected_return': round(expected_return, 0),
            'expected_profit': round(expected_return - allocated, 0),
            'roi': round((expected_return / allocated - 1) * 100, 1) if allocated > 0 else 0,
            'recommendations': recommendations,
            'risk_level': self._assess_risk(recommendations),
            'strategy_used': strategy
        }
    
    def apply_strategy(
        self, 
        bets: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """戦略に応じて馬券をフィルタリング"""
        filtered = []
        
        for bet in bets:
            # EV閾値チェック
            if bet['ev'] < config['min_ev']:
                continue
            
            # 優先券種チェック（優先度を付与）
            if bet['bet_type'] in config['prefer_bet_types']:
                bet['priority'] = config['prefer_bet_types'].index(bet['bet_type'])
            else:
                bet['priority'] = 10
            
            filtered.append(bet)
        
        # 優先度 → EV でソート
        filtered.sort(key=lambda x: (x['priority'], -x['ev']))
        
        return filtered
    
    def allocate_budget(
        self, 
        bets: List[Dict[str, Any]],
        config: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """ケリー基準で資金配分"""
        recommendations = []
        remaining_budget = self.total_budget
        max_single = self.total_budget * config['max_single_bet']
        
        for bet in bets:
            if remaining_budget < self.min_bet_amount:
                break
            
            # ケリー基準で計算
            kelly_bet = self.calculate_kelly_bet(
                bet['probability'],
                bet['odds'],
                remaining_budget
            )
            
            # 調整
            kelly_bet *= config['kelly_multiplier']
            kelly_bet = min(kelly_bet, max_single, remaining_budget)
            kelly_bet = max(kelly_bet, self.min_bet_amount)
            
            # 100円単位に丸める
            kelly_bet = round(kelly_bet / 100) * 100
            
            if kelly_bet >= self.min_bet_amount:
                rec = bet.copy()
                rec['bet_amount'] = kelly_bet
                rec['expected_return'] = round(kelly_bet * (1 + bet['ev']), 0)
                recommendations.append(rec)
                remaining_budget -= kelly_bet
        
        return recommendations
    
    def calculate_kelly_bet(
        self, 
        probability: float, 
        odds: float,
        budget: float
    ) -> float:
        """
        ケリー基準で最適購入額を計算
        
        kelly = (p * odds - 1) / (odds - 1)
        """
        if odds <= 1:
            return 0
        
        kelly_fraction = (probability * odds - 1) / (odds - 1)
        kelly_fraction = max(0, min(kelly_fraction, 1))
        
        return budget * kelly_fraction
    
    def _assess_risk(self, recommendations: List[Dict[str, Any]]) -> str:
        """リスクレベルを評価"""
        if not recommendations:
            return 'none'
        
        avg_ev = np.mean([r['ev'] for r in recommendations])
        total_allocated = sum(r['bet_amount'] for r in recommendations)
        allocation_ratio = total_allocated / self.total_budget
        
        if avg_ev >= 0.2 and allocation_ratio < 0.5:
            return 'low'
        elif avg_ev >= 0.1 or allocation_ratio < 0.7:
            return 'medium'
        else:
            return 'high'
    
    def format_output_text(
        self, 
        recommendations: Dict[str, Any],
        race_info: Optional[Dict[str, Any]] = None
    ) -> str:
        """ユーザー向けテキスト出力を生成"""
        lines = [
            "=" * 50,
            "         競馬予測AI - 買い目推奨",
            "=" * 50
        ]
        
        if race_info:
            lines.append(f"レース: {race_info.get('race_name', 'Unknown')}")
        
        lines.extend([
            f"予算: {recommendations['total_budget']:,.0f}円",
            f"戦略: {recommendations['strategy_used']}",
            "",
            "-" * 50,
            "【推奨買い目】",
            "-" * 50
        ])
        
        for i, rec in enumerate(recommendations['recommendations'], 1):
            bet_type_jp = {
                'win': '単勝',
                'place': '複勝',
                'wide': 'ワイド',
                'quinella': '馬連',
                'trifecta': '3連複'
            }.get(rec['bet_type'], rec['bet_type'])
            
            horses_str = '-'.join(map(str, rec['horses']))
            names_str = ', '.join(rec['horse_names'])
            
            lines.extend([
                f"{i}. {bet_type_jp} {horses_str} ({names_str})",
                f"   オッズ: {rec['odds']:.1f}倍",
                f"   期待値: +{rec['ev']*100:.0f}% ({rec['ev_rank']}ランク)",
                f"   購入額: {rec['bet_amount']:,.0f}円",
                f"   期待リターン: {rec['expected_return']:,.0f}円",
                f"   信頼度: {rec['confidence']*100:.0f}%",
                ""
            ])
        
        lines.extend([
            "-" * 50,
            "【合計】",
            "-" * 50,
            f"購入合計: {recommendations['allocated_budget']:,.0f}円 "
            f"(予算の{recommendations['allocated_budget']/recommendations['total_budget']*100:.0f}%)",
            f"期待リターン: {recommendations['expected_return']:,.0f}円",
            f"期待利益: {recommendations['expected_profit']:+,.0f}円",
            f"期待ROI: {recommendations['roi']:+.1f}%",
            "",
            f"リスクレベル: {recommendations['risk_level']}",
            "=" * 50
        ])
        
        return '\n'.join(lines)
    
    def format_output_json(
        self, 
        recommendations: Dict[str, Any]
    ) -> str:
        """JSON形式で出力"""
        import json
        return json.dumps(recommendations, ensure_ascii=False, indent=2)
