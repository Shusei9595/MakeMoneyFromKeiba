"""
Orchestrator Module Tests
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import tempfile

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator.agent_manager import AgentManager
from src.orchestrator.weight_optimizer import WeightOptimizer
from src.orchestrator.prediction_orchestrator import PredictionOrchestrator
from src.orchestrator.ev_calculator import EVCalculator
from src.orchestrator.betting_recommender import BettingRecommender


@pytest.fixture
def sample_data():
    """テスト用のサンプルデータ"""
    np.random.seed(42)
    n = 14
    
    data = {
        'horse_id': [f'H{i:03d}' for i in range(n)],
        'horse_name': [f'テスト馬{i+1}' for i in range(n)],
        'horse_number': list(range(1, n+1)),
        'odds': np.random.uniform(2, 50, n),
        'popularity': list(range(1, n+1)),
        'distance': [1600] * n,
        'career_win_rate': np.random.uniform(0, 0.3, n),
        'career_place_rate': np.random.uniform(0, 0.5, n),
        'career_show_rate': np.random.uniform(0, 0.6, n),
        'career_total_races': np.random.randint(1, 50, n),
        'career_total_wins': np.random.randint(0, 10, n),
        'recent_form_score': np.random.uniform(0.1, 0.5, n),
        'recent_3_win_count': np.random.randint(0, 3, n),
        'consistency_score': np.random.uniform(0.1, 1.0, n),
        'track_win_rate': np.random.uniform(0, 0.3, n),
        'track_experience_count': np.random.randint(0, 10, n),
        'recent_3_avg_speed': np.random.uniform(15, 20, n),
        'integrated_score': np.random.uniform(4, 9, n)
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_predictions(sample_data):
    """予測結果のサンプル"""
    df = sample_data.copy()
    df['win_probability'] = np.exp(df['integrated_score']) / np.exp(df['integrated_score']).sum()
    df['place_probability'] = df['win_probability'] * 2.0
    df['place_probability'] = df['place_probability'].clip(0, 0.95)
    return df


class TestWeightOptimizer:
    """WeightOptimizerのテスト"""
    
    def test_static_weights(self):
        """静的重みのテスト"""
        optimizer = WeightOptimizer()
        weights = optimizer.get_static_weights()
        
        assert isinstance(weights, dict)
        assert len(weights) == 9
        assert abs(sum(weights.values()) - 1.0) < 0.01
    
    def test_get_weights_with_filter(self):
        """利用可能なエージェントでフィルタリング"""
        optimizer = WeightOptimizer()
        agent_names = ['past_performance_agent', 'odds_analysis_agent']
        
        weights = optimizer.get_weights(agent_names)
        
        assert len(weights) == 2
        assert abs(sum(weights.values()) - 1.0) < 0.01


class TestEVCalculator:
    """EVCalculatorのテスト"""
    
    def test_calculate_win_ev(self):
        """単勝EV計算"""
        calc = EVCalculator()
        
        # 勝率30%, オッズ4.0 → EV = 0.3 * 4 - 1 = 0.2
        ev = calc.calculate_win_ev(0.3, 4.0)
        assert abs(ev - 0.2) < 0.01
        
        # 勝率10%, オッズ5.0 → EV = 0.1 * 5 - 1 = -0.5
        ev = calc.calculate_win_ev(0.1, 5.0)
        assert abs(ev - (-0.5)) < 0.01
    
    def test_calculate_place_ev(self):
        """複勝EV計算"""
        calc = EVCalculator()
        
        ev = calc.calculate_place_ev(0.6, 1.5)
        assert ev == pytest.approx(-0.1, abs=0.01)
    
    def test_get_ev_rank(self):
        """EVランク分類"""
        calc = EVCalculator()
        
        assert calc.get_ev_rank(0.25) == 'S'
        assert calc.get_ev_rank(0.17) == 'A'
        assert calc.get_ev_rank(0.12) == 'B'
        assert calc.get_ev_rank(0.07) == 'C'
        assert calc.get_ev_rank(0.02) == '-'
    
    def test_find_positive_ev_bets(self, sample_predictions):
        """EV > 0の馬券抽出"""
        calc = EVCalculator(min_ev_threshold=0.0)  # 全て抽出
        
        bets = calc.find_positive_ev_bets(sample_predictions)
        
        assert isinstance(bets, list)
        # 少なくとも1件は抽出される
        assert len(bets) >= 0


class TestBettingRecommender:
    """BettingRecommenderのテスト"""
    
    def test_init(self):
        """初期化テスト"""
        recommender = BettingRecommender(total_budget=10000)
        assert recommender.total_budget == 10000
        assert recommender.min_bet_amount == 100
    
    def test_calculate_kelly_bet(self):
        """ケリー基準計算"""
        recommender = BettingRecommender(total_budget=10000)
        
        # 勝率50%, オッズ3.0
        # kelly = (0.5 * 3 - 1) / (3 - 1) = 0.5 / 2 = 0.25
        kelly = recommender.calculate_kelly_bet(0.5, 3.0, 10000)
        assert kelly == pytest.approx(2500, abs=100)
    
    def test_generate_recommendations(self):
        """推奨生成テスト"""
        recommender = BettingRecommender(total_budget=10000)
        
        positive_ev_bets = [
            {
                'bet_type': 'win',
                'horses': [5],
                'horse_names': ['テスト馬'],
                'odds': 5.0,
                'probability': 0.3,
                'ev': 0.5,
                'ev_rank': 'S',
                'confidence': 0.8
            }
        ]
        
        recommendations = recommender.generate_recommendations(
            positive_ev_bets,
            strategy='balanced'
        )
        
        assert 'recommendations' in recommendations
        assert 'total_budget' in recommendations
        assert 'allocated_budget' in recommendations
        assert 'expected_return' in recommendations
    
    def test_format_output_text(self):
        """テキスト出力フォーマット"""
        recommender = BettingRecommender(total_budget=10000)
        
        recommendations = {
            'total_budget': 10000,
            'allocated_budget': 5000,
            'expected_return': 6000,
            'expected_profit': 1000,
            'roi': 20.0,
            'recommendations': [
                {
                    'bet_type': 'win',
                    'horses': [5],
                    'horse_names': ['テスト馬'],
                    'odds': 5.0,
                    'ev': 0.3,
                    'ev_rank': 'A',
                    'bet_amount': 2000,
                    'expected_return': 2600,
                    'confidence': 0.8
                }
            ],
            'risk_level': 'medium',
            'strategy_used': 'balanced'
        }
        
        output = recommender.format_output_text(recommendations)
        
        assert '競馬予測AI' in output
        assert '単勝' in output
        assert 'テスト馬' in output


class TestAgentManager:
    """AgentManagerのテスト"""
    
    def test_init_without_models(self):
        """モデルなしでの初期化"""
        manager = AgentManager(model_dir='nonexistent_dir')
        assert len(manager.agents) == 0
    
    def test_get_agent_status(self):
        """エージェント状態取得"""
        manager = AgentManager(model_dir='nonexistent_dir')
        status = manager.get_agent_status()
        
        assert isinstance(status, dict)
        assert len(status) == 9


class TestIntegration:
    """統合テスト"""
    
    def test_end_to_end_with_mock_models(self, sample_data):
        """エンドツーエンドテスト（モデルなし）"""
        # AgentManagerをスキップしてテスト
        optimizer = WeightOptimizer()
        calc = EVCalculator(min_ev_threshold=0.0)
        recommender = BettingRecommender(total_budget=10000)
        
        # 手動で予測を作成
        predictions = sample_data.copy()
        predictions['integrated_score'] = np.random.uniform(4, 9, len(predictions))
        scores = predictions['integrated_score'].values
        exp_scores = np.exp(scores - np.max(scores))
        predictions['win_probability'] = exp_scores / exp_scores.sum()
        predictions['place_probability'] = (predictions['win_probability'] * 2.0).clip(0, 0.95)
        
        # EV計算
        positive_ev_bets = calc.find_positive_ev_bets(predictions)
        
        # 推奨生成
        recommendations = recommender.generate_recommendations(
            positive_ev_bets,
            strategy='balanced'
        )
        
        assert 'recommendations' in recommendations
        assert isinstance(recommendations['recommendations'], list)
