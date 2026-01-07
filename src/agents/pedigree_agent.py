"""
Pedigree Agent

血統分析を行うエージェント
"""
from typing import List
from .base_agent import BaseAgent


class PedigreeAgent(BaseAgent):
    """
    血統分析AI
    
    責任: 血統データから競走馬のポテンシャルを評価
    
    評価観点:
    - 父馬の成績
    - 母馬の成績
    - 血統による距離適性
    
    注意: 現在の特徴量に血統データがないため、代替特徴量を使用
    """
    
    def __init__(self, version: str = "v1"):
        super().__init__(name="pedigree_agent", version=version)
    
    def _get_feature_list(self) -> List[str]:
        """血統分析に使用する特徴量（代替）"""
        # 血統データが不足しているため、関連する代替特徴量を使用
        return [
            # 馬の基本情報（血統の代わり）
            'career_total_races',
            'career_win_rate',
            'career_place_rate',
            'career_show_rate',
            
            # 距離適性（血統による傾向の代替）
            'distance_win_rate',
            'track_type_win_rate',
            
            # 競馬場適性
            'track_win_rate',
            'distance_adaptability_score'
        ]
