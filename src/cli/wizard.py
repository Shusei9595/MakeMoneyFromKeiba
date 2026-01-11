"""
対話的設定ウィザード
"""
import click
from pathlib import Path
import yaml
from rich.console import Console
from rich.panel import Panel

console = Console()


def run_wizard():
    """対話的設定ウィザードを実行"""
    console.print(Panel.fit("🧙 競馬AI設定ウィザード", style="bold cyan"))
    console.print()
    
    config = {}
    
    # 基本設定
    console.print("[bold]📁 データディレクトリ設定[/bold]")
    raw_dir = click.prompt('生データ保存先', default='data/raw')
    processed_dir = click.prompt('処理済みデータ保存先', default='data/processed')
    
    config['data'] = {
        'raw_dir': raw_dir,
        'processed_dir': processed_dir
    }
    
    # モデル設定
    console.print()
    console.print("[bold]🧠 モデル設定[/bold]")
    models_dir = click.prompt('モデル保存先', default='models')
    
    config['models'] = {
        'dir': models_dir
    }
    
    # スクレイピング設定
    console.print()
    console.print("[bold]🌐 スクレイピング設定[/bold]")
    crawl_delay = click.prompt('クロール間隔（秒）', default=1.0, type=float)
    max_retries = click.prompt('最大リトライ回数', default=3, type=int)
    
    config['scraping'] = {
        'crawl_delay': crawl_delay,
        'max_retries': max_retries,
        'timeout': 30
    }
    
    # 予測設定
    console.print()
    console.print("[bold]🎯 予測設定[/bold]")
    default_strategy = click.prompt(
        'デフォルト戦略',
        type=click.Choice(['conservative', 'balanced', 'aggressive']),
        default='balanced'
    )
    default_budget = click.prompt('デフォルト予算（円）', default=10000, type=int)
    
    config['prediction'] = {
        'default_strategy': default_strategy,
        'default_budget': default_budget
    }
    
    # 監視設定（オプション）
    console.print()
    if click.confirm('監視・アラート設定を行いますか？', default=False):
        console.print("[bold]📊 監視設定[/bold]")
        enable_alerts = click.confirm('アラート通知を有効にしますか？', default=False)
        
        config['monitoring'] = {
            'enabled': True,
            'metrics_dir': 'logs/metrics',
            'alerts': {
                'enabled': enable_alerts
            }
        }
        
        if enable_alerts:
            alert_method = click.prompt(
                'アラート方法',
                type=click.Choice(['email', 'slack', 'none']),
                default='none'
            )
            if alert_method == 'email':
                smtp_server = click.prompt('SMTPサーバー')
                sender_email = click.prompt('送信者メールアドレス')
                recipient_email = click.prompt('受信者メールアドレス')
                config['monitoring']['alerts']['email'] = {
                    'smtp_server': smtp_server,
                    'sender': sender_email,
                    'recipients': [recipient_email]
                }
            elif alert_method == 'slack':
                webhook_url = click.prompt('Slack Webhook URL')
                config['monitoring']['alerts']['slack'] = {
                    'webhook_url': webhook_url
                }
    
    # 保存
    console.print()
    config_path = Path('config/config.yaml')
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    console.print(Panel.fit(
        f"✅ 設定を保存しました: {config_path}",
        style="bold green"
    ))
    
    return config


if __name__ == '__main__':
    run_wizard()
