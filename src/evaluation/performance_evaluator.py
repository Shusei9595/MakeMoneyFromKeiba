"""
Performance Evaluator Module

バックテスト結果から各種評価指標を計算する
"""
from typing import Dict, List, Tuple, Any
import logging

import numpy as np
import pandas as pd


class PerformanceEvaluator:
    """
    パフォーマンス評価クラス
    
    評価指標:
    - 収益性: 回収率、ROI、純利益
    - 的中率: 全体、券種別
    - リスク: 最大ドローダウン、シャープレシオ、ソルティノレシオ
    - 安定性: 月次勝率、連勝/連敗、変動係数
    """
    
    def __init__(self, backtest_results: Dict[str, Any]):
        """
        Args:
            backtest_results: Backtesterの実行結果
        """
        self.results = backtest_results
        self.race_results = backtest_results.get('race_results', [])
        self.summary = backtest_results.get('summary', {})
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def calculate_recovery_rate(self) -> float:
        """回収率を計算"""
        return self.summary.get('recovery_rate', 0)
    
    def calculate_roi(self) -> float:
        """ROIを計算"""
        return self.summary.get('roi', 0)
    
    def calculate_hit_rate(self) -> float:
        """的中率を計算"""
        return self.summary.get('hit_rate', 0)
    
    def calculate_hit_rate_by_bet_type(self) -> Dict[str, float]:
        """券種別的中率を計算"""
        bet_type_stats = {}
        
        for race in self.race_results:
            for bet in race.get('bets_placed', []):
                bet_type = bet.get('bet_type', 'unknown')
                if bet_type not in bet_type_stats:
                    bet_type_stats[bet_type] = {'total': 0, 'hits': 0}
                bet_type_stats[bet_type]['total'] += 1
            
            for hit in race.get('hits', []):
                bet_type = hit.get('bet_type', 'unknown')
                if bet_type in bet_type_stats:
                    bet_type_stats[bet_type]['hits'] += 1
        
        result = {}
        for bet_type, stats in bet_type_stats.items():
            if stats['total'] > 0:
                result[bet_type] = round(stats['hits'] / stats['total'] * 100, 2)
        
        return result
    
    def calculate_max_drawdown(self) -> Tuple[float, str, str]:
        """最大ドローダウンを計算"""
        if not self.race_results:
            return 0.0, '', ''
        
        equity_curve = self._build_equity_curve()
        
        peak = equity_curve[0]
        max_dd = 0
        peak_idx = 0
        max_dd_start_idx = 0
        max_dd_end_idx = 0
        
        for i, equity in enumerate(equity_curve):
            if equity > peak:
                peak = equity
                peak_idx = i
            
            dd = (peak - equity) / peak if peak > 0 else 0
            if dd > max_dd:
                max_dd = dd
                max_dd_start_idx = peak_idx
                max_dd_end_idx = i
        
        start_date = self.race_results[max_dd_start_idx].get('race_date', '') if max_dd_start_idx < len(self.race_results) else ''
        end_date = self.race_results[max_dd_end_idx].get('race_date', '') if max_dd_end_idx < len(self.race_results) else ''
        
        return round(max_dd * 100, 2), start_date, end_date
    
    def _build_equity_curve(self) -> List[float]:
        """資産曲線を構築"""
        initial = self.results.get('summary', {}).get('total_investment', 100000) / len(self.race_results) if self.race_results else 100000
        equity = [initial]
        
        for race in self.race_results:
            new_equity = equity[-1] + race.get('profit', 0)
            equity.append(new_equity)
        
        return equity
    
    def calculate_sharpe_ratio(self, risk_free_rate: float = 0.0) -> float:
        """シャープレシオを計算"""
        returns = self._calculate_race_returns()
        
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0
        
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        # 年率換算（1年=250営業日として計算）
        sharpe = (avg_return - risk_free_rate / 250) / std_return * np.sqrt(250)
        return round(sharpe, 2)
    
    def calculate_sortino_ratio(self, risk_free_rate: float = 0.0) -> float:
        """ソルティノレシオを計算（下方リスクのみ考慮）"""
        returns = self._calculate_race_returns()
        
        if len(returns) == 0:
            return 0.0
        
        avg_return = np.mean(returns)
        downside_returns = returns[returns < 0]
        
        if len(downside_returns) == 0:
            return float('inf')
        
        downside_std = np.std(downside_returns)
        if downside_std == 0:
            return 0.0
        
        sortino = (avg_return - risk_free_rate / 250) / downside_std * np.sqrt(250)
        return round(sortino, 2)
    
    def _calculate_race_returns(self) -> np.ndarray:
        """レースごとのリターンを計算"""
        returns = []
        for race in self.race_results:
            investment = race.get('investment', 0)
            if investment > 0:
                ret = race.get('profit', 0) / investment
                returns.append(ret)
        return np.array(returns)
    
    def calculate_win_rate(self) -> float:
        """勝率（利益が出たレースの割合）"""
        if not self.race_results:
            return 0.0
        
        profitable = sum(1 for r in self.race_results if r.get('profit', 0) > 0)
        return round(profitable / len(self.race_results) * 100, 2)
    
    def calculate_payoff_ratio(self) -> float:
        """ペイオフレシオ"""
        profits = [r['profit'] for r in self.race_results if r.get('profit', 0) > 0]
        losses = [-r['profit'] for r in self.race_results if r.get('profit', 0) < 0]
        
        if not profits or not losses:
            return 0.0
        
        return round(np.mean(profits) / np.mean(losses), 2)
    
    def get_longest_winning_streak(self) -> int:
        """最大連勝数"""
        max_streak = 0
        current_streak = 0
        
        for race in self.race_results:
            if race.get('profit', 0) > 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def get_longest_losing_streak(self) -> int:
        """最大連敗数"""
        max_streak = 0
        current_streak = 0
        
        for race in self.race_results:
            if race.get('profit', 0) < 0:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 0
        
        return max_streak
    
    def calculate_all_metrics(self) -> Dict[str, Any]:
        """全評価指標を一括計算"""
        max_dd, dd_start, dd_end = self.calculate_max_drawdown()
        
        return {
            # 収益性
            'recovery_rate': self.calculate_recovery_rate(),
            'roi': self.calculate_roi(),
            'net_profit': self.summary.get('net_profit', 0),
            'total_investment': self.summary.get('total_investment', 0),
            'total_payout': self.summary.get('total_payout', 0),
            
            # 的中率
            'hit_rate': self.calculate_hit_rate(),
            'hit_rate_by_type': self.calculate_hit_rate_by_bet_type(),
            
            # リスク
            'max_drawdown': max_dd,
            'max_drawdown_period': (dd_start, dd_end),
            'sharpe_ratio': self.calculate_sharpe_ratio(),
            'sortino_ratio': self.calculate_sortino_ratio(),
            
            # 安定性
            'win_rate': self.calculate_win_rate(),
            'payoff_ratio': self.calculate_payoff_ratio(),
            'longest_winning_streak': self.get_longest_winning_streak(),
            'longest_losing_streak': self.get_longest_losing_streak(),
            
            # 総計
            'total_races': self.summary.get('total_races', 0),
            'total_bets': self.summary.get('total_bets', 0),
            'total_hits': self.summary.get('total_hits', 0)
        }
