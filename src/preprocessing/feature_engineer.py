"""
特徴量エンジニアリングモジュール

レースデータから予測用の特徴量を生成するクラス
"""
import pandas as pd
import numpy as np
from typing import Dict, List
import logging


class FeatureEngineer:
    """特徴量エンジニアリングを行うクラス"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def create_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        全ての特徴量を生成
        
        Args:
            df: 前処理済みDataFrame
        
        Returns:
            特徴量追加済みDataFrame
        """
        df = df.copy()
        
        self.logger.info("特徴量生成開始...")
        
        # 前走関連特徴量
        df = self.create_past_performance_features(df)
        
        # 距離・コース特徴量
        df = self.create_distance_course_features(df)
        
        # 騎手・調教師特徴量
        df = self.create_jockey_trainer_features(df)
        
        # 相対特徴量
        df = self.create_relative_features(df)
        
        # 統計特徴量
        df = self.create_statistical_features(df)
        
        self.logger.info(f"特徴量生成完了: {len(df.columns)}カラム")
        
        return df
    
    def create_past_performance_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        前走関連の特徴量を生成
        
        特徴量:
        - recent_3_avg_speed: 直近3走の平均速度
        - recent_3_finish_variance: 直近3走の着順分散
        - days_since_last_race: 前走からの経過日数
        - last_race_position: 前走の着順
        - recent_3_win_count: 直近3走での勝利数
        - recent_5_avg_odds: 直近5走の平均オッズ
        - speed_trend_slope: 直近5走の速度トレンド
        - consistency_score: 着順の一貫性スコア
        
        Args:
            df: DataFrame
        
        Returns:
            特徴量追加済みDataFrame
        """
        df = df.copy()
        
        # 馬ごとにソート（日付順）
        df = df.sort_values(['horse_id', 'race_date'])
        
        # 速度を計算 (finish_timeが秒の場合)
        if 'finish_time' in df.columns and 'distance' in df.columns:
            df['speed'] = df['distance'] / (df['finish_time'] + 1e-6)  # m/秒
        else:
            df['speed'] = 0
        
        # 直近3走の平均速度
        df['recent_3_avg_speed'] = df.groupby('horse_id')['speed'].transform(
            lambda x: x.rolling(window=3, min_periods=1).mean().shift(1)
        )
        
        # 直近3走の着順分散
        if 'finish_position' in df.columns:
            df['recent_3_finish_variance'] = df.groupby('horse_id')['finish_position'].transform(
                lambda x: x.rolling(window=3, min_periods=1).var().shift(1)
            )
        
        # 前走からの経過日数
        if 'race_date' in df.columns:
            df['days_since_last_race'] = df.groupby('horse_id')['race_date'].diff().dt.days
            df['days_since_last_race'] = df['days_since_last_race'].fillna(0)
        
        # 前走の着順
        if 'finish_position' in df.columns:
            df['last_race_position'] = df.groupby('horse_id')['finish_position'].shift(1)
        
        # 勝利フラグ
        if 'finish_position' in df.columns:
            df['is_win'] = (df['finish_position'] == 1).astype(int)
        else:
            df['is_win'] = 0
        
        # 直近3走での勝利数
        df['recent_3_win_count'] = df.groupby('horse_id')['is_win'].transform(
            lambda x: x.rolling(window=3, min_periods=1).sum().shift(1)
        )
        
        # 直近5走の平均オッズ
        if 'odds' in df.columns:
            df['recent_5_avg_odds'] = df.groupby('horse_id')['odds'].transform(
                lambda x: x.rolling(window=5, min_periods=1).mean().shift(1)
            )
        
        # 速度トレンド（線形回帰の傾き）
        def calculate_trend(series):
            series = series.dropna()
            if len(series) < 2:
                return 0
            x = np.arange(len(series))
            try:
                slope = np.polyfit(x, series, 1)[0]
                return slope
            except:
                return 0
        
        df['speed_trend_slope'] = df.groupby('horse_id')['speed'].transform(
            lambda x: x.rolling(window=5, min_periods=2).apply(calculate_trend, raw=False).shift(1)
        )
        
        # 一貫性スコア（着順の標準偏差の逆数）
        if 'finish_position' in df.columns:
            df['consistency_score'] = df.groupby('horse_id')['finish_position'].transform(
                lambda x: 1 / (x.rolling(window=5, min_periods=2).std().shift(1) + 1)
            )
        
        return df
    
    def create_distance_course_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        距離・コース関連の特徴量を生成
        
        特徴量:
        - distance_experience_count: この距離の出走回数
        - track_experience_count: この競馬場の出走回数
        - distance_win_rate: この距離での勝率
        - track_win_rate: この競馬場での勝率
        - distance_category: 距離カテゴリ
        - distance_adaptability_score: 距離適性スコア
        
        Args:
            df: DataFrame
        
        Returns:
            特徴量追加済みDataFrame
        """
        df = df.copy()
        
        # 距離カテゴリ
        if 'distance' in df.columns:
            df['distance_category'] = pd.cut(
                df['distance'],
                bins=[0, 1400, 1800, 2200, 5000],
                labels=['sprint', 'mile', 'middle', 'long']
            )
        
        # 累積経験値（レースごとに更新）
        # 注意: 現在のレースを含まないようshift(1)
        if 'distance' in df.columns:
            df['distance_experience_count'] = df.groupby(
                ['horse_id', 'distance']
            ).cumcount()  # 0始まりなのでshift不要（現在のレースはカウントされない）
        
        if 'track_name' in df.columns:
            df['track_experience_count'] = df.groupby(
                ['horse_id', 'track_name']
            ).cumcount()  # 0始まりなのでshift不要
        
        # 距離別勝率（過去の成績から計算）
        # 注意: 現在のレース結果を含まないようshift(1)
        if 'distance' in df.columns and 'is_win' in df.columns:
            df['distance_wins'] = df.groupby(['horse_id', 'distance'])['is_win'].cumsum().shift(1).fillna(0)
            df['distance_win_rate'] = df['distance_wins'] / (df['distance_experience_count'] + 1)
        
        # 競馬場別勝率
        # 注意: 現在のレース結果を含まないようshift(1)
        if 'track_name' in df.columns and 'is_win' in df.columns:
            df['track_wins'] = df.groupby(['horse_id', 'track_name'])['is_win'].cumsum().shift(1).fillna(0)
            df['track_win_rate'] = df['track_wins'] / (df['track_experience_count'] + 1)
        
        # 芝/ダート別勝率
        # 注意: 現在のレース結果を含まないようshift(1)
        if 'track_type' in df.columns and 'is_win' in df.columns:
            df['track_type_wins'] = df.groupby(['horse_id', 'track_type'])['is_win'].cumsum().shift(1).fillna(0)
            df['track_type_experience'] = df.groupby(['horse_id', 'track_type']).cumcount()
            df['track_type_win_rate'] = df['track_type_wins'] / (df['track_type_experience'] + 1)
        
        # 距離適性スコア（前走距離との差）
        if 'distance' in df.columns:
            df['last_race_distance'] = df.groupby('horse_id')['distance'].shift(1)
            df['distance_change'] = df['distance'] - df['last_race_distance']
            df['distance_adaptability_score'] = np.exp(-np.abs(df['distance_change'].fillna(0)) / 400)
        
        return df
    
    def create_jockey_trainer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        騎手・調教師関連の特徴量を生成
        
        特徴量:
        - jockey_win_rate_overall: 騎手の全体勝率
        - trainer_win_rate_overall: 調教師の全体勝率
        - jockey_horse_combination_count: 騎手×馬の組み合わせ回数
        - jockey_horse_combination_wins: 騎手×馬の組み合わせ勝利数
        
        Args:
            df: DataFrame
        
        Returns:
            特徴量追加済みDataFrame
        """
        df = df.copy()
        
        # 騎手の全体勝率（累積）
        # 注意: 現在のレース結果を含まないようshift(1)
        if 'jockey_id' in df.columns and 'is_win' in df.columns:
            df['jockey_race_count'] = df.groupby('jockey_id').cumcount()  # 0始まり
            df['jockey_wins'] = df.groupby('jockey_id')['is_win'].cumsum().shift(1).fillna(0)
            df['jockey_win_rate_overall'] = df['jockey_wins'] / (df['jockey_race_count'] + 1)
        
        # 調教師の全体勝率（累積）
        # 注意: 現在のレース結果を含まないようshift(1)
        if 'trainer_id' in df.columns and 'is_win' in df.columns:
            df['trainer_race_count'] = df.groupby('trainer_id').cumcount()  # 0始まり
            df['trainer_wins'] = df.groupby('trainer_id')['is_win'].cumsum().shift(1).fillna(0)
            df['trainer_win_rate_overall'] = df['trainer_wins'] / (df['trainer_race_count'] + 1)
        
        # 騎手×馬の組み合わせ
        if 'jockey_id' in df.columns and 'horse_id' in df.columns:
            df['jockey_horse_combination_count'] = df.groupby(
                ['jockey_id', 'horse_id']
            ).cumcount()
            
            if 'is_win' in df.columns:
                df['jockey_horse_combination_wins'] = df.groupby(
                    ['jockey_id', 'horse_id']
                )['is_win'].cumsum().shift(1).fillna(0)  # 現在のレースを含まない
        
        return df
    
    def create_relative_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        レース内での相対的な特徴量を生成
        
        特徴量:
        - relative_weight: レース内での相対体重
        - relative_odds: レース内での相対オッズ
        - odds_rank: オッズ順位
        - weight_advantage: 斤量アドバンテージ
        
        Args:
            df: DataFrame
        
        Returns:
            特徴量追加済みDataFrame
        """
        df = df.copy()
        
        # レース内の平均値を計算
        agg_dict = {}
        if 'horse_weight' in df.columns:
            agg_dict['horse_weight'] = 'mean'
        if 'odds' in df.columns:
            agg_dict['odds'] = 'mean'
        if 'weight' in df.columns:
            agg_dict['weight'] = 'mean'
        
        if agg_dict:
            race_stats = df.groupby('race_id').agg(agg_dict).reset_index()
            race_stats.columns = ['race_id'] + [f'avg_{c}' for c in agg_dict.keys()]
            df = df.merge(race_stats, on='race_id', how='left')
        
        # 相対値を計算
        if 'horse_weight' in df.columns and 'avg_horse_weight' in df.columns:
            df['relative_weight'] = df['horse_weight'] - df['avg_horse_weight']
        
        if 'odds' in df.columns and 'avg_odds' in df.columns:
            df['relative_odds'] = df['odds'] - df['avg_odds']
        
        if 'weight' in df.columns and 'avg_weight' in df.columns:
            df['weight_advantage'] = df['avg_weight'] - df['weight']
        
        # レース内順位
        if 'odds' in df.columns:
            df['odds_rank'] = df.groupby('race_id')['odds'].rank(method='min')
        
        return df
    
    def create_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        統計的な特徴量を生成
        
        特徴量:
        - career_total_races: 通算出走回数
        - career_win_rate: 通算勝率
        - career_place_rate: 通算連対率
        - career_show_rate: 通算複勝率
        - recent_form_score: 直近調子スコア
        - rest_days_category: 休養日数カテゴリ
        
        Args:
            df: DataFrame
        
        Returns:
            特徴量追加済みDataFrame
        """
        df = df.copy()
        
        # 通算成績
        # 注意: 現在のレースを含まないように計算
        df['career_total_races'] = df.groupby('horse_id').cumcount()  # 0始まり（現在のレースを含まない）
        
        if 'is_win' in df.columns:
            # 現在のレース結果を含まないようshift(1)
            df['career_total_wins'] = df.groupby('horse_id')['is_win'].cumsum().shift(1).fillna(0)
            df['career_win_rate'] = df['career_total_wins'] / (df['career_total_races'] + 1)
            # 初出走の場合は0
            df.loc[df['career_total_races'] == 0, 'career_win_rate'] = 0.0
        
        # 連対・複勝
        # 注意: 現在のレース結果を含まないようshift(1)
        if 'finish_position' in df.columns:
            df['is_place'] = (df['finish_position'] <= 2).astype(int)
            df['is_show'] = (df['finish_position'] <= 3).astype(int)
            # 現在のレースを含まない累積平均
            df['career_place_rate'] = df.groupby('horse_id')['is_place'].transform(
                lambda x: x.expanding().mean().shift(1)
            ).fillna(0)
            df['career_show_rate'] = df.groupby('horse_id')['is_show'].transform(
                lambda x: x.expanding().mean().shift(1)
            ).fillna(0)
        
        # 直近調子スコア（加重平均: 最近ほど重み大）
        def weighted_recent_form(positions):
            positions = positions.dropna()
            if len(positions) == 0:
                return 0
            weights = np.exp(np.linspace(-1, 0, len(positions)))
            scores = 1 / (positions + 1)  # 着順が良いほど高スコア
            return np.average(scores, weights=weights)
        
        if 'finish_position' in df.columns:
            df['recent_form_score'] = df.groupby('horse_id')['finish_position'].transform(
                lambda x: x.rolling(window=5, min_periods=1).apply(weighted_recent_form, raw=False).shift(1)
            )
        
        # 休養日数カテゴリ
        if 'days_since_last_race' in df.columns:
            df['rest_days_category'] = pd.cut(
                df['days_since_last_race'].fillna(0),
                bins=[-1, 14, 30, 60, 365, 10000],
                labels=['short', 'normal', 'medium', 'long', 'very_long']
            )
        
        return df
    
    def get_feature_importance_ranking(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        特徴量の統計情報を取得
        
        Returns:
            特徴量の統計DataFrame
        """
        feature_stats = []
        
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_columns:
            stats = {
                'feature': col,
                'mean': df[col].mean(),
                'std': df[col].std(),
                'min': df[col].min(),
                'max': df[col].max(),
                'missing_ratio': df[col].isna().mean()
            }
            feature_stats.append(stats)
        
        return pd.DataFrame(feature_stats).sort_values('missing_ratio')
