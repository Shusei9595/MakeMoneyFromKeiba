"""
Agent Manager Module

9つの専門家AIを管理し、並列実行でスコアを収集する
"""
from pathlib import Path
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import sys

import pandas as pd
import numpy as np

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agents.base_agent import BaseAgent
from src.agents.past_performance_agent import PastPerformanceAgent
from src.agents.distance_adaptability_agent import DistanceAdaptabilityAgent
from src.agents.jockey_trainer_agent import JockeyTrainerAgent
from src.agents.pedigree_agent import PedigreeAgent
from src.agents.race_pace_agent import RacePaceAgent
from src.agents.physical_condition_agent import PhysicalConditionAgent
from src.agents.track_condition_agent import TrackConditionAgent
from src.agents.statistical_pattern_agent import StatisticalPatternAgent
from src.agents.odds_analysis_agent import OddsAnalysisAgent


class AgentManager:
    """
    9つの専門家AIを管理するクラス
    
    責任:
    - エージェントのロード
    - 並列実行でスコア収集
    - エラーハンドリング
    """
    
    AGENT_CLASSES = [
        PastPerformanceAgent,
        DistanceAdaptabilityAgent,
        JockeyTrainerAgent,
        PedigreeAgent,
        RacePaceAgent,
        PhysicalConditionAgent,
        TrackConditionAgent,
        StatisticalPatternAgent,
        OddsAnalysisAgent
    ]
    
    def __init__(self, model_dir: str = "models"):
        """
        Args:
            model_dir: モデルファイルが格納されているディレクトリ
        """
        self.model_dir = Path(model_dir)
        self.agents: Dict[str, BaseAgent] = {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # エージェントをロード
        self.load_agents()
    
    def load_agents(self) -> Dict[str, BaseAgent]:
        """全エージェントをロード"""
        for AgentClass in self.AGENT_CLASSES:
            agent = AgentClass()
            model_path = self.model_dir / f"{agent.name}_v1.pkl"
            
            try:
                if model_path.exists():
                    agent.load_model(model_path)
                    self.agents[agent.name] = agent
                    self.logger.info(f"Loaded: {agent.name}")
                else:
                    self.logger.warning(f"Model not found: {model_path}")
            except Exception as e:
                self.logger.error(f"Failed to load {agent.name}: {e}")
        
        self.logger.info(f"Loaded {len(self.agents)}/{len(self.AGENT_CLASSES)} agents")
        return self.agents
    
    def predict_parallel(
        self, 
        data: pd.DataFrame,
        max_workers: int = 9
    ) -> Dict[str, np.ndarray]:
        """
        並列でエージェントのスコアを取得
        
        Args:
            data: 予測用データ（前処理済み）
            max_workers: 並列実行数
        
        Returns:
            {agent_name: スコア配列} の辞書
        """
        results: Dict[str, np.ndarray] = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._predict_single, agent, data): name
                for name, agent in self.agents.items()
            }
            
            for future in as_completed(futures):
                agent_name = futures[future]
                try:
                    scores = future.result()
                    if scores is not None:
                        results[agent_name] = scores
                except Exception as e:
                    self.logger.error(f"Prediction failed for {agent_name}: {e}")
        
        return results
    
    def _predict_single(
        self, 
        agent: BaseAgent, 
        data: pd.DataFrame
    ) -> Optional[np.ndarray]:
        """単一エージェントの予測"""
        try:
            return agent.predict(data)
        except Exception as e:
            self.logger.warning(f"{agent.name} prediction error: {e}")
            return None
    
    def get_agent_status(self) -> Dict[str, bool]:
        """各エージェントのロード状態を返す"""
        status = {}
        for AgentClass in self.AGENT_CLASSES:
            agent = AgentClass()
            status[agent.name] = agent.name in self.agents
        return status
    
    def get_loaded_agent_names(self) -> List[str]:
        """ロード済みエージェント名のリストを返す"""
        return list(self.agents.keys())
