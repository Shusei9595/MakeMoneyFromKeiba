"""
Past Performance Agent

過去成績から馬の調子を分析するエージェント
"""
from typing import List
from .base_agent import BaseAgent


class PastPerformanceAgent(BaseAgent):
    """
    過去成績分析AI
    
    責任: 直近の走行パフォーマンスを分析し、調子の良し悪しを評価
    
    評価観点:
    - 直近3〜5走の平均速度・着順
    - 着順の安定性（分散）
    - 速度トレンド（向上中/下降中）
    - 前走からの休養日数
    """
    
    def __init__(self, version: str = "v1"):
        super().__init__(name="past_performance_agent", version=version)
    
    def _get_feature_list(self) -> List[str]:
        """過去成績分析に使用する特徴量"""
        return [
            # 直近成績
            'recent_3_avg_speed',
            'recent_3_finish_variance',
            'last_race_position',
            'recent_3_win_count',
            'recent_5_avg_odds',
            
            # トレンド
            'speed_trend_slope',
            'consistency_score',
            
            # 休養
            'days_since_last_race',
            
            # 累積成績
            'career_win_rate',
            'career_place_rate',
            'career_show_rate',
            'career_total_races',
            
            # 調子スコア
            'recent_form_score'
        ]
