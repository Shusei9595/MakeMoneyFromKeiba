"""
定期実行スケジューラー
"""
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Dict, List
import logging
import yaml

logger = logging.getLogger(__name__)


class TaskScheduler:
    """タスクスケジューラー"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.tasks: Dict[str, dict] = {}
        self.running = False
    
    def add_daily_task(self, name: str, func: Callable, hour: int = 6, minute: int = 0):
        """日次タスクを追加"""
        self.tasks[name] = {
            'func': func,
            'schedule': 'daily',
            'hour': hour,
            'minute': minute,
            'last_run': None
        }
    
    def add_weekly_task(self, name: str, func: Callable, weekday: int = 0, hour: int = 8):
        """週次タスクを追加（weekday: 0=月曜）"""
        self.tasks[name] = {
            'func': func,
            'schedule': 'weekly',
            'weekday': weekday,
            'hour': hour,
            'last_run': None
        }
    
    def add_monthly_task(self, name: str, func: Callable, day: int = 1, hour: int = 9):
        """月次タスクを追加"""
        self.tasks[name] = {
            'func': func,
            'schedule': 'monthly',
            'day': day,
            'hour': hour,
            'last_run': None
        }
    
    def _should_run(self, task: dict, now: datetime) -> bool:
        """タスクを実行すべきか判定"""
        last_run = task.get('last_run')
        schedule = task['schedule']
        
        if schedule == 'daily':
            target_time = now.replace(hour=task['hour'], minute=task.get('minute', 0), second=0)
            if last_run and last_run.date() == now.date():
                return False
            return now >= target_time
        
        elif schedule == 'weekly':
            if now.weekday() != task['weekday']:
                return False
            target_time = now.replace(hour=task['hour'], minute=0, second=0)
            if last_run and (now - last_run).days < 7:
                return False
            return now >= target_time
        
        elif schedule == 'monthly':
            if now.day != task['day']:
                return False
            target_time = now.replace(hour=task['hour'], minute=0, second=0)
            if last_run and last_run.month == now.month and last_run.year == now.year:
                return False
            return now >= target_time
        
        return False
    
    def run_once(self):
        """一度だけ実行チェック"""
        now = datetime.now()
        
        for name, task in self.tasks.items():
            if self._should_run(task, now):
                logger.info(f"タスク実行開始: {name}")
                try:
                    task['func']()
                    task['last_run'] = now
                    logger.info(f"タスク実行完了: {name}")
                except Exception as e:
                    logger.error(f"タスク実行エラー ({name}): {e}")
    
    def run(self, check_interval: int = 60):
        """スケジューラーを起動（無限ループ）"""
        logger.info("スケジューラー起動")
        self.running = True
        
        while self.running:
            self.run_once()
            time.sleep(check_interval)
    
    def stop(self):
        """スケジューラーを停止"""
        self.running = False
        logger.info("スケジューラー停止")


def create_default_scheduler(config: dict = None) -> TaskScheduler:
    """デフォルトのスケジューラーを作成"""
    scheduler = TaskScheduler(config)
    
    # 日次タスク例
    def daily_data_check():
        logger.info("日次データチェック実行")
        # TODO: 実際のデータチェック処理
    
    # 週次タスク例
    def weekly_backtest():
        logger.info("週次バックテスト実行")
        # TODO: 実際のバックテスト処理
    
    # 月次タスク例
    def monthly_report():
        logger.info("月次レポート生成")
        # TODO: 実際のレポート生成処理
    
    scheduler.add_daily_task("daily_data_check", daily_data_check, hour=6)
    scheduler.add_weekly_task("weekly_backtest", weekly_backtest, weekday=0, hour=8)
    scheduler.add_monthly_task("monthly_report", monthly_report, day=1, hour=9)
    
    return scheduler


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    scheduler = create_default_scheduler()
    
    try:
        scheduler.run()
    except KeyboardInterrupt:
        scheduler.stop()
