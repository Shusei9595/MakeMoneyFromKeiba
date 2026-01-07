"""
Evaluation Module Tests
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import tempfile

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.evaluation.performance_evaluator import PerformanceEvaluator
from src.evaluation.report_generator import ReportGenerator, generate_text_summary


@pytest.fixture
def sample_backtest_results():
    """テスト用のバックテスト結果"""
    return {
        'summary': {
            'total_races': 10,
            'total_bets': 25,
            'total_hits': 8,
            'hit_rate': 32.0,
            'total_investment': 100000,
            'total_payout': 108000,
            'net_profit': 8000,
            'recovery_rate': 108.0,
            'roi': 8.0
        },
        'race_results': [
            {'race_id': '1', 'race_date': '2024-01-05', 'investment': 10000, 'payout': 15000, 'profit': 5000, 'bets_placed': [{'bet_type': 'win'}], 'hits': [{'bet_type': 'win'}]},
            {'race_id': '2', 'race_date': '2024-01-05', 'investment': 10000, 'payout': 0, 'profit': -10000, 'bets_placed': [{'bet_type': 'wide'}], 'hits': []},
            {'race_id': '3', 'race_date': '2024-01-06', 'investment': 10000, 'payout': 12000, 'profit': 2000, 'bets_placed': [{'bet_type': 'place'}], 'hits': [{'bet_type': 'place'}]},
            {'race_id': '4', 'race_date': '2024-01-06', 'investment': 10000, 'payout': 8000, 'profit': -2000, 'bets_placed': [{'bet_type': 'win'}], 'hits': []},
            {'race_id': '5', 'race_date': '2024-01-07', 'investment': 10000, 'payout': 20000, 'profit': 10000, 'bets_placed': [{'bet_type': 'trifecta'}], 'hits': [{'bet_type': 'trifecta'}]},
            {'race_id': '6', 'race_date': '2024-02-01', 'investment': 10000, 'payout': 11000, 'profit': 1000, 'bets_placed': [{'bet_type': 'wide'}], 'hits': [{'bet_type': 'wide'}]},
            {'race_id': '7', 'race_date': '2024-02-01', 'investment': 10000, 'payout': 0, 'profit': -10000, 'bets_placed': [{'bet_type': 'win'}], 'hits': []},
            {'race_id': '8', 'race_date': '2024-02-02', 'investment': 10000, 'payout': 14000, 'profit': 4000, 'bets_placed': [{'bet_type': 'place'}], 'hits': [{'bet_type': 'place'}]},
            {'race_id': '9', 'race_date': '2024-02-02', 'investment': 10000, 'payout': 13000, 'profit': 3000, 'bets_placed': [{'bet_type': 'wide'}], 'hits': [{'bet_type': 'wide'}]},
            {'race_id': '10', 'race_date': '2024-02-03', 'investment': 10000, 'payout': 15000, 'profit': 5000, 'bets_placed': [{'bet_type': 'win'}], 'hits': [{'bet_type': 'win'}]},
        ],
        'strategy': 'balanced',
        'final_budget': 108000
    }


class TestPerformanceEvaluator:
    """PerformanceEvaluatorのテスト"""
    
    def test_recovery_rate(self, sample_backtest_results):
        """回収率テスト"""
        evaluator = PerformanceEvaluator(sample_backtest_results)
        assert evaluator.calculate_recovery_rate() == 108.0
    
    def test_roi(self, sample_backtest_results):
        """ROIテスト"""
        evaluator = PerformanceEvaluator(sample_backtest_results)
        assert evaluator.calculate_roi() == 8.0
    
    def test_hit_rate(self, sample_backtest_results):
        """的中率テスト"""
        evaluator = PerformanceEvaluator(sample_backtest_results)
        assert evaluator.calculate_hit_rate() == 32.0
    
    def test_hit_rate_by_type(self, sample_backtest_results):
        """券種別的中率テスト"""
        evaluator = PerformanceEvaluator(sample_backtest_results)
        rates = evaluator.calculate_hit_rate_by_bet_type()
        assert 'win' in rates
        assert 'wide' in rates
    
    def test_max_drawdown(self, sample_backtest_results):
        """最大ドローダウンテスト"""
        evaluator = PerformanceEvaluator(sample_backtest_results)
        max_dd, start, end = evaluator.calculate_max_drawdown()
        assert max_dd >= 0
    
    def test_sharpe_ratio(self, sample_backtest_results):
        """シャープレシオテスト"""
        evaluator = PerformanceEvaluator(sample_backtest_results)
        sharpe = evaluator.calculate_sharpe_ratio()
        assert isinstance(sharpe, float)
    
    def test_win_rate(self, sample_backtest_results):
        """勝率テスト"""
        evaluator = PerformanceEvaluator(sample_backtest_results)
        win_rate = evaluator.calculate_win_rate()
        # 10レース中7レースで利益
        assert win_rate == 70.0
    
    def test_longest_streaks(self, sample_backtest_results):
        """連勝・連敗テスト"""
        evaluator = PerformanceEvaluator(sample_backtest_results)
        
        win_streak = evaluator.get_longest_winning_streak()
        lose_streak = evaluator.get_longest_losing_streak()
        
        assert win_streak >= 1
        assert lose_streak >= 1
    
    def test_all_metrics(self, sample_backtest_results):
        """全指標一括計算テスト"""
        evaluator = PerformanceEvaluator(sample_backtest_results)
        metrics = evaluator.calculate_all_metrics()
        
        assert 'recovery_rate' in metrics
        assert 'roi' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics


class TestReportGenerator:
    """ReportGeneratorのテスト"""
    
    def test_generate_html_report(self, sample_backtest_results):
        """HTMLレポート生成テスト"""
        evaluator = PerformanceEvaluator(sample_backtest_results)
        metrics = evaluator.calculate_all_metrics()
        
        generator = ReportGenerator(sample_backtest_results, metrics)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_report.html"
            generator.generate_html_report(str(output_path))
            
            assert output_path.exists()
            
            content = output_path.read_text(encoding='utf-8')
            assert '競馬予測AI' in content
            assert '回収率' in content
    
    def test_generate_text_summary(self, sample_backtest_results):
        """テキストサマリー生成テスト"""
        evaluator = PerformanceEvaluator(sample_backtest_results)
        metrics = evaluator.calculate_all_metrics()
        
        text = generate_text_summary(metrics, 'balanced')
        
        assert '競馬予測AI' in text
        assert 'balanced' in text
        assert '回収率' in text


class TestIntegration:
    """統合テスト"""
    
    def test_empty_results(self):
        """空の結果でのテスト"""
        empty_results = {
            'summary': {
                'total_races': 0,
                'total_investment': 0,
                'total_payout': 0,
                'net_profit': 0,
                'recovery_rate': 0,
                'roi': 0
            },
            'race_results': [],
            'strategy': 'balanced'
        }
        
        evaluator = PerformanceEvaluator(empty_results)
        metrics = evaluator.calculate_all_metrics()
        
        assert metrics['recovery_rate'] == 0
        assert metrics['total_races'] == 0
