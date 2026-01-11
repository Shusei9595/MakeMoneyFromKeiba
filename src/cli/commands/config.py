"""
設定管理コマンド
"""
import click
from pathlib import Path
import yaml


@click.group()
def config():
    """
    設定を管理
    
    \b
    使用例:
        keiba-ai config show
        keiba-ai config set data.raw_dir /custom/path
        keiba-ai config wizard
    """
    pass


@config.command()
def show():
    """現在の設定を表示"""
    config_path = Path('config/config.yaml')
    
    if not config_path.exists():
        click.echo("⚠️ 設定ファイルが見つかりません")
        click.echo(f"   パス: {config_path}")
        return
    
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    
    click.echo("📋 現在の設定:")
    click.echo(yaml.dump(cfg, default_flow_style=False, allow_unicode=True))


@config.command()
@click.argument('key')
@click.argument('value')
def set(key, value):
    """設定値を変更"""
    config_path = Path('config/config.yaml')
    
    if not config_path.exists():
        cfg = {}
    else:
        with open(config_path) as f:
            cfg = yaml.safe_load(f) or {}
    
    # ドット区切りのキーを処理
    keys = key.split('.')
    current = cfg
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    
    current[keys[-1]] = value
    
    with open(config_path, 'w') as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
    
    click.echo(f"✅ 設定を変更しました: {key} = {value}")


@config.command()
def wizard():
    """対話的設定ウィザード"""
    click.echo("🧙 設定ウィザードを開始します")
    click.echo()
    
    config_path = Path('config/config.yaml')
    cfg = {}
    
    # データディレクトリ
    raw_dir = click.prompt('生データ保存先', default='data/raw')
    processed_dir = click.prompt('処理済みデータ保存先', default='data/processed')
    
    cfg['data'] = {
        'raw_dir': raw_dir,
        'processed_dir': processed_dir
    }
    
    # モデル設定
    models_dir = click.prompt('モデル保存先', default='models')
    cfg['models'] = {
        'dir': models_dir
    }
    
    # スクレイピング設定
    crawl_delay = click.prompt('クロール間隔（秒）', default=1.0, type=float)
    cfg['scraping'] = {
        'crawl_delay': crawl_delay
    }
    
    # 保存
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, 'w') as f:
        yaml.dump(cfg, f, default_flow_style=False, allow_unicode=True)
    
    click.echo()
    click.echo(f"✅ 設定を保存しました: {config_path}")
