"""Setup script: generate dataset and train model."""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from app.seed.generate_dataset import generate_dataset
from app.ml.train import train_model


def main():
    print("=== RecoverAI ML Setup ===\n")

    # Generate synthetic dataset
    print("Step 1: Generating synthetic dataset...")
    dataset_path = generate_dataset(n_records=12000)
    print(f"✓ Dataset created: {dataset_path}\n")

    # Train model
    print("Step 2: Training recovery prediction model...")
    model, metrics = train_model(data_path=dataset_path)
    print(f"✓ Model trained successfully\n")

    print("=== Setup Complete ===")
    print(f"Test ROC-AUC: {metrics['test_metrics']['roc_auc']:.4f}")
    print(f"Test F1: {metrics['test_metrics']['f1']:.4f}")


if __name__ == '__main__':
    main()
