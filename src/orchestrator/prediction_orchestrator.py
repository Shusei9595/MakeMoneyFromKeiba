"""
Prediction Orchestrator Module

エージェントスコアを統合し、勝率・3着内率を算出する
"""
from typing import Dict, List, Tuple, Any, Optional
import logging
import json

import numpy as np
import pandas as pd

from .agent_manager import AgentManager
from .weight_optimizer import WeightOptimizer


class PredictionOrchestrator:
    """
    予測オーケストレーター
    
    責任:
    - AgentManagerとWeightOptimizerの統合
    - 統合スコアの計算
    - 勝率・3着内率の算出
    """
    
    def __init__(
        self, 
        agent_manager: AgentManager,
        weight_optimizer: WeightOptimizer,
        use_dynamic_weights: bool = False
    ):
        """
        Args:
            agent_manager: エージェント管理インスタンス
            weight_optimizer: 重み最適化インスタンス
            use_dynamic_weights: 動的重みを使用するか
        """
        self.agent_manager = agent_manager
        self.weight_optimizer = weight_optimizer
        self.use_dynamic_weights = use_dynamic_weights
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def predict_race(
        self, 
        data: pd.DataFrame
    ) -> pd.DataFrame:
        """
        レース予測を実行
        
        Args:
            data: 前処理済みデータ
        
        Returns:
            予測結果DataFrame
        """
        self.logger.info(f"Predicting for {len(data)} horses")
        
        # 1. 各エージェントのスコアを並列取得
        agent_scores = self.agent_manager.predict_parallel(data)
        
        if not agent_scores:
            raise RuntimeError("No agent predictions available")
        
        self.logger.info(f"Got scores from {len(agent_scores)} agents")
        
        # 2. 重みを取得
        agent_names = list(agent_scores.keys())
        weights = self.weight_optimizer.get_weights(agent_names)
        
        # 3. 統合スコアを計算
        integrated_scores = self.calculate_integrated_score(agent_scores, weights)
        
        # 4. 勝率・3着内率を算出
        win_probs, place_probs = self.score_to_probability(integrated_scores)
        
        # 5. 結果DataFrameを構築
        result = data[['horse_id', 'horse_name', 'horse_number', 'odds', 'popularity']].copy() \
            if all(c in data.columns for c in ['horse_id', 'horse_name']) else data.copy()
        
        result['integrated_score'] = integrated_scores
        result['win_probability'] = win_probs
        result['place_probability'] = place_probs
        
        # 各エージェントのスコアを追加
        for agent_name, scores in agent_scores.items():
            short_name = agent_name.replace('_agent', '')
            result[f'score_{short_name}'] = scores
        
        # 重み情報を追加
        result['weights_used'] = json.dumps(weights)
        
        # スコアでソート（降順）
        result = result.sort_values('integrated_score', ascending=False)
        
        return result
    
    def calculate_integrated_score(
        self, 
        agent_scores: Dict[str, np.ndarray],
        weights: Dict[str, float]
    ) -> np.ndarray:
        """
        加重平均で統合スコアを計算
        
        Args:
            agent_scores: {エージェント名: スコア配列}
            weights: {エージェント名: 重み}
        
        Returns:
            統合スコア配列
        """
        # データ長を取得
        sample_scores = next(iter(agent_scores.values()))
        n = len(sample_scores)
        
        integrated = np.zeros(n)
        total_weight = 0.0
        
        for agent_name, scores in agent_scores.items():
            weight = weights.get(agent_name, 0.0)
            if weight > 0 and scores is not None:
                integrated += weight * np.array(scores)
                total_weight += weight
        
        # 正規化
        if total_weight > 0:
            integrated /= total_weight
        
        return integrated
    
    def score_to_probability(
        self, 
        scores: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        統合スコアから勝率・3着内率を算出
        
        Args:
            scores: 統合スコア配列
        
        Returns:
            (勝率配列, 3着内率配列)
        """
        # Softmax正規化で勝率を計算
        # スコアをスケーリング（温度パラメータ）
        temperature = 1.0
        scaled_scores = np.array(scores) / temperature
        
        # Softmax
        exp_scores = np.exp(scaled_scores - np.max(scaled_scores))
        win_probs = exp_scores / exp_scores.sum()
        
        # 3着内率の計算
        # 上位スコアの馬ほど3着内確率が高い
        n = len(scores)
        sorted_indices = np.argsort(scores)[::-1]
        
        place_probs = np.zeros(n)
        
        # 累積確率を割り当て
        # トップ3の累積確率を各馬のランクに基づいて配分
        for rank, idx in enumerate(sorted_indices):
            if rank == 0:
                place_probs[idx] = min(0.95, win_probs[idx] * 2.5)
            elif rank == 1:
                place_probs[idx] = min(0.90, win_probs[idx] * 2.2)
            elif rank == 2:
                place_probs[idx] = min(0.85, win_probs[idx] * 2.0)
            else:
                # 4位以下は勝率に基づく減衰
                decay = 0.7 ** (rank - 2)
                place_probs[idx] = min(0.5, win_probs[idx] * 1.8 * decay)
        
        return win_probs, place_probs
    
    def get_prediction_summary(
        self, 
        predictions: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        予測サマリーを取得
        
        Args:
            predictions: 予測結果DataFrame
        
        Returns:
            サマリー情報
        """
        top3 = predictions.head(3)
        
        return {
            'total_horses': len(predictions),
            'top_pick': {
                'horse_name': top3.iloc[0].get('horse_name', 'Unknown'),
                'horse_number': int(top3.iloc[0].get('horse_number', 0)),
                'score': float(top3.iloc[0]['integrated_score']),
                'win_probability': float(top3.iloc[0]['win_probability'])
            },
            'top3': [
                {
                    'horse_name': row.get('horse_name', 'Unknown'),
                    'horse_number': int(row.get('horse_number', 0)),
                    'score': float(row['integrated_score']),
                    'win_probability': float(row['win_probability'])
                }
                for _, row in top3.iterrows()
            ],
            'score_range': {
                'max': float(predictions['integrated_score'].max()),
                'min': float(predictions['integrated_score'].min()),
                'mean': float(predictions['integrated_score'].mean())
            }
        }
