"""
Base model interface for pluggable AI/ML predictions.
Any ML framework (sklearn, TensorFlow, PyTorch, XGBoost, etc.)
can be integrated by subclassing BasePredictionModel.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

import numpy as np
import pandas as pd


class BasePredictionModel(ABC):
    """
    Abstract base class for all prediction models.

    Subclass this to integrate any ML framework:
    - scikit-learn (RandomForest, GradientBoosting, SVM)
    - TensorFlow / Keras (LSTM, Transformer)
    - PyTorch (custom architectures)
    - XGBoost / LightGBM
    - Custom rule engines

    The model should predict one of: 0=SELL, 1=HOLD, 2=BUY
    """

    ACTION_MAP = {0: "SELL", 1: "HOLD", 2: "BUY"}

    @abstractmethod
    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """
        Train the model on historical features and labels.

        Parameters
        ----------
        X : np.ndarray
            Feature matrix of shape (n_samples, n_features).
        y : np.ndarray
            Label vector of shape (n_samples,).
            Values: 0=SELL, 1=HOLD, 2=BUY.
        """
        ...

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict action labels for the given features.

        Parameters
        ----------
        X : np.ndarray
            Feature matrix of shape (n_samples, n_features).

        Returns
        -------
        np.ndarray
            Predicted labels (0=SELL, 1=HOLD, 2=BUY).
        """
        ...

    def predict_proba(self, X: np.ndarray) -> Optional[np.ndarray]:
        """
        Predict class probabilities (optional).

        Returns
        -------
        np.ndarray | None
            Probability matrix of shape (n_samples, 3) or None.
        """
        return None

    @abstractmethod
    def save(self, path: str) -> None:
        """Save the trained model to disk."""
        ...

    @abstractmethod
    def load(self, path: str) -> None:
        """Load a trained model from disk."""
        ...

    def get_feature_columns(self) -> List[str]:
        """
        Return the list of expected feature column names.
        Override this if your model uses specific features.
        """
        return [
            "rsi",
            "ema_fast",
            "ema_slow",
            "macd_line",
            "macd_signal",
            "macd_histogram",
            "price_change",
            "volatility",
        ]

    def prepare_features(self, df: pd.DataFrame) -> np.ndarray:
        """Extract the feature matrix from a DataFrame."""
        cols = [c for c in self.get_feature_columns() if c in df.columns]
        return df[cols].values
