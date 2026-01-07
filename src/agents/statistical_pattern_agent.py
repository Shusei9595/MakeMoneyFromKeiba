"""
Statistical Pattern Agent

統計パターン分析を行うエージェント
"""
from typing import List
from .base_agent import BaseAgent


class StatisticalPatternAgent(BaseAgent):
    """
    統計パターン分析AI
    
    責任: 統計的パターン、ラップタイム分析、隠れた相関を検出
    
    評価観点:
    - タイムの分散・一貫性
    - レース展開パターン
    - 統計的な異常検出
    """
    
    def __init__(self, version: str = "v1"):
        super().__init__(name="statistical_pattern_agent", version=version)
    
    def _get_feature_list(self) -> List[str]:
        """統計パターン分析に使用する特徴量"""
        return [
            # タイム関連
            'finish_time',
            'last_3f_time',
            'speed',
            
            # 分散・一貫性
            'recent_3_finish_variance',
            'consistency_score',
            'speed_trend_slope',
            
            # 相対指標
            'relative_odds',
            'relative_weight',
            'odds_rank',
            
            # 統計的特徴
            'career_total_races',
            'career_win_rate',
            'recent_form_score'
        ]
