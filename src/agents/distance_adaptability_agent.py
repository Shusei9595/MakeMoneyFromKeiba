"""
Distance Adaptability Agent

距離適性を分析するエージェント
"""
from typing import List
from .base_agent import BaseAgent


class DistanceAdaptabilityAgent(BaseAgent):
    """
    距離適性分析AI
    
    責任: 馬の距離適性と今回のレース距離の相性を評価
    
    評価観点:
    - 距離カテゴリ別の過去成績
    - 前走との距離変化
    - 距離経験値
    """
    
    def __init__(self, version: str = "v1"):
        super().__init__(name="distance_adaptability_agent", version=version)
    
    def _get_feature_list(self) -> List[str]:
        """距離適性分析に使用する特徴量"""
        return [
            # 距離経験
            'distance_experience_count',
            'distance_win_rate',
            'distance_wins',
            
            # コース経験
            'track_experience_count',
            'track_win_rate',
            'track_wins',
            
            # トラックタイプ
            'track_type_win_rate',
            'track_type_experience',
            'track_type_encoded',
            
            # 距離適応
            'distance_change',
            'distance_adaptability_score',
            'last_race_distance',
            
            # 基本情報
            'distance',
            'track_name_encoded'
        ]
