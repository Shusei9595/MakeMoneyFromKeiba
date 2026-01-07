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
    - 騎手の全体勝率（現在は代替特徴量を使用）
    - 調教師の全体勝率（現在は代替特徴量を使用）
    - 騎手×馬の相性（現在は代替特徴量を使用）
    
    注意: 現在のデータセットには騎手・調教師の統計が不足しているため、
    馬の成績ベースの代替特徴量を使用しています。
    """
    
    def __init__(self, version: str = "v1"):
        super().__init__(name="jockey_trainer_agent", version=version)
    
    def _get_feature_list(self) -> List[str]:
        """騎手・調教師分析に使用する特徴量（代替版）"""
        # 騎手・調教師の直接的な統計がないため、
        # 馬の成績から間接的に評価する特徴量を使用
        return [
            # 馬の成績（騎手の影響を反映）
            'career_win_rate',
            'career_place_rate',
            'career_show_rate',
            'career_total_races',
            'career_total_wins',
            
            # 最近の調子（調教師の仕上げを反映）
            'recent_form_score',
            'recent_3_win_count',
            'consistency_score',
            
            # レース経験
            'track_win_rate',
            'track_experience_count'
        ]

