"""Train the XGBoost recovery prediction model."""

import os
import joblib
import json
from datetime import datetime
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    classification_report, roc_auc_score, precision_recall_curve,
    confusion_matrix, f1_score, precision_score, recall_score
)
import xgboost as xgb
from app.ml.features import prepare_dataset, get_feature_names


def train_model(data_path=None, output_dir=None):
    """Train the recovery prediction model."""
    if data_path is None:
        data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
            'data', 'raw', 'synthetic_payments.csv'
        )

    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), 'artifacts')

    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading data from {data_path}...")
    X, y = prepare_dataset(data_path)

    print(f"Dataset: {X.shape[0]} records, {X.shape[1]} features")
    print(f"Target distribution: {np.bincount(y)} (recovered: {y.sum()}, failed: {len(y) - y.sum()})")

    # Split: 70% train, 15% validation, 15% test
    X_temp, X_test, y_temp, y_test = train_test_split(X, y, test_size=0.15, random_state=42, stratify=y)
    X_train, X_val, y_train, y_val = train_test_split(X_temp, y_temp, test_size=0.176, random_state=42, stratify=y_temp)

    print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

    # Train XGBoost
    print("Training XGBoost model...")
    model = xgb.XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='auc',
        early_stopping_rounds=20,
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=10
    )

    # Evaluate
    print("\n=== Evaluation ===")

    def evaluate_split(X_split, y_split, split_name):
        y_pred_proba = model.predict_proba(X_split)[:, 1]
        y_pred = (y_pred_proba >= 0.5).astype(int)

        print(f"\n{split_name} Set:")
        print(f"  ROC-AUC: {roc_auc_score(y_split, y_pred_proba):.4f}")
        print(f"  Precision: {precision_score(y_split, y_pred):.4f}")
        print(f"  Recall: {recall_score(y_split, y_pred):.4f}")
        print(f"  F1: {f1_score(y_split, y_pred):.4f}")

        return {
            'roc_auc': float(roc_auc_score(y_split, y_pred_proba)),
            'precision': float(precision_score(y_split, y_pred)),
            'recall': float(recall_score(y_split, y_pred)),
            'f1': float(f1_score(y_split, y_pred)),
            'confusion_matrix': confusion_matrix(y_split, y_pred).tolist(),
        }

    train_metrics = evaluate_split(X_train, y_train, 'Train')
    val_metrics = evaluate_split(X_val, y_val, 'Validation')
    test_metrics = evaluate_split(X_test, y_test, 'Test')

    # Save model
    model_path = os.path.join(output_dir, 'recovery_model.joblib')
    joblib.dump(model, model_path)
    print(f"\nModel saved to {model_path}")

    # Save feature names
    feature_names_path = os.path.join(output_dir, 'feature_names.json')
    with open(feature_names_path, 'w') as f:
        json.dump(list(X.columns), f, indent=2)
    print(f"Feature names saved to {feature_names_path}")

    # Save metrics
    metrics = {
        'model_version': 'v1',
        'trained_at': datetime.utcnow().isoformat(),
        'n_samples': int(len(X)),
        'n_features': int(X.shape[1]),
        'train_metrics': train_metrics,
        'val_metrics': val_metrics,
        'test_metrics': test_metrics,
    }

    metrics_path = os.path.join(output_dir, 'metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"Metrics saved to {metrics_path}")

    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    print("\nTop 10 Features:")
    print(feature_importance.head(10).to_string(index=False))

    feature_importance_path = os.path.join(output_dir, 'feature_importance.csv')
    feature_importance.to_csv(feature_importance_path, index=False)
    print(f"Feature importance saved to {feature_importance_path}")

    return model, metrics


if __name__ == '__main__':
    train_model()
