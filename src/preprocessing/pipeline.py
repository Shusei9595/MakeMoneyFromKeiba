"""
データ前処理パイプラインモジュール

前処理とFeature Engineeringを統合管理するパイプラインクラス
"""
from pathlib import Path
import pickle
import pandas as pd
import logging

from .preprocessor import RaceDataPreprocessor
from .feature_engineer import FeatureEngineer


class DataPreprocessingPipeline:
    """前処理パイプライン全体を管理"""
    
    def __init__(self, config: dict):
        self.config = config
        self.preprocessor = RaceDataPreprocessor(config)
        self.feature_engineer = FeatureEngineer()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def fit_transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        訓練データで前処理パイプラインを構築し、変換
        
        Args:
            df: 生データDataFrame
        
        Returns:
            前処理済みDataFrame
        """
        self.logger.info("パイプライン処理開始...")
        
        # Step 1: データクリーニング
        self.logger.info("Step 1: データクリーニング")
        df = self.preprocessor.clean_data(df)
        
        # Step 2: 欠損値処理
        self.logger.info("Step 2: 欠損値処理")
        df = self.preprocessor.handle_missing_values(df)
        
        # Step 3: カテゴリ変数エンコーディング
        self.logger.info("Step 3: カテゴリエンコーディング")
        df = self.preprocessor.encode_categorical(df)
        
        # Step 4: 日付特徴量抽出
        self.logger.info("Step 4: 日付特徴量抽出")
        df = self.preprocessor.extract_datetime_features(df)
        
        # Step 5: 特徴量エンジニアリング
        self.logger.info("Step 5: 特徴量エンジニアリング")
        df = self.feature_engineer.create_all_features(df)
        
        # Step 6: 数値正規化
        self.logger.info("Step 6: 数値正規化")
        df = self.preprocessor.normalize_numeric(df)
        
        self.logger.info("パイプライン処理完了")
        return df
    
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        テストデータを変換（fit済みパイプライン使用）
        
        Args:
            df: 生データDataFrame
        
        Returns:
            前処理済みDataFrame
        """
        # 同じ処理を適用（fit済みのスケーラー等を使用）
        return self.fit_transform(df)
    
    def save(self, output_dir: Path):
        """パイプラインを保存"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 前処理アーティファクトを保存
        self.preprocessor.save_artifacts(output_dir)
        
        # 設定を保存
        with open(output_dir / 'config.pkl', 'wb') as f:
            pickle.dump(self.config, f)
        
        self.logger.info(f"パイプライン保存完了: {output_dir}")
    
    @classmethod
    def load(cls, input_dir: Path) -> 'DataPreprocessingPipeline':
        """保存済みパイプラインを読み込み"""
        input_dir = Path(input_dir)
        
        # 設定読み込み
        with open(input_dir / 'config.pkl', 'rb') as f:
            config = pickle.load(f)
        
        pipeline = cls(config)
        pipeline.preprocessor.load_artifacts(input_dir)
        
        return pipeline
