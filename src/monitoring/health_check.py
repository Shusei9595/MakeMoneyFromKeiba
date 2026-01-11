"""
システムヘルスチェック
"""
import os
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional
import shutil
import logging

logger = logging.getLogger(__name__)


@dataclass
class HealthStatus:
    """ヘルスステータス"""
    component: str
    status: str  # OK, WARNING, ERROR
    message: str
    timestamp: datetime


class HealthChecker:
    """システムヘルスチェッカー"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.models_dir = Path(self.config.get('models', {}).get('dir', 'models'))
        self.data_dir = Path(self.config.get('data', {}).get('processed_dir', 'data/processed'))
        self.raw_data_dir = Path(self.config.get('data', {}).get('raw_dir', 'data/raw'))
    
    def check_all(self) -> List[HealthStatus]:
        """全コンポーネントをチェック"""
        results = []
        results.append(self.check_models())
        results.append(self.check_data())
        results.append(self.check_disk_space())
        results.append(self.check_model_freshness())
        results.append(self.check_config())
        return results
    
    def check_models(self) -> HealthStatus:
        """モデルファイルの存在確認"""
        if not self.models_dir.exists():
            return HealthStatus(
                component="models",
                status="ERROR",
                message=f"モデルディレクトリが存在しません: {self.models_dir}",
                timestamp=datetime.now()
            )
        
        model_files = list(self.models_dir.glob("*.pkl"))
        if len(model_files) == 0:
            return HealthStatus(
                component="models",
                status="WARNING",
                message="訓練済みモデルが見つかりません",
                timestamp=datetime.now()
            )
        
        expected_count = 9  # 9エージェント
        if len(model_files) < expected_count:
            return HealthStatus(
                component="models",
                status="WARNING",
                message=f"モデル数が不足しています: {len(model_files)}/{expected_count}",
                timestamp=datetime.now()
            )
        
        return HealthStatus(
            component="models",
            status="OK",
            message=f"モデル数: {len(model_files)}",
            timestamp=datetime.now()
        )
    
    def check_data(self) -> HealthStatus:
        """データファイルの存在確認"""
        if not self.data_dir.exists():
            return HealthStatus(
                component="data",
                status="WARNING",
                message=f"処理済みデータディレクトリが存在しません: {self.data_dir}",
                timestamp=datetime.now()
            )
        
        csv_files = list(self.data_dir.glob("*.csv"))
        if len(csv_files) == 0:
            return HealthStatus(
                component="data",
                status="WARNING",
                message="処理済みデータファイルが見つかりません",
                timestamp=datetime.now()
            )
        
        # 最新データの確認
        latest_file = max(csv_files, key=lambda p: p.stat().st_mtime)
        latest_mtime = datetime.fromtimestamp(latest_file.stat().st_mtime)
        days_old = (datetime.now() - latest_mtime).days
        
        if days_old > 30:
            return HealthStatus(
                component="data",
                status="WARNING",
                message=f"最新データが{days_old}日前です。更新を推奨します",
                timestamp=datetime.now()
            )
        
        return HealthStatus(
            component="data",
            status="OK",
            message=f"データファイル数: {len(csv_files)}",
            timestamp=datetime.now()
        )
    
    def check_disk_space(self, min_gb: float = 1.0) -> HealthStatus:
        """ディスク容量チェック"""
        total, used, free = shutil.disk_usage("/")
        free_gb = free / (1024 ** 3)
        
        if free_gb < min_gb:
            return HealthStatus(
                component="disk",
                status="ERROR",
                message=f"ディスク空き容量が不足しています: {free_gb:.1f}GB",
                timestamp=datetime.now()
            )
        
        if free_gb < min_gb * 5:
            return HealthStatus(
                component="disk",
                status="WARNING",
                message=f"ディスク空き容量: {free_gb:.1f}GB",
                timestamp=datetime.now()
            )
        
        return HealthStatus(
            component="disk",
            status="OK",
            message=f"ディスク空き容量: {free_gb:.1f}GB",
            timestamp=datetime.now()
        )
    
    def check_model_freshness(self, max_days: int = 30) -> HealthStatus:
        """モデルの鮮度チェック"""
        if not self.models_dir.exists():
            return HealthStatus(
                component="model_freshness",
                status="ERROR",
                message="モデルディレクトリが存在しません",
                timestamp=datetime.now()
            )
        
        model_files = list(self.models_dir.glob("*.pkl"))
        if not model_files:
            return HealthStatus(
                component="model_freshness",
                status="ERROR",
                message="モデルファイルが存在しません",
                timestamp=datetime.now()
            )
        
        oldest_file = min(model_files, key=lambda p: p.stat().st_mtime)
        oldest_mtime = datetime.fromtimestamp(oldest_file.stat().st_mtime)
        days_old = (datetime.now() - oldest_mtime).days
        
        if days_old > max_days:
            return HealthStatus(
                component="model_freshness",
                status="WARNING",
                message=f"最も古いモデルが{days_old}日前です。再訓練を推奨します",
                timestamp=datetime.now()
            )
        
        return HealthStatus(
            component="model_freshness",
            status="OK",
            message=f"モデル最終更新: {days_old}日前",
            timestamp=datetime.now()
        )
    
    def check_config(self) -> HealthStatus:
        """設定ファイルチェック"""
        config_path = Path('config/config.yaml')
        
        if not config_path.exists():
            return HealthStatus(
                component="config",
                status="WARNING",
                message="設定ファイルが存在しません。デフォルト設定を使用します",
                timestamp=datetime.now()
            )
        
        return HealthStatus(
            component="config",
            status="OK",
            message=f"設定ファイル: {config_path}",
            timestamp=datetime.now()
        )
    
    def get_summary(self) -> Dict:
        """サマリーを取得"""
        results = self.check_all()
        
        status_counts = {"OK": 0, "WARNING": 0, "ERROR": 0}
        for r in results:
            status_counts[r.status] += 1
        
        overall = "OK"
        if status_counts["ERROR"] > 0:
            overall = "ERROR"
        elif status_counts["WARNING"] > 0:
            overall = "WARNING"
        
        return {
            "overall": overall,
            "counts": status_counts,
            "details": [
                {
                    "component": r.component,
                    "status": r.status,
                    "message": r.message
                }
                for r in results
            ]
        }


def print_health_report():
    """ヘルスレポートを表示"""
    checker = HealthChecker()
    summary = checker.get_summary()
    
    print("=" * 50)
    print("システムヘルスチェック結果")
    print("=" * 50)
    print(f"全体ステータス: {summary['overall']}")
    print(f"OK: {summary['counts']['OK']}, WARNING: {summary['counts']['WARNING']}, ERROR: {summary['counts']['ERROR']}")
    print("-" * 50)
    
    for detail in summary['details']:
        icon = "✅" if detail['status'] == "OK" else ("⚠️" if detail['status'] == "WARNING" else "❌")
        print(f"{icon} [{detail['component']}] {detail['message']}")
    
    print("=" * 50)


if __name__ == '__main__':
    print_health_report()
