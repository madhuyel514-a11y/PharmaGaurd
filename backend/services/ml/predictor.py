"""
Prediction helpers for the PharmaGuard ML module.

The functions in this module load the saved model artifact, transform raw
variant-presence inputs into a pandas DataFrame, and return a class label plus
confidence score. Imports for optional ML dependencies are kept lazy so the
rest of the backend can still run even if the model stack is not installed yet.
"""

from pathlib import Path
from typing import Dict, Tuple


CURRENT_DIR = Path(__file__).resolve().parent
MODEL_PATH = CURRENT_DIR / "models" / "drug_response_model.pkl"
FEATURE_COLUMNS = [
    "CYP2C19_variant",
    "CYP2D6_variant",
    "SLCO1B1_variant",
    "CYP2C9_variant",
    "TPMT_variant",
    "DPYD_variant",
]
GENE_TO_FEATURE_MAP = {
    "CYP2C19": "CYP2C19_variant",
    "CYP2D6": "CYP2D6_variant",
    "SLCO1B1": "SLCO1B1_variant",
    "CYP2C9": "CYP2C9_variant",
    "TPMT": "TPMT_variant",
    "DPYD": "DPYD_variant",
}

_MODEL_CACHE = None


def _import_prediction_dependencies():
    """
    Import optional ML dependencies only when prediction is requested.

    Returns:
        Tuple containing (pandas_module, joblib_module)
    """
    try:
        import pandas as pd
        import joblib
    except ImportError as exc:
        raise RuntimeError(
            "ML dependencies are not installed. Install pandas, scikit-learn, and joblib."
        ) from exc

    return pd, joblib


def load_model() -> Dict:
    """
    Load and cache the trained model artifact from disk.

    Returns:
        A dictionary with the estimator and metadata.
    """
    global _MODEL_CACHE

    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Trained model not found at {MODEL_PATH}. Run train_model.py first."
        )

    _, joblib = _import_prediction_dependencies()
    artifact = joblib.load(MODEL_PATH)

    if isinstance(artifact, dict) and "model" in artifact:
        _MODEL_CACHE = artifact
    else:
        _MODEL_CACHE = {
            "model": artifact,
            "feature_columns": FEATURE_COLUMNS,
            "target_column": "Drug_Response",
        }

    return _MODEL_CACHE


def build_feature_payload(
    CYP2C19_variant: int = 0,
    CYP2D6_variant: int = 0,
    SLCO1B1_variant: int = 0,
    CYP2C9_variant: int = 0,
    TPMT_variant: int = 0,
    DPYD_variant: int = 0,
) -> Dict[str, int]:
    """
    Build a normalized feature dictionary from raw binary inputs.

    Returns:
        Dictionary in the exact feature order expected by the model.
    """
    raw_payload = {
        "CYP2C19_variant": CYP2C19_variant,
        "CYP2D6_variant": CYP2D6_variant,
        "SLCO1B1_variant": SLCO1B1_variant,
        "CYP2C9_variant": CYP2C9_variant,
        "TPMT_variant": TPMT_variant,
        "DPYD_variant": DPYD_variant,
    }

    return {
        feature_name: 1 if int(raw_payload.get(feature_name, 0)) > 0 else 0
        for feature_name in FEATURE_COLUMNS
    }


def extract_variant_features(variants_by_gene: Dict[str, list]) -> Dict[str, int]:
    """
    Convert matched pharmacogene variants into binary ML features.

    Args:
        variants_by_gene: Dictionary keyed by gene name with matched variant lists.

    Returns:
        A binary feature vector compatible with the trained model.
    """
    features = {feature_name: 0 for feature_name in FEATURE_COLUMNS}

    for gene_name, feature_name in GENE_TO_FEATURE_MAP.items():
        matched_variants = variants_by_gene.get(gene_name, [])
        features[feature_name] = 1 if matched_variants else 0

    return features


def predict_drug_response(
    CYP2C19_variant: int = 0,
    CYP2D6_variant: int = 0,
    SLCO1B1_variant: int = 0,
    CYP2C9_variant: int = 0,
    TPMT_variant: int = 0,
    DPYD_variant: int = 0,
) -> Dict:
    """
    Predict drug response risk from pharmacogenomic variant features.

    Returns:
        Dictionary containing the predicted class label and confidence score.
    """
    feature_payload = build_feature_payload(
        CYP2C19_variant=CYP2C19_variant,
        CYP2D6_variant=CYP2D6_variant,
        SLCO1B1_variant=SLCO1B1_variant,
        CYP2C9_variant=CYP2C9_variant,
        TPMT_variant=TPMT_variant,
        DPYD_variant=DPYD_variant,
    )

    try:
        pd, _ = _import_prediction_dependencies()
        artifact = load_model()
    except (RuntimeError, FileNotFoundError) as exc:
        return {
            "prediction": "Unavailable",
            "confidence": 0.0,
            "model_status": "unavailable",
            "error": str(exc),
            "features": feature_payload,
        }

    input_frame = pd.DataFrame(
        [{column: feature_payload[column] for column in artifact["feature_columns"]}]
    )

    model = artifact["model"]
    prediction = str(model.predict(input_frame)[0])
    probabilities = model.predict_proba(input_frame)[0]
    confidence = round(float(max(probabilities)), 2)
    probability_map = {
        str(label): round(float(probability), 4)
        for label, probability in zip(model.classes_, probabilities)
    }

    return {
        "prediction": prediction,
        "confidence": confidence,
        "model_status": "ready",
        "probabilities": probability_map,
        "features": feature_payload,
    }

