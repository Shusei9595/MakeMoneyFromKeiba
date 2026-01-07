"""
Physical Condition Agent

馬体・コンディション分析を行うエージェント
"""
from typing import List
from .base_agent import BaseAgent


class PhysicalConditionAgent(BaseAgent):
    """
    馬体・コンディション分析AI
    
    責任: 馬体重、体調、仕上がりを評価
    
    評価観点:
    - 馬体重と変動
    - 斤量
    - 相対的な体重ポジション
    """
    
    def __init__(self, version: str = "v1"):
        super().__init__(name="physical_condition_agent", version=version)
    
    def _get_feature_list(self) -> List[str]:
        """馬体分析に使用する特徴量"""
        return [
            # 体重関連
            'horse_weight',
            'relative_weight',
            'weight',  # 斤量
            'weight_advantage',
            
            # 休養
            'days_since_last_race',
            
            # 調子
            'recent_form_score',
            'consistency_score'
        ]
