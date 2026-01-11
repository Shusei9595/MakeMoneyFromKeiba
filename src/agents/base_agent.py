"""
Base Agent Module

全ての専門家AIの基底クラス
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any
import pickle
import logging

import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


class BaseAgent(ABC):
    """
    全エージェントの基底クラス
    
    共通機能:
    - LightGBM Regressorによる10点満点スコア予測
    - モデルの保存・読み込み
    - 特徴量重要度の取得
    - 評価指標の計算
    """
    
    def __init__(self, name: str, version: str = "v1"):
        """
        Args:
            name: エージェント名
            version: モデルバージョン
        """
        self.name = name
        self.version = version
        self.model: Optional[lgb.LGBMRegressor] = None
        self.feature_columns: List[str] = []
        self.is_trained: bool = False
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        
        # モデルパラメータ
        self.model_params = self._get_model_params()
    
    @abstractmethod
    def _get_feature_list(self) -> List[str]:
        """
        このエージェントが使用する特徴量リストを返す
        
        Returns:
            特徴量名のリスト
        """
        pass
    
    def _get_model_params(self) -> Dict[str, Any]:
        """
        LightGBMのモデルパラメータを返す
        サブクラスでオーバーライド可能
        
        Returns:
            モデルパラメータの辞書
        """
        return {
            'objective': 'regression',
            'metric': 'rmse',
            'num_leaves': 31,
            'learning_rate': 0.05,
            'n_estimators': 500,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1,
            'random_state': 42
        }
    
    def _build_model(self) -> lgb.LGBMRegressor:
        """
        LightGBMモデルを構築
        
        Returns:
            LGBMRegressorインスタンス
        """
        return lgb.LGBMRegressor(**self.model_params)
    
    @staticmethod
    def create_target_score(finish_position: int) -> float:
        """
        着順から10点満点の理想スコアを生成
        
        Args:
            finish_position: 着順（1〜18）
        
        Returns:
            10点満点のスコア
        """
        if pd.isna(finish_position) or finish_position <= 0:
            return 5.0  # 欠損値は中間スコア
        
        if finish_position == 1:
            return 10.0
        elif finish_position == 2:
            return 8.5
        elif finish_position == 3:
            return 7.0
        else:
            return max(1.0, 7.0 - (finish_position - 3) * 0.5)
    
    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        特徴量を準備（欠損している特徴量は0で埋める）
        
        Args:
            df: 入力DataFrame
        
        Returns:
            特徴量DataFrame
        """
        if self.model is not None and hasattr(self.model, 'feature_name_'):
            required_features = self.model.feature_name_
        else:
            required_features = self._get_feature_list()
        
        # すべての要求される特徴量を確保（欠落している場合は0で埋める）
        X = pd.DataFrame(index=df.index)
        for f in required_features:
            if f in df.columns:
                # 型変換
                try:
                    X[f] = pd.to_numeric(df[f], errors='coerce')
                except:
                    X[f] = 0.0
            else:
                X[f] = 0.0
        
        # NaNを0で埋める
        X = X.fillna(0)
        
        self.feature_columns = required_features
        return X
    
    def train(self, X: pd.DataFrame, y: pd.Series, 
              groups: Optional[pd.Series] = None,
              n_folds: int = 5) -> Dict[str, float]:
        """
        モデルを訓練
        
        Args:
            X: 特徴量DataFrame
            y: ターゲット（10点満点スコア）
            groups: グループID（レースID）
            n_folds: 交差検証のフォールド数
        
        Returns:
            評価指標の辞書
        """
        self.logger.info(f"Training {self.name}...")
        
        # 特徴量を準備
        X_prepared = self._prepare_features(X)
        
        # 交差検証
        tscv = TimeSeriesSplit(n_splits=n_folds)
        fold_metrics = []
        
        for fold, (train_idx, val_idx) in enumerate(tscv.split(X_prepared)):
            X_train, X_val = X_prepared.iloc[train_idx], X_prepared.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
            
            model = self._build_model()
            model.fit(
                X_train, y_train,
                eval_set=[(X_val, y_val)],
                callbacks=[lgb.early_stopping(50, verbose=False)]
            )
            
            y_pred = model.predict(X_val)
            
            metrics = {
                'fold': fold + 1,
                'rmse': np.sqrt(mean_squared_error(y_val, y_pred)),
                'mae': mean_absolute_error(y_val, y_pred),
                'r2': r2_score(y_val, y_pred)
            }
            fold_metrics.append(metrics)
            self.logger.info(f"Fold {fold + 1}: RMSE={metrics['rmse']:.4f}, MAE={metrics['mae']:.4f}, R²={metrics['r2']:.4f}")
        
        # 全データで最終モデルを訓練
        self.model = self._build_model()
        self.model.fit(X_prepared, y)
        self.is_trained = True
        
        # 平均指標を計算
        avg_metrics = {
            'rmse': np.mean([m['rmse'] for m in fold_metrics]),
            'mae': np.mean([m['mae'] for m in fold_metrics]),
            'r2': np.mean([m['r2'] for m in fold_metrics])
        }
        
        self.logger.info(f"Training complete. Avg RMSE={avg_metrics['rmse']:.4f}, Avg R²={avg_metrics['r2']:.4f}")
        return avg_metrics
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        予測を実行
        
        Args:
            X: 特徴量DataFrame
        
        Returns:
            10点満点のスコア配列
        """
        if not self.is_trained:
            raise RuntimeError(f"{self.name} is not trained yet")
        
        X_prepared = self._prepare_features(X)
        predictions = self.model.predict(X_prepared)
        
        # 1.0〜10.0の範囲にクリップ
        predictions = np.clip(predictions, 1.0, 10.0)
        
        return predictions
    
    def evaluate(self, X: pd.DataFrame, y: pd.Series) -> Dict[str, float]:
        """
        モデルを評価
        
        Args:
            X: 特徴量DataFrame
            y: ターゲット
        
        Returns:
            評価指標の辞書
        """
        y_pred = self.predict(X)
        
        return {
            'rmse': np.sqrt(mean_squared_error(y, y_pred)),
            'mae': mean_absolute_error(y, y_pred),
            'r2': r2_score(y, y_pred)
        }
    
    def get_feature_importance(self) -> pd.DataFrame:
        """
        特徴量重要度を取得
        
        Returns:
            特徴量重要度のDataFrame
        """
        if not self.is_trained:
            raise RuntimeError(f"{self.name} is not trained yet")
        
        importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return importance
    
    def save_model(self, output_dir: Path) -> Path:
        """
        モデルを保存
        
        Args:
            output_dir: 保存先ディレクトリ
        
        Returns:
            保存されたファイルパス
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{self.name}_{self.version}.pkl"
        filepath = output_dir / filename
        
        with open(filepath, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'feature_columns': self.feature_columns,
                'model_params': self.model_params,
                'is_trained': self.is_trained,
                'name': self.name,
                'version': self.version
            }, f)
        
        self.logger.info(f"Model saved to {filepath}")
        return filepath
    
    def load_model(self, filepath: Path) -> None:
        """
        モデルを読み込み
        
        Args:
            filepath: モデルファイルパス
        """
        filepath = Path(filepath)
        
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        self.model = data['model']
        self.feature_columns = data['feature_columns']
        self.model_params = data['model_params']
        self.is_trained = data['is_trained']
        self.name = data['name']
        self.version = data['version']
        
        self.logger.info(f"Model loaded from {filepath}")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', trained={self.is_trained})"
