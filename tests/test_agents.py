"""
エージェントモジュールのテスト
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import tempfile

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

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


@pytest.fixture
def sample_training_data():
    """テスト用のサンプルデータ"""
    np.random.seed(42)
    n = 100
    
    data = {
        'race_id': [f'2024010{i % 10}0101' for i in range(n)],
        'horse_id': [f'H{i % 20:03d}' for i in range(n)],
        'finish_position': np.random.randint(1, 15, n),
        
        # 過去成績特徴量
        'recent_3_avg_speed': np.random.uniform(15, 20, n),
        'recent_3_finish_variance': np.random.uniform(0, 5, n),
        'last_race_position': np.random.randint(1, 15, n),
        'recent_3_win_count': np.random.randint(0, 3, n),
        'recent_5_avg_odds': np.random.uniform(5, 50, n),
        'speed_trend_slope': np.random.uniform(-0.5, 0.5, n),
        'consistency_score': np.random.uniform(0.1, 1.0, n),
        'days_since_last_race': np.random.randint(7, 90, n),
        'career_win_rate': np.random.uniform(0, 0.3, n),
        'career_place_rate': np.random.uniform(0, 0.5, n),
        'career_show_rate': np.random.uniform(0, 0.6, n),
        'career_total_races': np.random.randint(1, 50, n),
        'recent_form_score': np.random.uniform(0.1, 0.5, n),
        
        # 距離特徴量
        'distance': np.random.choice([1200, 1600, 1800, 2000], n),
        'distance_experience_count': np.random.randint(0, 10, n),
        'distance_win_rate': np.random.uniform(0, 0.3, n),
        'distance_wins': np.random.randint(0, 5, n),
        'track_experience_count': np.random.randint(0, 10, n),
        'track_win_rate': np.random.uniform(0, 0.3, n),
        'track_wins': np.random.randint(0, 5, n),
        'track_type_win_rate': np.random.uniform(0, 0.3, n),
        'track_type_experience': np.random.randint(0, 10, n),
        'track_type_encoded': np.random.randint(0, 2, n),
        'distance_change': np.random.uniform(-200, 200, n),
        'distance_adaptability_score': np.random.uniform(0.5, 1.0, n),
        'last_race_distance': np.random.choice([1200, 1600, 1800], n),
        'track_name_encoded': np.random.randint(0, 10, n),
        
        # 騎手・調教師特徴量
        'jockey_win_rate_overall': np.random.uniform(0.05, 0.2, n),
        'jockey_wins': np.random.randint(0, 100, n),
        'jockey_race_count': np.random.randint(10, 500, n),
        'trainer_win_rate_overall': np.random.uniform(0.05, 0.15, n),
        'trainer_wins': np.random.randint(0, 50, n),
        'trainer_race_count': np.random.randint(10, 300, n),
        'jockey_horse_combination_count': np.random.randint(0, 10, n),
        'jockey_horse_combination_wins': np.random.randint(0, 3, n),
        
        # ペース特徴量
        'speed': np.random.uniform(15, 20, n),
        'finish_time': np.random.uniform(70, 130, n),
        'last_3f_time': np.random.uniform(33, 40, n),
        
        # 馬体特徴量
        'horse_weight': np.random.uniform(440, 520, n),
        'relative_weight': np.random.uniform(-20, 20, n),
        'weight': np.random.uniform(54, 58, n),
        'weight_advantage': np.random.uniform(-2, 2, n),
        
        # 馬場特徴量
        'track_condition_encoded': np.random.randint(0, 4, n),
        'month': np.random.randint(1, 13, n),
        'season': np.random.choice(['spring', 'summer', 'autumn', 'winter'], n),
        'is_weekend': np.random.randint(0, 2, n),
        
        # オッズ特徴量
        'odds': np.random.uniform(1.5, 100, n),
        'popularity': np.random.randint(1, 16, n),
        'relative_odds': np.random.uniform(-30, 30, n),
        'odds_rank': np.random.randint(1, 16, n),
        'odds_normalized': np.random.uniform(-2, 2, n)
    }
    
    df = pd.DataFrame(data)
    df['target_score'] = df['finish_position'].apply(BaseAgent.create_target_score)
    
    return df


class TestBaseAgent:
    """BaseAgentのテスト"""
    
    def test_create_target_score_1st(self):
        """1着のスコアが10.0であること"""
        assert BaseAgent.create_target_score(1) == 10.0
    
    def test_create_target_score_2nd(self):
        """2着のスコアが8.5であること"""
        assert BaseAgent.create_target_score(2) == 8.5
    
    def test_create_target_score_3rd(self):
        """3着のスコアが7.0であること"""
        assert BaseAgent.create_target_score(3) == 7.0
    
    def test_create_target_score_range(self):
        """全着順のスコアが1.0〜10.0の範囲内であること"""
        for pos in range(1, 19):
            score = BaseAgent.create_target_score(pos)
            assert 1.0 <= score <= 10.0, f"Position {pos} score {score} out of range"
    
    def test_create_target_score_nan(self):
        """欠損値のスコアが5.0であること"""
        assert BaseAgent.create_target_score(np.nan) == 5.0


class TestAllAgents:
    """全エージェントの共通テスト"""
    
    @pytest.fixture
    def all_agents(self):
        """全エージェントのリスト"""
        return [
            PastPerformanceAgent(),
            DistanceAdaptabilityAgent(),
            JockeyTrainerAgent(),
            PedigreeAgent(),
            RacePaceAgent(),
            PhysicalConditionAgent(),
            TrackConditionAgent(),
            StatisticalPatternAgent(),
            OddsAnalysisAgent()
        ]
    
    def test_all_agents_instantiate(self, all_agents):
        """全エージェントがインスタンス化できること"""
        assert len(all_agents) == 9
        for agent in all_agents:
            assert agent is not None
            assert agent.name is not None
            assert agent.is_trained is False
    
    def test_all_agents_have_feature_list(self, all_agents):
        """全エージェントが特徴量リストを持つこと"""
        for agent in all_agents:
            features = agent._get_feature_list()
            assert isinstance(features, list)
            assert len(features) > 0, f"{agent.name} has no features"
    
    def test_all_agents_train_and_predict(self, all_agents, sample_training_data):
        """全エージェントが訓練と予測ができること"""
        for agent in all_agents:
            y = sample_training_data['target_score']
            
            # 訓練
            metrics = agent.train(sample_training_data, y, n_folds=2)
            
            assert agent.is_trained is True
            assert 'rmse' in metrics
            assert 'mae' in metrics
            assert 'r2' in metrics
            
            # 予測
            predictions = agent.predict(sample_training_data)
            
            assert len(predictions) == len(sample_training_data)
            assert all(1.0 <= p <= 10.0 for p in predictions), f"{agent.name} predictions out of range"
    
    def test_all_agents_save_load(self, all_agents, sample_training_data):
        """全エージェントが保存・読み込みできること"""
        for agent in all_agents:
            y = sample_training_data['target_score']
            agent.train(sample_training_data, y, n_folds=2)
            
            with tempfile.TemporaryDirectory() as tmpdir:
                # 保存
                filepath = agent.save_model(Path(tmpdir))
                assert filepath.exists()
                
                # 新しいインスタンスで読み込み
                new_agent = type(agent)()
                new_agent.load_model(filepath)
                
                assert new_agent.is_trained is True
                assert new_agent.name == agent.name
    
    def test_all_agents_feature_importance(self, all_agents, sample_training_data):
        """全エージェントが特徴量重要度を取得できること"""
        for agent in all_agents:
            y = sample_training_data['target_score']
            agent.train(sample_training_data, y, n_folds=2)
            
            importance = agent.get_feature_importance()
            
            assert isinstance(importance, pd.DataFrame)
            assert 'feature' in importance.columns
            assert 'importance' in importance.columns
            assert len(importance) > 0


class TestPastPerformanceAgent:
    """PastPerformanceAgentの個別テスト"""
    
    def test_feature_list_contains_expected(self):
        """期待される特徴量が含まれていること"""
        agent = PastPerformanceAgent()
        features = agent._get_feature_list()
        
        assert 'recent_3_avg_speed' in features
        assert 'career_win_rate' in features
        assert 'consistency_score' in features


class TestDistanceAdaptabilityAgent:
    """DistanceAdaptabilityAgentの個別テスト"""
    
    def test_feature_list_contains_expected(self):
        """期待される特徴量が含まれていること"""
        agent = DistanceAdaptabilityAgent()
        features = agent._get_feature_list()
        
        assert 'distance_win_rate' in features
        assert 'track_win_rate' in features


class TestOddsAnalysisAgent:
    """OddsAnalysisAgentの個別テスト"""
    
    def test_feature_list_contains_expected(self):
        """期待される特徴量が含まれていること"""
        agent = OddsAnalysisAgent()
        features = agent._get_feature_list()
        
        assert 'odds' in features
        assert 'popularity' in features
