"""
データ前処理モジュール

レースデータのクリーニング、エンコーディング、正規化を行うクラス
"""
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder, OrdinalEncoder
from sklearn.impute import SimpleImputer
from typing import Dict, List, Tuple, Optional
import logging
from pathlib import Path
import pickle


class RaceDataPreprocessor:
    """レースデータの前処理を行うクラス"""
    
    def __init__(self, config: Dict):
        """
        Args:
            config: 前処理設定（config.yamlから読み込み）
        """
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # スケーラーとエンコーダーを保存（推論時に再利用）
        self.scalers = {}
        self.encoders = {}
        self.imputers = {}
        
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        データクリーニング
        
        処理内容:
        1. 重複行の削除
        2. 不正な値の修正
        3. データ型の変換
        4. 外れ値の検出と処理
        
        Args:
            df: 生データのDataFrame
        
        Returns:
            クリーニング済みDataFrame
        """
        df_clean = df.copy()
        
        # 重複削除
        initial_rows = len(df_clean)
        df_clean = df_clean.drop_duplicates(
            subset=['race_id', 'horse_id'],
            keep='first'
        )
        removed_rows = initial_rows - len(df_clean)
        if removed_rows > 0:
            self.logger.info(f"重複行を削除: {removed_rows}件")
        
        # データ型変換
        df_clean = self._convert_dtypes(df_clean)
        
        # 外れ値処理
        df_clean = self._handle_outliers(df_clean)
        
        # 不正値の修正
        df_clean = self._fix_invalid_values(df_clean)
        
        return df_clean
    
    def _convert_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """データ型の変換"""
        df = df.copy()
        
        # 日付型変換
        date_columns = ['race_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # 数値型変換
        numeric_columns = [
            'distance', 'finish_position', 'horse_number', 'frame_number',
            'weight', 'finish_time', 'odds', 'popularity', 
            'horse_weight', 'horse_weight_diff', 'prize_money', 'race_number'
        ]
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # カテゴリ型変換
        categorical_columns = [
            'track_name', 'track_type', 'track_condition', 
            'weather', 'sex_age', 'grade'
        ]
        for col in categorical_columns:
            if col in df.columns:
                df[col] = df[col].astype('category')
        
        return df
    
    def _handle_outliers(self, df: pd.DataFrame) -> pd.DataFrame:
        """外れ値の処理"""
        df = df.copy()
        threshold = self.config.get('outlier_threshold', 3.0)
        
        # 数値カラムに対して外れ値を検出
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            if col in ['race_id', 'horse_id', 'jockey_id', 'trainer_id']:
                continue  # IDカラムはスキップ
            
            if df[col].std() == 0:
                continue
                
            mean = df[col].mean()
            std = df[col].std()
            
            # 外れ値をNaNに変換（後で補完）
            outlier_mask = np.abs((df[col] - mean) / std) > threshold
            outlier_count = outlier_mask.sum()
            
            if outlier_count > 0:
                self.logger.warning(
                    f"{col}: {outlier_count}件の外れ値を検出"
                )
                df.loc[outlier_mask, col] = np.nan
        
        return df
    
    def _fix_invalid_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """不正値の修正"""
        df = df.copy()
        
        # 着順が0以下または馬数以上の場合
        if 'finish_position' in df.columns:
            invalid_position = (df['finish_position'] <= 0) | \
                              (df['finish_position'] > 18)
            df.loc[invalid_position, 'finish_position'] = np.nan
        
        # オッズが1.0未満
        if 'odds' in df.columns:
            df.loc[df['odds'] < 1.0, 'odds'] = np.nan
        
        # 距離が範囲外（1000-4000m）
        if 'distance' in df.columns:
            invalid_distance = (df['distance'] < 1000) | \
                              (df['distance'] > 4000)
            df.loc[invalid_distance, 'distance'] = np.nan
        
        return df
    
    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        欠損値の処理
        
        戦略:
        - 数値: 中央値補完 or 前方補完
        - カテゴリ: 最頻値補完
        - 時系列: 前方補完
        
        Args:
            df: DataFrame
        
        Returns:
            欠損値処理済みDataFrame
        """
        df = df.copy()
        strategy = self.config.get('missing_value_strategy', 'median')
        
        # 数値カラム
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            missing_count = df[col].isna().sum()
            if missing_count == 0:
                continue
            
            # 全て欠損の場合はスキップ（補完不可能）
            if missing_count == len(df):
                self.logger.warning(f"{col}: 全て欠損のためスキップ")
                continue
                
            if col not in self.imputers:
                if strategy == 'median':
                    self.imputers[col] = SimpleImputer(strategy='median')
                elif strategy == 'mean':
                    self.imputers[col] = SimpleImputer(strategy='mean')
                else:
                    self.imputers[col] = SimpleImputer(strategy='constant', fill_value=0)
                
                df[col] = self.imputers[col].fit_transform(df[[col]]).ravel()
            else:
                df[col] = self.imputers[col].transform(df[[col]]).ravel()
        
        # カテゴリカラム
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns
        for col in categorical_columns:
            missing_count = df[col].isna().sum()
            if missing_count == 0:
                continue
            
            # 全て欠損の場合はスキップ（補完不可能）
            if missing_count == len(df):
                self.logger.warning(f"{col}: 全て欠損のためスキップ")
                continue
                
            if col not in self.imputers:
                self.imputers[col] = SimpleImputer(strategy='most_frequent')
                # カテゴリをstr型に変換してから補完
                df[col] = self.imputers[col].fit_transform(df[[col]].astype(str)).ravel()
            else:
                df[col] = self.imputers[col].transform(df[[col]].astype(str)).ravel()
        
        return df
    
    def encode_categorical(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        カテゴリ変数のエンコーディング
        
        手法:
        - 競馬場名: LabelEncoding
        - 馬場状態: OrdinalEncoding（良 > 稍重 > 重 > 不良）
        - 天気: OrdinalEncoding
        - トラックタイプ: LabelEncoding
        
        Args:
            df: DataFrame
        
        Returns:
            エンコーディング済みDataFrame
        """
        df = df.copy()
        
        # 馬場状態（順序あり）
        if 'track_condition' in df.columns:
            track_condition_order = [['良', '稍重', '重', '不良']]
            if 'track_condition' not in self.encoders:
                self.encoders['track_condition'] = OrdinalEncoder(
                    categories=track_condition_order,
                    handle_unknown='use_encoded_value',
                    unknown_value=-1
                )
                df['track_condition_encoded'] = self.encoders['track_condition'].fit_transform(
                    df[['track_condition']].astype(str)
                )
            else:
                df['track_condition_encoded'] = self.encoders['track_condition'].transform(
                    df[['track_condition']].astype(str)
                )
        
        # 競馬場名（順序なし）
        if 'track_name' in df.columns:
            if 'track_name' not in self.encoders:
                self.encoders['track_name'] = LabelEncoder()
                df['track_name_encoded'] = self.encoders['track_name'].fit_transform(
                    df['track_name'].astype(str)
                )
            else:
                # 未知のラベルを処理
                known_labels = set(self.encoders['track_name'].classes_)
                df['track_name_encoded'] = df['track_name'].apply(
                    lambda x: self.encoders['track_name'].transform([str(x)])[0] 
                    if str(x) in known_labels else -1
                )
        
        # トラックタイプ（芝/ダート）
        if 'track_type' in df.columns:
            if 'track_type' not in self.encoders:
                self.encoders['track_type'] = LabelEncoder()
                df['track_type_encoded'] = self.encoders['track_type'].fit_transform(
                    df['track_type'].astype(str)
                )
            else:
                known_labels = set(self.encoders['track_type'].classes_)
                df['track_type_encoded'] = df['track_type'].apply(
                    lambda x: self.encoders['track_type'].transform([str(x)])[0] 
                    if str(x) in known_labels else -1
                )
        
        # grade（グレード）
        if 'grade' in df.columns:
            if 'grade' not in self.encoders:
                self.encoders['grade'] = LabelEncoder()
                df['grade_encoded'] = self.encoders['grade'].fit_transform(
                    df['grade'].astype(str)
                )
            else:
                known_labels = set(self.encoders['grade'].classes_)
                df['grade_encoded'] = df['grade'].apply(
                    lambda x: self.encoders['grade'].transform([str(x)])[0] 
                    if str(x) in known_labels else -1
                )
        
        return df
    
    def normalize_numeric(self, df: pd.DataFrame, 
                         columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        数値データの正規化
        
        Args:
            df: DataFrame
            columns: 正規化対象カラム（Noneの場合は全数値カラム）
        
        Returns:
            正規化済みDataFrame
        """
        df = df.copy()
        
        if columns is None:
            columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # ID系カラムと既にエンコード済みのカラムを除外
        exclude_patterns = ['_id', '_encoded', '_normalized', 'race_number', 
                           'horse_number', 'frame_number', 'finish_position']
        columns = [c for c in columns if not any(p in c for p in exclude_patterns)]
        
        for col in columns:
            if col not in self.scalers:
                self.scalers[col] = StandardScaler()
                values = df[[col]].values
                if not np.isnan(values).all():
                    df[f'{col}_normalized'] = self.scalers[col].fit_transform(values)
            else:
                df[f'{col}_normalized'] = self.scalers[col].transform(df[[col]])
        
        return df
    
    def extract_datetime_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        日付から特徴量を抽出
        
        抽出内容:
        - year: 年
        - month: 月
        - day: 日
        - day_of_week: 曜日（0=月曜, 6=日曜）
        - is_weekend: 週末フラグ
        - season: 季節（春夏秋冬）
        
        Args:
            df: DataFrame
        
        Returns:
            日付特徴量追加済みDataFrame
        """
        df = df.copy()
        
        if 'race_date' in df.columns:
            df['year'] = df['race_date'].dt.year
            df['month'] = df['race_date'].dt.month
            df['day'] = df['race_date'].dt.day
            df['day_of_week'] = df['race_date'].dt.dayofweek
            df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
            
            # 季節
            df['season'] = pd.cut(
                df['month'],
                bins=[0, 3, 6, 9, 12],
                labels=['winter', 'spring', 'summer', 'autumn']
            )
        
        return df
    
    def save_artifacts(self, output_dir: Path):
        """
        スケーラーとエンコーダーを保存（推論時に再利用）
        
        Args:
            output_dir: 保存先ディレクトリ
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # スケーラー保存
        with open(output_dir / 'scalers.pkl', 'wb') as f:
            pickle.dump(self.scalers, f)
        
        # エンコーダー保存
        with open(output_dir / 'encoders.pkl', 'wb') as f:
            pickle.dump(self.encoders, f)
        
        # 補完器保存
        with open(output_dir / 'imputers.pkl', 'wb') as f:
            pickle.dump(self.imputers, f)
        
        self.logger.info(f"前処理アーティファクトを保存: {output_dir}")
    
    def load_artifacts(self, input_dir: Path):
        """保存済みアーティファクトを読み込み"""
        input_dir = Path(input_dir)
        
        with open(input_dir / 'scalers.pkl', 'rb') as f:
            self.scalers = pickle.load(f)
        
        with open(input_dir / 'encoders.pkl', 'rb') as f:
            self.encoders = pickle.load(f)
        
        with open(input_dir / 'imputers.pkl', 'rb') as f:
            self.imputers = pickle.load(f)
        
        self.logger.info(f"前処理アーティファクトを読み込み: {input_dir}")
