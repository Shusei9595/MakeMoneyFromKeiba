"""
Track Condition Agent

馬場・天候適性を分析するエージェント
"""
from typing import List
from .base_agent import BaseAgent


class TrackConditionAgent(BaseAgent):
    """
    馬場・天候適性分析AI
    
    責任: 馬場状態、天候、コース適性を評価
    
    評価観点:
    - 馬場状態（良/稍重/重/不良）
    - 芝/ダート適性
    - 競馬場ごとの成績
    """
    
    def __init__(self, version: str = "v1"):
        super().__init__(name="track_condition_agent", version=version)
    
    def _get_feature_list(self) -> List[str]:
        """馬場適性分析に使用する特徴量"""
        return [
            # 馬場状態
            'track_condition_encoded',
            
            # トラックタイプ
            'track_type_encoded',
            'track_type_win_rate',
            
            # 競馬場
            'track_name_encoded',
            'track_win_rate',
            'track_experience_count',
            
            # 日付関連（季節・天候の代替）
            'month',
            'day_of_week',
            'is_weekend'
        ]
