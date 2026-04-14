"""
Backend service wrapper for PharmaGuard machine-learning predictions.

This module converts existing variant-matching output into the binary feature
vector expected by the ML classifier and exposes a single integration function
that the analysis route can call.
"""

from typing import Dict

from backend.data.drug_gene_mapping import get_drug_genes
from backend.services.ml.ai_features import (
    calculate_risk_score,
    predict_adverse_reaction,
    suggest_alternative_drug,
)
from backend.services.ml.predictor import (
    GENE_TO_FEATURE_MAP,
    extract_variant_features,
    predict_drug_response,
)


def get_gene_variant_presence(variants_by_gene: Dict[str, list]) -> Dict[str, int]:
    """
    Convert matched variants into a patient-level gene presence map.
    """
    patient_features = extract_variant_features(variants_by_gene)

    return {
        gene_name: int(patient_features.get(feature_name, 0))
        for gene_name, feature_name in GENE_TO_FEATURE_MAP.items()
    }


def build_drug_specific_features(drug_name: str, variants_by_gene: Dict[str, list]) -> Dict[str, int]:
    """
    Build ML features for a specific drug by keeping only its relevant genes.
    """
    patient_features = extract_variant_features(variants_by_gene)
    relevant_genes = set(get_drug_genes(drug_name))

    drug_specific_features = {feature_name: 0 for feature_name in patient_features}
    for gene_name, feature_name in GENE_TO_FEATURE_MAP.items():
        if gene_name in relevant_genes:
            drug_specific_features[feature_name] = int(patient_features.get(feature_name, 0))

    return drug_specific_features


def analyze_ml_drug_response(drug_name: str, variants_by_gene: Dict[str, list]) -> Dict:
    """
    Generate drug-specific ML prediction metadata from matched pharmacogene variants.

    Args:
        drug_name: Drug currently being analyzed.
        variants_by_gene: Dictionary keyed by gene name with matched variant lists.

    Returns:
        Dictionary with ML prediction, risk score, alternatives, and ADR data.
    """
    gene_variants = get_gene_variant_presence(variants_by_gene)
    feature_vector = build_drug_specific_features(drug_name, variants_by_gene)
    prediction_result = predict_drug_response(**feature_vector)
    risk_result = calculate_risk_score(drug_name, feature_vector, prediction_result)
    alternative_result = suggest_alternative_drug(
        gene_variants,
        drug_name=drug_name,
        risk_level=risk_result["risk_level"],
    )
    adr_result = predict_adverse_reaction(
        feature_vector,
        drug_name=drug_name,
        prediction_result=prediction_result,
    )

    if alternative_result["recommended_alternatives"]:
        drug_recommendation = (
            f"Avoid {drug_name}; consider {', '.join(alternative_result['recommended_alternatives'])}"
        )
    elif risk_result["risk_level"] == "Moderate":
        drug_recommendation = f"Use caution with {drug_name} and monitor closely"
    else:
        drug_recommendation = f"Standard therapy risk is lower for {drug_name}"

    return {
        "gene_variants": gene_variants,
        "ml_prediction": prediction_result.get("prediction", "Unavailable"),
        "confidence": prediction_result.get("confidence", 0.0),
        "risk_score": risk_result["risk_score"],
        "risk_level": risk_result["risk_level"],
        "alternative_drugs": alternative_result["recommended_alternatives"],
        "alternative_drug_suggestion": alternative_result,
        "adr_prediction": adr_result,
        "drug_recommendation": drug_recommendation,
        "ml_model_status": prediction_result.get("model_status", "unavailable"),
        "ml_probabilities": prediction_result.get("probabilities", {}),
        "ml_features": feature_vector,
        "ml_error": prediction_result.get("error", ""),
    }
