"""
Race Pace Agent

レースペース・展開を分析するエージェント
"""
from typing import List
from .base_agent import BaseAgent


class RacePaceAgent(BaseAgent):
    """
    レースペース分析AI
    
    責任: 展開予想とペース適性を評価
    
    評価観点:
    - 脚質（逃げ/先行/差し/追込）
    - ラスト3ハロンのタイム
    - 速度トレンド
    """
    
    def __init__(self, version: str = "v1"):
        super().__init__(name="race_pace_agent", version=version)
    
    def _get_feature_list(self) -> List[str]:
        """ペース分析に使用する特徴量"""
        return [
            # 速度関連
            'speed',
            'recent_3_avg_speed',
            'speed_trend_slope',
            
            # タイム関連
            'finish_time',
            'last_3f_time',
            
            # 一貫性
            'consistency_score',
            'recent_3_finish_variance',
            
            # 距離
            'distance'
        ]
