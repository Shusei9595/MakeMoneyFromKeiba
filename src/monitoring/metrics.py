"""
パフォーマンスメトリクス収集
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional
import json
from pathlib import Path


@dataclass
class PredictionMetrics:
    """予測メトリクス"""
    timestamp: datetime
    race_id: str
    strategy: str
    execution_time: float  # 秒
    num_recommendations: int
    avg_ev: float
    memory_usage: float  # MB


@dataclass
class BacktestMetrics:
    """バックテストメトリクス"""
    timestamp: datetime
    start_date: str
    end_date: str
    strategy: str
    initial_budget: int
    final_budget: int
    roi: float
    hit_rate: float
    num_races: int


class MetricsCollector:
    """メトリクスコレクター"""
    
    def __init__(self, output_dir: str = "logs/metrics"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def record_prediction(self, metrics: PredictionMetrics):
        """予測メトリクスを記録"""
        log_file = self.output_dir / f"predictions_{datetime.now().strftime('%Y%m')}.jsonl"
        
        data = asdict(metrics)
        data['timestamp'] = metrics.timestamp.isoformat()
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    def record_backtest(self, metrics: BacktestMetrics):
        """バックテストメトリクスを記録"""
        log_file = self.output_dir / f"backtests_{datetime.now().strftime('%Y%m')}.jsonl"
        
        data = asdict(metrics)
        data['timestamp'] = metrics.timestamp.isoformat()
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
    
    def get_daily_summary(self, date: datetime) -> Dict:
        """日次サマリーを取得"""
        log_file = self.output_dir / f"predictions_{date.strftime('%Y%m')}.jsonl"
        
        if not log_file.exists():
            return {}
        
        metrics = []
        date_prefix = date.strftime('%Y-%m-%d')
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                data = json.loads(line)
                if data['timestamp'].startswith(date_prefix):
                    metrics.append(data)
        
        if not metrics:
            return {}
        
        return {
            'date': date_prefix,
            'total_predictions': len(metrics),
            'avg_execution_time': sum(m['execution_time'] for m in metrics) / len(metrics),
            'total_recommendations': sum(m['num_recommendations'] for m in metrics),
            'avg_ev': sum(m['avg_ev'] for m in metrics) / len(metrics),
            'avg_memory_usage': sum(m['memory_usage'] for m in metrics) / len(metrics)
        }
    
    def get_monthly_summary(self, year: int, month: int) -> Dict:
        """月次サマリーを取得"""
        log_file = self.output_dir / f"predictions_{year}{month:02d}.jsonl"
        
        if not log_file.exists():
            return {}
        
        metrics = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                metrics.append(json.loads(line))
        
        if not metrics:
            return {}
        
        return {
            'year': year,
            'month': month,
            'total_predictions': len(metrics),
            'total_recommendations': sum(m['num_recommendations'] for m in metrics),
            'avg_ev': sum(m['avg_ev'] for m in metrics) / len(metrics)
        }
