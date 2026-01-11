"""
アラート送信
"""
from enum import Enum
from datetime import datetime
from typing import Optional, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """アラートレベル"""
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class AlertManager:
    """アラート管理"""
    
    def __init__(self, config: dict = None):
        config = config or {}
        self.smtp_server = config.get('smtp_server')
        self.smtp_port = config.get('smtp_port', 587)
        self.sender_email = config.get('sender_email')
        self.sender_password = config.get('sender_password')
        self.recipient_emails = config.get('recipient_emails', [])
        self.enabled = bool(self.smtp_server and self.sender_email)
    
    def send_alert(self, level: AlertLevel, title: str, message: str):
        """アラート送信"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # コンソール出力
        log_message = f"[{level.value}] {title}: {message}"
        if level == AlertLevel.CRITICAL:
            logger.critical(log_message)
        elif level == AlertLevel.ERROR:
            logger.error(log_message)
        elif level == AlertLevel.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # メール送信（設定がある場合）
        if self.enabled and self.recipient_emails:
            self._send_email(level, title, message, timestamp)
    
    def _send_email(self, level: AlertLevel, title: str, message: str, timestamp: str):
        """メール送信"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = ', '.join(self.recipient_emails)
            msg['Subject'] = f"[競馬AI] {level.value}: {title}"
            
            body = f"""
競馬AI予測システム - アラート通知

レベル: {level.value}
タイトル: {title}
発生時刻: {timestamp}

詳細:
{message}

---
このメールは自動送信されています。
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            logger.info(f"アラートメール送信完了: {title}")
            
        except Exception as e:
            logger.error(f"アラートメール送信失敗: {e}")
    
    def check_performance_degradation(self, current_roi: float, threshold: float = 0.95):
        """パフォーマンス低下を検知"""
        if current_roi < threshold:
            self.send_alert(
                AlertLevel.WARNING,
                "パフォーマンス低下",
                f"回収率が {current_roi:.1%} に低下しました（閾値: {threshold:.1%}）"
            )
            return True
        return False
    
    def check_model_staleness(self, last_train_date: datetime, max_days: int = 30):
        """モデルの陳腐化を検知"""
        days_since_train = (datetime.now() - last_train_date).days
        
        if days_since_train > max_days:
            self.send_alert(
                AlertLevel.WARNING,
                "モデル再訓練推奨",
                f"最終訓練から {days_since_train} 日経過しています（推奨: {max_days}日以内）"
            )
            return True
        return False
    
    def check_data_quality(self, missing_rate: float, threshold: float = 0.1):
        """データ品質をチェック"""
        if missing_rate > threshold:
            self.send_alert(
                AlertLevel.WARNING,
                "データ品質低下",
                f"欠損率が {missing_rate:.1%} です（閾値: {threshold:.1%}）"
            )
            return True
        return False
