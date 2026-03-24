"""
Example ML model using scikit-learn RandomForestClassifier.
Demonstrates how to integrate a trained model into the trading bot.
"""

import logging
from typing import Optional

import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

from ml.base_model import BasePredictionModel

logger = logging.getLogger("ml.sklearn")


class SklearnModel(BasePredictionModel):
    """
    RandomForest-based prediction model.

    Predicts: 0=SELL, 1=HOLD, 2=BUY
    based on technical indicator features.
    """

    def __init__(
        self,
        n_estimators: int = 100,
        max_depth: int = 10,
        random_state: int = 42,
    ):
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            class_weight="balanced",
        )
        self._is_trained = False

    # ── Core Interface ───────────────────────────────────────

    def train(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train the RandomForest model."""
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        self.model.fit(X_train, y_train)
        self._is_trained = True

        # Evaluation
        y_pred = self.model.predict(X_val)
        report = classification_report(
            y_val, y_pred, target_names=["SELL", "HOLD", "BUY"]
        )
        logger.info("Training complete. Validation report:\n%s", report)

        # Feature importance
        importances = self.model.feature_importances_
        feature_names = self.get_feature_columns()
        for name, imp in sorted(
            zip(feature_names[: len(importances)], importances),
            key=lambda x: x[1],
            reverse=True,
        ):
            logger.info("  Feature %s: %.4f", name, imp)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict action labels."""
        if not self._is_trained:
            raise RuntimeError("Model has not been trained yet")
        return self.model.predict(X)

    def predict_proba(self, X: np.ndarray) -> Optional[np.ndarray]:
        """Predict class probabilities."""
        if not self._is_trained:
            return None
        return self.model.predict_proba(X)

    def save(self, path: str) -> None:
        """Save model to disk using joblib."""
        joblib.dump(self.model, path)
        logger.info("Model saved to %s", path)

    def load(self, path: str) -> None:
        """Load model from disk."""
        self.model = joblib.load(path)
        self._is_trained = True
        logger.info("Model loaded from %s", path)


def create_labels(df, future_periods: int = 5, threshold: float = 0.005):
    """
    Create training labels from historical price data.

    Labels:
        0 = SELL  (price drops > threshold)
        1 = HOLD  (price stays within threshold)
        2 = BUY   (price rises > threshold)

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with a 'close' column.
    future_periods : int
        How many candles ahead to look for the return.
    threshold : float
        Minimum return magnitude to trigger a BUY or SELL label.

    Returns
    -------
    np.ndarray
        Labels array aligned with the DataFrame rows.
    """
    close = df["close"]
    future_return = close.shift(-future_periods) / close - 1

    labels = np.where(
        future_return > threshold,
        2,  # BUY
        np.where(future_return < -threshold, 0, 1),  # SELL / HOLD
    )

    return labels
