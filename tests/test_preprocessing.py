"""
前処理モジュールのテスト
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.preprocessing.preprocessor import RaceDataPreprocessor
from src.preprocessing.feature_engineer import FeatureEngineer
from src.preprocessing.pipeline import DataPreprocessingPipeline


@pytest.fixture
def sample_race_data():
    """テスト用のサンプルデータ"""
    dates = pd.date_range('2024-01-01', periods=10, freq='7D')
    
    data = {
        'race_id': [f'2024010{i}0101' for i in range(1, 11)],
        'race_date': dates,
        'track_name': ['東京'] * 5 + ['中山'] * 5,
        'distance': [1600] * 5 + [1800] * 5,
        'track_type': ['芝'] * 10,
        'track_condition': ['良'] * 10,
        'horse_id': ['H001'] * 10,
        'horse_name': ['テストホース'] * 10,
        'finish_position': [1, 2, 3, 1, 2, 3, 1, 2, 3, 1],
        'finish_time': [95.5, 96.0, 96.5, 95.0, 95.8, 96.2, 94.8, 95.5, 96.0, 94.5],
        'odds': [5.2, 6.1, 7.3, 4.8, 5.9, 7.1, 4.5, 5.5, 6.8, 4.2],
        'horse_weight': [480, 482, 481, 483, 485, 484, 486, 487, 485, 488],
        'horse_weight_diff': [0, 2, -1, 2, 2, -1, 2, 1, -2, 3],
        'jockey_id': ['J001'] * 5 + ['J002'] * 5,
        'trainer_id': ['T001'] * 10,
        'weight': [55] * 10,
        'popularity': [1, 2, 3, 1, 2, 3, 1, 2, 3, 1],
        'grade': ['一般'] * 10
    }
    
    return pd.DataFrame(data)


@pytest.fixture
def preprocessor_config():
    """前処理設定"""
    return {
        'missing_value_strategy': 'median',
        'outlier_threshold': 3.0,
        'normalization': 'standard'
    }


class TestRaceDataPreprocessor:
    """RaceDataPreprocessorのテスト"""
    
    def test_clean_data(self, sample_race_data, preprocessor_config):
        """データクリーニングのテスト"""
        preprocessor = RaceDataPreprocessor(preprocessor_config)
        df_clean = preprocessor.clean_data(sample_race_data)
        
        assert len(df_clean) == len(sample_race_data)
        assert 'race_date' in df_clean.columns
        assert pd.api.types.is_datetime64_any_dtype(df_clean['race_date'])
    
    def test_handle_missing_values(self, preprocessor_config):
        """欠損値処理のテスト"""
        df = pd.DataFrame({
            'col1': [1, 2, np.nan, 4, 5],
            'col2': [10, np.nan, 30, 40, 50]
        })
        
        preprocessor = RaceDataPreprocessor(preprocessor_config)
        df_filled = preprocessor.handle_missing_values(df)
        
        assert df_filled['col1'].isna().sum() == 0
        assert df_filled['col2'].isna().sum() == 0
    
    def test_encode_categorical(self, sample_race_data, preprocessor_config):
        """カテゴリ変数エンコーディングのテスト"""
        preprocessor = RaceDataPreprocessor(preprocessor_config)
        df_encoded = preprocessor.encode_categorical(sample_race_data)
        
        assert 'track_name_encoded' in df_encoded.columns
        assert 'track_type_encoded' in df_encoded.columns
        assert 'track_condition_encoded' in df_encoded.columns
        assert 'grade_encoded' in df_encoded.columns
    
    def test_extract_datetime_features(self, sample_race_data, preprocessor_config):
        """日付特徴量抽出のテスト"""
        preprocessor = RaceDataPreprocessor(preprocessor_config)
        df_datetime = preprocessor.extract_datetime_features(sample_race_data)
        
        assert 'year' in df_datetime.columns
        assert 'month' in df_datetime.columns
        assert 'day' in df_datetime.columns
        assert 'day_of_week' in df_datetime.columns
        assert 'is_weekend' in df_datetime.columns
        assert 'season' in df_datetime.columns


class TestFeatureEngineer:
    """FeatureEngineerのテスト"""
    
    def test_create_past_performance_features(self, sample_race_data):
        """前走特徴量生成のテスト"""
        engineer = FeatureEngineer()
        df_features = engineer.create_past_performance_features(sample_race_data)
        
        assert 'recent_3_avg_speed' in df_features.columns
        assert 'days_since_last_race' in df_features.columns
        assert 'last_race_position' in df_features.columns
        assert 'recent_3_win_count' in df_features.columns
        assert 'consistency_score' in df_features.columns
    
    def test_create_distance_course_features(self, sample_race_data):
        """距離・コース特徴量生成のテスト"""
        # is_win カラムを追加
        sample_race_data['is_win'] = (sample_race_data['finish_position'] == 1).astype(int)
        
        engineer = FeatureEngineer()
        df_features = engineer.create_distance_course_features(sample_race_data)
        
        assert 'distance_experience_count' in df_features.columns
        assert 'distance_win_rate' in df_features.columns
        assert 'track_win_rate' in df_features.columns
        assert 'distance_category' in df_features.columns
    
    def test_create_jockey_trainer_features(self, sample_race_data):
        """騎手・調教師特徴量生成のテスト"""
        sample_race_data['is_win'] = (sample_race_data['finish_position'] == 1).astype(int)
        
        engineer = FeatureEngineer()
        df_features = engineer.create_jockey_trainer_features(sample_race_data)
        
        assert 'jockey_win_rate_overall' in df_features.columns
        assert 'trainer_win_rate_overall' in df_features.columns
        assert 'jockey_horse_combination_count' in df_features.columns
    
    def test_create_relative_features(self, sample_race_data):
        """相対特徴量生成のテスト"""
        engineer = FeatureEngineer()
        df_features = engineer.create_relative_features(sample_race_data)
        
        assert 'relative_weight' in df_features.columns
        assert 'relative_odds' in df_features.columns
        assert 'odds_rank' in df_features.columns
    
    def test_create_statistical_features(self, sample_race_data):
        """統計特徴量生成のテスト"""
        sample_race_data['is_win'] = (sample_race_data['finish_position'] == 1).astype(int)
        
        engineer = FeatureEngineer()
        df_features = engineer.create_statistical_features(sample_race_data)
        
        assert 'career_total_races' in df_features.columns
        assert 'career_win_rate' in df_features.columns
        assert 'career_place_rate' in df_features.columns
        assert 'career_show_rate' in df_features.columns


class TestDataPreprocessingPipeline:
    """DataPreprocessingPipelineのテスト"""
    
    def test_fit_transform(self, sample_race_data, preprocessor_config):
        """パイプライン全体のテスト"""
        pipeline = DataPreprocessingPipeline(preprocessor_config)
        df_processed = pipeline.fit_transform(sample_race_data)
        
        # 元データより多くのカラムがあるはず（特徴量が追加される）
        assert len(df_processed.columns) > len(sample_race_data.columns)
        
        # レコード数は変わらない
        assert len(df_processed) == len(sample_race_data)
        
        # 主要な特徴量が存在する
        expected_features = [
            'recent_3_avg_speed',
            'distance_experience_count',
            'career_total_races'
        ]
        for feature in expected_features:
            assert feature in df_processed.columns, f"Missing feature: {feature}"
    
    def test_pipeline_save_load(self, sample_race_data, preprocessor_config, tmp_path):
        """パイプライン保存・読み込みのテスト"""
        pipeline = DataPreprocessingPipeline(preprocessor_config)
        df_processed = pipeline.fit_transform(sample_race_data)
        
        # 保存
        pipeline.save(tmp_path)
        
        # 読み込み
        loaded_pipeline = DataPreprocessingPipeline.load(tmp_path)
        
        assert loaded_pipeline.config == preprocessor_config
    
    def test_get_feature_importance_ranking(self, sample_race_data, preprocessor_config):
        """特徴量統計取得のテスト"""
        pipeline = DataPreprocessingPipeline(preprocessor_config)
        df_processed = pipeline.fit_transform(sample_race_data)
        
        stats = pipeline.feature_engineer.get_feature_importance_ranking(df_processed)
        
        assert 'feature' in stats.columns
        assert 'mean' in stats.columns
        assert 'std' in stats.columns
        assert 'missing_ratio' in stats.columns
        assert len(stats) > 0
