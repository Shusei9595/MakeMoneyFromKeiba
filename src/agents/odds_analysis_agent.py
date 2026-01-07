"""
Odds Analysis Agent

オッズ分析を行うエージェント
"""
from typing import List
from .base_agent import BaseAgent


class OddsAnalysisAgent(BaseAgent):
    """
    オッズ分析AI
    
    責任: オッズの歪み、市場心理、過剰評価/過小評価を検出
    
    評価観点:
    - 単勝オッズ
    - 人気順位
    - オッズの相対位置
    - バリューベット検出
    """
    
    def __init__(self, version: str = "v1"):
        super().__init__(name="odds_analysis_agent", version=version)
    
    def _get_feature_list(self) -> List[str]:
        """オッズ分析に使用する特徴量"""
        return [
            # オッズ関連
            'odds',
            'popularity',
            'relative_odds',
            'odds_rank',
            'recent_5_avg_odds',
            
            # 成績との乖離
            'career_win_rate',
            'recent_form_score',
            
            # 正規化オッズ
            'odds_normalized'
        ]
