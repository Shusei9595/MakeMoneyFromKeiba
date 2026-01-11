"""
入力検証ユーティリティ
"""
import click
import re
from datetime import datetime


def validate_date(ctx, param, value):
    """日付形式を検証"""
    if value is None:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d')
    except ValueError:
        raise click.BadParameter('日付は YYYY-MM-DD 形式で指定してください')


def validate_race_id(race_id: str):
    """レースIDを検証"""
    if not re.match(r'^\d{12}$', race_id):
        raise click.BadParameter('レースIDは12桁の数字で指定してください（例: 202401050811）')
    return race_id


def validate_strategy(strategy: str):
    """戦略を検証"""
    valid = ['conservative', 'balanced', 'aggressive']
    if strategy not in valid:
        raise click.BadParameter(f"戦略は {', '.join(valid)} のいずれかを指定してください")
    return strategy


def validate_positive_int(ctx, param, value):
    """正の整数を検証"""
    if value is not None and value <= 0:
        raise click.BadParameter('正の整数を指定してください')
    return value
