"""
Training script for the PharmaGuard drug-response classifier.

This module reads a synthetic pharmacogenomic dataset, trains a
RandomForestClassifier, evaluates it, and saves the trained model to disk.
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split


# Resolve paths relative to this file so the script works from any directory.
CURRENT_DIR = Path(__file__).resolve().parent
DATASET_PATH = CURRENT_DIR / "dataset" / "training_data.csv"
MODELS_DIR = CURRENT_DIR / "models"
MODEL_PATH = MODELS_DIR / "drug_response_model.pkl"

# Define the exact feature order used by both training and inference.
FEATURE_COLUMNS = [
    "CYP2C19_variant",
    "CYP2D6_variant",
    "SLCO1B1_variant",
    "CYP2C9_variant",
    "TPMT_variant",
    "DPYD_variant",
]
TARGET_COLUMN = "Drug_Response"


def load_training_data() -> pd.DataFrame:
    """
    Load the synthetic pharmacogenomic dataset from CSV.

    Returns:
        A pandas DataFrame containing feature columns and the target label.
    """
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Training dataset not found: {DATASET_PATH}")

    return pd.read_csv(DATASET_PATH)


def train_model() -> dict:
    """
    Train and evaluate the Random Forest classifier.

    Returns:
        A dictionary containing the trained model artifact and metrics.
    """
    # Step 1: Load the full dataset into memory.
    dataset = load_training_data()

    # Step 2: Separate input features from the target label.
    features = dataset[FEATURE_COLUMNS]
    target = dataset[TARGET_COLUMN]

    # Step 3: Split the dataset so we can evaluate on unseen records.
    # Stratification keeps class balance similar across train/test splits.
    X_train, X_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.25,
        random_state=42,
        stratify=target,
    )

    # Step 4: Initialize the classifier.
    # A moderate number of trees is enough for this small synthetic dataset.
    model = RandomForestClassifier(
        n_estimators=250,
        max_depth=8,
        random_state=42,
        class_weight="balanced",
    )

    # Step 5: Fit the model using the training portion of the dataset.
    model.fit(X_train, y_train)

    # Step 6: Evaluate accuracy and per-class metrics on the held-out split.
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    report = classification_report(y_test, predictions)

    print(f"Model accuracy: {accuracy:.4f}")
    print("Classification report:")
    print(report)

    # Step 7: Save both the estimator and metadata needed during inference.
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model": model,
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
    }
    joblib.dump(artifact, MODEL_PATH)
    print(f"Saved trained model to: {MODEL_PATH}")

    return {
        "artifact": artifact,
        "accuracy": accuracy,
        "classification_report": report,
        "model_path": MODEL_PATH,
    }


if __name__ == "__main__":
    train_model()

