"""
データ検証モジュール
収集したデータの品質チェックを行う
"""

import pandas as pd
from typing import Dict, List
import logging


class DataValidator:
    """取得したデータの検証を行う"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.validation_results = []
    
    def validate_race_data(self, df: pd.DataFrame) -> Dict:
        """
        レースデータの検証
        
        チェック項目:
        - 必須カラムの存在確認
        - データ型の検証
        - 欠損値の確認とレポート
        - 値の範囲チェック（例: 着順は1-18、オッズは1.0以上）
        - 整合性チェック（例: 着順と馬番の対応）
        - 重複データの検出
        
        Returns:
            検証結果の辞書
        """
        self.logger.info("Validating race data...")
        
        result = {
            'is_valid': True,
            'total_records': len(df),
            'missing_values': {},
            'invalid_values': {},
            'warnings': [],
            'errors': []
        }
        
        if df.empty:
            result['is_valid'] = False
            result['errors'].append("DataFrame is empty")
            return result
        
        # 必須カラムのチェック
        required_columns = [
            'race_id', 'race_date', 'track_name', 'horse_number',
            'horse_name', 'finish_position'
        ]
        
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            result['is_valid'] = False
            result['errors'].append(f"Missing required columns: {missing_cols}")
            return result
        
        # 欠損値のチェック
        for col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                result['missing_values'][col] = int(null_count)
                missing_pct = (null_count / len(df)) * 100
                
                if col in required_columns and missing_pct > 5:
                    result['is_valid'] = False
                    result['errors'].append(
                        f"Column '{col}' has {missing_pct:.1f}% missing values (threshold: 5%)"
                    )
                elif missing_pct > 20:
                    result['warnings'].append(
                        f"Column '{col}' has {missing_pct:.1f}% missing values"
                    )
        
        # 数値カラムの範囲チェック
        numeric_checks = [
            ('finish_position', 1, 18, 'Finish position'),
            ('horse_number', 1, 18, 'Horse number'),
            ('frame_number', 1, 8, 'Frame number'),
            ('odds', 1.0, 1000.0, 'Odds'),
            ('weight', 45.0, 60.0, 'Weight'),
            ('horse_weight', 300, 600, 'Horse weight'),
        ]
        
        for col, min_val, max_val, label in numeric_checks:
            if col in df.columns:
                invalid_mask = (df[col] < min_val) | (df[col] > max_val)
                invalid_count = invalid_mask.sum()
                
                if invalid_count > 0:
                    result['invalid_values'][col] = int(invalid_count)
                    invalid_pct = (invalid_count / len(df)) * 100
                    
                    if invalid_pct > 10:
                        result['is_valid'] = False
                        result['errors'].append(
                            f"{label} out of range [{min_val}-{max_val}]: {invalid_pct:.1f}%"
                        )
                    else:
                        result['warnings'].append(
                            f"{label} out of range [{min_val}-{max_val}]: {invalid_count} records"
                        )
        
        # 重複チェック
        if 'race_id' in df.columns and 'horse_number' in df.columns:
            duplicate_mask = df.duplicated(subset=['race_id', 'horse_number'])
            duplicate_count = duplicate_mask.sum()
            
            if duplicate_count > 0:
                result['warnings'].append(f"Found {duplicate_count} duplicate records")
        
        # 日付フォーマットのチェック
        if 'race_date' in df.columns:
            try:
                pd.to_datetime(df['race_date'])
            except:
                result['is_valid'] = False
                result['errors'].append("Invalid date format in 'race_date' column")
        
        # 整合性チェック：レースごとの馬番の重複
        if 'race_id' in df.columns and 'horse_number' in df.columns:
            for race_id in df['race_id'].unique():
                race_df = df[df['race_id'] == race_id]
                horse_numbers = race_df['horse_number'].dropna()
                
                if len(horse_numbers) != len(horse_numbers.unique()):
                    result['warnings'].append(
                        f"Race {race_id} has duplicate horse numbers"
                    )
        
        self.logger.info(f"Validation complete: {'PASSED' if result['is_valid'] else 'FAILED'}")
        return result
    
    def validate_horse_data(self, df: pd.DataFrame) -> Dict:
        """馬データの検証"""
        self.logger.info("Validating horse data...")
        
        result = {
            'is_valid': True,
            'total_records': len(df),
            'missing_values': {},
            'invalid_values': {},
            'warnings': [],
            'errors': []
        }
        
        if df.empty:
            result['is_valid'] = False
            result['errors'].append("DataFrame is empty")
            return result
        
        # 必須カラムのチェック
        required_columns = ['horse_id', 'horse_name']
        
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            result['is_valid'] = False
            result['errors'].append(f"Missing required columns: {missing_cols}")
            return result
        
        # 欠損値のチェック
        for col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                result['missing_values'][col] = int(null_count)
                missing_pct = (null_count / len(df)) * 100
                
                if col in required_columns and missing_pct > 0:
                    result['is_valid'] = False
                    result['errors'].append(
                        f"Required column '{col}' has missing values"
                    )
        
        # 重複チェック
        if 'horse_id' in df.columns:
            duplicate_count = df['horse_id'].duplicated().sum()
            if duplicate_count > 0:
                result['warnings'].append(f"Found {duplicate_count} duplicate horse IDs")
        
        self.logger.info(f"Horse data validation: {'PASSED' if result['is_valid'] else 'FAILED'}")
        return result
    
    def validate_jockey_data(self, df: pd.DataFrame) -> Dict:
        """騎手データの検証"""
        self.logger.info("Validating jockey data...")
        
        result = {
            'is_valid': True,
            'total_records': len(df),
            'missing_values': {},
            'invalid_values': {},
            'warnings': [],
            'errors': []
        }
        
        if df.empty:
            result['is_valid'] = False
            result['errors'].append("DataFrame is empty")
            return result
        
        # 必須カラムのチェック
        required_columns = ['jockey_id', 'jockey_name']
        
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            result['is_valid'] = False
            result['errors'].append(f"Missing required columns: {missing_cols}")
            return result
        
        # 欠損値のチェック
        for col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                result['missing_values'][col] = int(null_count)
                missing_pct = (null_count / len(df)) * 100
                
                if col in required_columns and missing_pct > 0:
                    result['is_valid'] = False
                    result['errors'].append(
                        f"Required column '{col}' has missing values"
                    )
        
        # 勝率の範囲チェック
        rate_columns = ['win_rate', 'place_rate', 'show_rate']
        for col in rate_columns:
            if col in df.columns:
                invalid_mask = (df[col] < 0) | (df[col] > 100)
                invalid_count = invalid_mask.sum()
                
                if invalid_count > 0:
                    result['warnings'].append(
                        f"Column '{col}' has {invalid_count} values out of range [0-100]"
                    )
        
        self.logger.info(f"Jockey data validation: {'PASSED' if result['is_valid'] else 'FAILED'}")
        return result
    
    def generate_report(self, validation_results: List[Dict]) -> str:
        """
        検証結果のレポートを生成
        
        Returns:
            Markdown形式のレポート
        """
        report_lines = ["# Data Validation Report\n"]
        report_lines.append(f"Generated at: {pd.Timestamp.now()}\n")
        report_lines.append("---\n\n")
        
        for i, result in enumerate(validation_results, 1):
            report_lines.append(f"## Validation {i}\n")
            
            # 基本情報
            report_lines.append(f"- **Status**: {'✅ PASSED' if result['is_valid'] else '❌ FAILED'}\n")
            report_lines.append(f"- **Total Records**: {result['total_records']}\n\n")
            
            # エラー
            if result['errors']:
                report_lines.append("### Errors\n")
                for error in result['errors']:
                    report_lines.append(f"- ❌ {error}\n")
                report_lines.append("\n")
            
            # 警告
            if result['warnings']:
                report_lines.append("### Warnings\n")
                for warning in result['warnings']:
                    report_lines.append(f"- ⚠️ {warning}\n")
                report_lines.append("\n")
            
            # 欠損値
            if result['missing_values']:
                report_lines.append("### Missing Values\n")
                for col, count in result['missing_values'].items():
                    pct = (count / result['total_records']) * 100
                    report_lines.append(f"- **{col}**: {count} ({pct:.2f}%)\n")
                report_lines.append("\n")
            
            # 無効値
            if result['invalid_values']:
                report_lines.append("### Invalid Values\n")
                for col, count in result['invalid_values'].items():
                    report_lines.append(f"- **{col}**: {count} records\n")
                report_lines.append("\n")
            
            report_lines.append("---\n\n")
        
        return "".join(report_lines)
