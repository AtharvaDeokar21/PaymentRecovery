"""Recovery probability prediction service."""

import os
import joblib
import json
import pandas as pd
from typing import Dict, Any
from app.ml.features import extract_features
from app.utils.logging import get_logger

logger = get_logger('predictor')


class RecoveryPredictor:
    """ML model for predicting payment recovery probability."""

    def __init__(self):
        self.model = None
        self.feature_names = None
        self.model_version = 'v1'
        self._load_model()

    def _load_model(self):
        """Load the trained model from disk."""
        artifacts_dir = os.path.join(os.path.dirname(__file__), 'artifacts')
        model_path = os.path.join(artifacts_dir, 'recovery_model.joblib')
        feature_names_path = os.path.join(artifacts_dir, 'feature_names.json')

        if not os.path.exists(model_path):
            logger.warning(f"Model not found at {model_path}. Predictor will return default probabilities.")
            return

        try:
            self.model = joblib.load(model_path)
            with open(feature_names_path, 'r') as f:
                self.feature_names = json.load(f)
            logger.info(f"Loaded recovery model from {model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None

    def predict(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict recovery probability for a single payment.

        Args:
            payment_data: Dict with keys matching the synthetic dataset schema.

        Returns:
            Dict with 'probability', 'expected_recovery', 'model_version'.
        """
        if self.model is None:
            # Fallback: return a baseline probability
            logger.warning("Model not loaded. Returning baseline probability.")
            baseline_prob = 0.35
            return {
                'probability': baseline_prob,
                'expected_recovery': int(payment_data.get('amount', 0) * baseline_prob),
                'model_version': 'baseline',
            }

        try:
            # Convert to DataFrame
            df = pd.DataFrame([payment_data])

            # Extract features
            X = extract_features(df)

            # Ensure feature alignment
            for col in self.feature_names:
                if col not in X.columns:
                    X[col] = 0
            X = X[self.feature_names]

            # Predict
            prob = float(self.model.predict_proba(X)[0, 1])
            amount = payment_data.get('amount', 0)

            return {
                'probability': round(prob, 4),
                'expected_recovery': int(amount * prob),
                'model_version': self.model_version,
            }

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            # Fallback
            return {
                'probability': 0.35,
                'expected_recovery': int(payment_data.get('amount', 0) * 0.35),
                'model_version': 'error_fallback',
            }

    def predict_batch(self, payments: list) -> list:
        """Predict recovery probabilities for multiple payments."""
        return [self.predict(p) for p in payments]


# Singleton instance
_predictor = None


def get_predictor() -> RecoveryPredictor:
    """Get or create the singleton predictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = RecoveryPredictor()
    return _predictor
