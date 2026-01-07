"""
Jockey Trainer Agent

騎手・調教師を分析するエージェント
"""
from typing import List
from .base_agent import BaseAgent


class JockeyTrainerAgent(BaseAgent):
    """
    騎手・調教師分析AI
    
    責任: 騎手と調教師の能力、コンビネーション相性を評価
    
    評価観点:
    - 騎手の全体勝率
    - 調教師の全体勝率
    - 騎手×馬の相性
    """
    
    def __init__(self, version: str = "v1"):
        super().__init__(name="jockey_trainer_agent", version=version)
    
    def _get_feature_list(self) -> List[str]:
        """騎手・調教師分析に使用する特徴量"""
        return [
            # 騎手成績
            'jockey_win_rate_overall',
            'jockey_wins',
            'jockey_race_count',
            
            # 調教師成績
            'trainer_win_rate_overall',
            'trainer_wins',
            'trainer_race_count',
            
            # 騎手×馬コンビ
            'jockey_horse_combination_count',
            'jockey_horse_combination_wins'
        ]
