"""
Higher-level ML-powered backend features for PharmaGuard.

This module builds on top of the base classifier prediction and exposes:
- drug risk score calculation
- alternative drug suggestions
- adverse drug reaction prediction
- drug-specific AI summary generation
"""

from typing import Dict, List, Optional

from backend.data.drug_gene_mapping import get_drug_genes
from backend.services.ml.predictor import predict_drug_response
from backend.utils.risk_logic import normalize_risk_triplet, risk_level_from_score


# Weighted severity map used to convert class probabilities into a single risk
# score. The weights are intentionally monotonic so the model's probability
# distribution is preserved in the final score.
RISK_CLASS_WEIGHTS = {
    "Normal": 0.10,
    "Intermediate": 0.55,
    "Poor": 0.80,
    "HighRisk": 0.95,
}

# Slightly more conservative weighting for adverse reaction estimation.
ADR_CLASS_WEIGHTS = {
    "Normal": 0.05,
    "Intermediate": 0.45,
    "Poor": 0.78,
    "HighRisk": 0.97,
}

ALTERNATIVE_DRUG_RULES = {
    "CODEINE": ["Morphine", "Tramadol"],
    "WARFARIN": ["Apixaban", "Rivaroxaban"],
    "CLOPIDOGREL": ["Prasugrel", "Ticagrelor"],
    "SIMVASTATIN": ["Pravastatin", "Rosuvastatin"],
    "AZATHIOPRINE": ["Mycophenolate", "Methotrexate"],
    "FLUOROURACIL": ["Raltitrexed", "Irinotecan"],
}

ADR_REACTION_MAP = {
    "CODEINE": "Reduced analgesia or opioid toxicity risk",
    "WARFARIN": "Bleeding risk",
    "CLOPIDOGREL": "Reduced antiplatelet response",
    "SIMVASTATIN": "Statin-associated myopathy",
    "AZATHIOPRINE": "Myelosuppression risk",
    "FLUOROURACIL": "Severe chemotherapy toxicity",
}

SLCO1B1_SIMVASTATIN_INTERPRETATION = (
    "SLCO1B1 variant reduces transporter activity, leading to higher circulating "
    "simvastatin levels and increased risk of muscle toxicity."
)

WARFARIN_CYP2C9_INTERPRETATION = (
    "Reduced CYP2C9 metabolism leading to increased warfarin sensitivity and bleeding risk"
)

GENE_ROLE_MAP = {
    "CYP2D6": "Drug metabolism enzyme converting prodrugs like codeine into active metabolites",
    "CYP2C19": "Activates clopidogrel into its active antiplatelet form",
    "CYP2C9": "Metabolizes warfarin and controls drug clearance",
    "VKORC1": "Drug target regulating warfarin sensitivity",
    "SLCO1B1": "Liver transporter affecting statin uptake and toxicity risk",
    "TPMT": "Thiopurine-metabolizing enzyme that influences azathioprine toxicity risk",
    "DPYD": "Breaks down fluoropyrimidines and influences fluorouracil toxicity risk",
}

# Drug-to-primary-gene mapping used specifically by the AI summary.
# This keeps the summary focused on the clinically relevant pharmacogene(s)
# for the drug being viewed instead of listing every gene detected in the VCF.
DRUG_GENE_MAP = {
    "codeine": ["CYP2D6"],
    "tramadol": ["CYP2D6"],
    "clopidogrel": ["CYP2C19"],
    "warfarin": ["CYP2C9", "VKORC1"],
    "simvastatin": ["SLCO1B1"],
    "azathioprine": ["TPMT"],
    "fluorouracil": ["DPYD"],
}


def _resolve_prediction_result(
    features: Dict[str, int],
    prediction_result: Optional[Dict] = None,
) -> Dict:
    """
    Reuse an existing prediction result when available to avoid duplicate model
    inference, otherwise call the predictor directly.
    """
    if prediction_result is not None:
        return prediction_result

    return predict_drug_response(**features)


def _weighted_probability_score(probabilities: Dict[str, float], weights: Dict[str, float]) -> float:
    """
    Collapse class probabilities into a single severity-weighted score.
    """
    score = 0.0
    for label, weight in weights.items():
        score += float(probabilities.get(label, 0.0)) * weight

    return round(min(max(score, 0.0), 1.0), 2)


def get_primary_genes_for_drug(drug_name: Optional[str]) -> List[str]:
    """
    Resolve the clinically relevant pharmacogene(s) for a drug.

    The explicit summary map takes priority, with the broader backend mapping
    used as a safe fallback for any additional supported drugs.
    """
    normalized_drug_name = (drug_name or "").strip().lower()

    if normalized_drug_name in DRUG_GENE_MAP:
        return DRUG_GENE_MAP[normalized_drug_name]

    return get_drug_genes(drug_name)


def build_gene_snapshot(
    drug_name: Optional[str],
    variants_by_gene: Dict[str, List[Dict]],
) -> List[Dict]:
    """
    Build a drug-specific gene snapshot enriched with functional gene roles.

    The legacy ``gene_variants`` map is left unchanged for frontend
    compatibility; this helper produces an additional structured view that
    backend consumers can use without breaking the existing UI.
    """
    relevant_genes = get_primary_genes_for_drug(drug_name) or get_drug_genes(drug_name)
    normalized_genes = []
    seen_genes = set()

    for gene_name in relevant_genes:
        normalized_gene_name = str(gene_name).upper()
        if normalized_gene_name and normalized_gene_name not in seen_genes:
            seen_genes.add(normalized_gene_name)
            normalized_genes.append(normalized_gene_name)

    if not normalized_genes:
        normalized_genes = [str(gene_name).upper() for gene_name in variants_by_gene.keys()]

    return [
        {
            "gene": gene_name,
            "variant_present": bool(variants_by_gene.get(gene_name, [])),
            "role": GENE_ROLE_MAP.get(gene_name, "Pharmacogene influencing drug response"),
        }
        for gene_name in normalized_genes
    ]


def _filter_detected_variants_for_drug(
    drug_name: Optional[str],
    detected_variants: List[Dict],
) -> List[Dict]:
    """
    Keep only variants that belong to the primary gene(s) relevant to the drug.
    """
    relevant_genes = {
        gene_name.upper()
        for gene_name in get_primary_genes_for_drug(drug_name)
    }

    if not relevant_genes:
        return detected_variants

    filtered_variants = []
    for variant in detected_variants:
        gene_name = str(variant.get("gene", "")).upper()
        if gene_name in relevant_genes:
            filtered_variants.append(variant)

    return filtered_variants


def _derive_detected_pharmacogenes(
    drug_name: Optional[str],
    gene_variants: Dict[str, int],
    filtered_detected_variants: List[Dict],
) -> List[str]:
    """
    Produce drug-specific detected gene labels for the AI summary.
    """
    relevant_genes = get_primary_genes_for_drug(drug_name)
    detected_genes = []
    seen_genes = set()

    for variant in filtered_detected_variants:
        gene_name = str(variant.get("gene", "")).upper()
        if gene_name and gene_name not in seen_genes:
            seen_genes.add(gene_name)
            detected_genes.append(f"{gene_name} variant present")

    if detected_genes:
        return detected_genes

    for gene_name in relevant_genes:
        normalized_gene_name = gene_name.upper()
        if int(gene_variants.get(normalized_gene_name, 0)) == 1 and normalized_gene_name not in seen_genes:
            seen_genes.add(normalized_gene_name)
            detected_genes.append(f"{normalized_gene_name} variant present")

    return detected_genes


def calculate_risk_score(
    drug_name: str,
    features: Dict[str, int],
    prediction_result: Optional[Dict] = None,
) -> Dict:
    """
    Calculate a drug-specific risk score using model probabilities.

    Args:
        drug_name: Drug currently being analyzed.
        features: Binary ML features for the drug.
        prediction_result: Optional cached predictor output.

    Returns:
        Dictionary with numeric score, categorical level, and raw probabilities.
    """
    resolved_prediction = _resolve_prediction_result(features, prediction_result)
    probabilities = resolved_prediction.get("probabilities", {})
    risk_score = _weighted_probability_score(probabilities, RISK_CLASS_WEIGHTS)
    normalized_risk, _ = normalize_risk_triplet(
        risk_score=risk_score,
        severity="",
        risk_level=risk_level_from_score(risk_score),
    )

    return {
        "drug": drug_name,
        "risk_score": normalized_risk["risk_score"],
        "risk_level": normalized_risk["risk_level"],
        "severity": normalized_risk["severity"],
        "probabilities": probabilities,
    }


def suggest_alternative_drug(
    gene_variants: Dict[str, int],
    drug_name: Optional[str] = None,
    risk_level: str = "Low",
) -> Dict:
    """
    Suggest safer alternatives when a drug has high predicted risk.

    Args:
        gene_variants: Binary map of detected pharmacogene variants.
        drug_name: Drug currently being analyzed.
        risk_level: Derived risk category from calculate_risk_score().

    Returns:
        Recommendation dictionary with avoided drug and suggested alternatives.
    """
    normalized_drug_name = (drug_name or "").upper()

    if risk_level != "High" or normalized_drug_name not in ALTERNATIVE_DRUG_RULES:
        return {
            "avoid_drug": normalized_drug_name or None,
            "recommended_alternatives": [],
        }

    # Require at least one detected variant before recommending alternatives.
    if not any(int(value) == 1 for value in gene_variants.values()):
        return {
            "avoid_drug": normalized_drug_name,
            "recommended_alternatives": [],
        }

    return {
        "avoid_drug": normalized_drug_name,
        "recommended_alternatives": ALTERNATIVE_DRUG_RULES[normalized_drug_name],
    }


def predict_adverse_reaction(
    features: Dict[str, int],
    drug_name: Optional[str] = None,
    prediction_result: Optional[Dict] = None,
) -> Dict:
    """
    Estimate the risk of clinically relevant adverse drug reactions.

    Args:
        features: Binary ML features for the drug.
        drug_name: Drug currently being analyzed.
        prediction_result: Optional cached predictor output.

    Returns:
        Dictionary with ADR probability and likely reaction description.
    """
    resolved_prediction = _resolve_prediction_result(features, prediction_result)
    probabilities = resolved_prediction.get("probabilities", {})
    adr_risk = _weighted_probability_score(probabilities, ADR_CLASS_WEIGHTS)
    normalized_drug_name = (drug_name or "UNKNOWN").upper()

    return {
        "drug": normalized_drug_name,
        "adr_risk": adr_risk,
        "possible_reaction": ADR_REACTION_MAP.get(
            normalized_drug_name,
            "General pharmacogenomic adverse reaction risk",
        ),
    }


def generate_ai_summary(analysis_result: Dict) -> Dict:
    """
    Build a structured drug-specific AI summary report.

    Args:
        analysis_result: Finalized analysis dictionary for a single drug.

    Returns:
        Structured JSON-compatible report summarizing the current drug.
    """
    if not analysis_result:
        return {
            "title": "AI SUMMARY REPORT",
            "drug": "UNKNOWN",
            "primary_gene": "UNKNOWN",
            "primary_genes": [],
            "phenotype": "Unknown",
            "clinical_interpretation": "AI summary unavailable because no analysis results were produced.",
            "detected_variants": [],
            "detected_pharmacogenes": [],
            "drug_risk_analysis": {
                "high_risk_drugs": [],
                "moderate_risk_drugs": [],
                "low_risk_drugs": [],
                "counts": {"high": 0, "moderate": 0, "low": 0},
            },
            "recommendations": [],
            "report_text": "AI summary unavailable because no analysis results were produced.",
        }

    drug_name = analysis_result.get("drug", "UNKNOWN")
    primary_genes = get_primary_genes_for_drug(drug_name)
    primary_gene = primary_genes[0] if primary_genes else (
        analysis_result.get("pharmacogenomic_profile", {}).get("primary_gene", "UNKNOWN")
    )
    phenotype = analysis_result.get("pharmacogenomic_profile", {}).get("phenotype", "Unknown")
    gene_variants = analysis_result.get("gene_variants", {})
    detected_variants = analysis_result.get("detected_variants", [])
    filtered_detected_variants = _filter_detected_variants_for_drug(
        drug_name,
        detected_variants,
    )
    detected_genes = _derive_detected_pharmacogenes(
        drug_name,
        gene_variants,
        filtered_detected_variants,
    )

    risk_level = analysis_result.get("risk_level", "Low")
    high_risk_drugs = [drug_name] if risk_level == "High" else []
    moderate_risk_drugs = [drug_name] if risk_level == "Moderate" else []
    low_risk_drugs = [drug_name] if risk_level == "Low" else []

    recommendations = []
    alternatives = analysis_result.get("alternative_drugs", [])
    if alternatives:
        recommendations.append(
            f"Avoid {drug_name}; consider {', '.join(alternatives)}"
        )
    elif analysis_result.get("drug_recommendation"):
        recommendations.append(analysis_result["drug_recommendation"])
    elif analysis_result.get("clinical_recommendation", {}).get("action"):
        recommendations.append(analysis_result["clinical_recommendation"]["action"])

    if not recommendations:
        recommendations.append("No drug-specific safety adjustments were identified")

    clinical_interpretation = (
        analysis_result.get("llm_generated_explanation", {}).get("summary")
        or analysis_result.get("drug_recommendation")
        or analysis_result.get("clinical_recommendation", {}).get("action")
        or "Drug-specific clinical interpretation unavailable."
    )
    if drug_name == "WARFARIN" and primary_gene == "CYP2C9" and filtered_detected_variants:
        clinical_interpretation = WARFARIN_CYP2C9_INTERPRETATION
    if primary_gene == "SLCO1B1" and filtered_detected_variants:
        clinical_interpretation = SLCO1B1_SIMVASTATIN_INTERPRETATION

    report_text_lines = [
        "AI SUMMARY REPORT",
        "",
        f"Drug: {drug_name}",
        f"Primary Gene(s): {', '.join(primary_genes) if primary_genes else primary_gene}",
        "",
        "Detected Pharmacogenes:",
    ]

    if detected_genes:
        report_text_lines.extend(detected_genes)
    else:
        report_text_lines.append("No relevant pharmacogene variants detected for this drug")

    report_text_lines.extend(
        [
            "",
            "Drug Risk Analysis:",
            f"High risk drugs: {len(high_risk_drugs)}",
            f"Moderate risk drugs: {len(moderate_risk_drugs)}",
            f"Low risk drugs: {len(low_risk_drugs)}",
            "",
            f"Phenotype: {phenotype}",
            f"Clinical Interpretation: {clinical_interpretation}",
            "",
            "Recommendation:",
        ]
    )
    report_text_lines.extend(recommendations)

    return {
        "title": "AI SUMMARY REPORT",
        "drug": drug_name,
        "primary_gene": primary_gene,
        "primary_genes": primary_genes,
        "phenotype": phenotype,
        "clinical_interpretation": clinical_interpretation,
        "detected_variants": filtered_detected_variants,
        "detected_pharmacogenes": detected_genes,
        "drug_risk_analysis": {
            "high_risk_drugs": high_risk_drugs,
            "moderate_risk_drugs": moderate_risk_drugs,
            "low_risk_drugs": low_risk_drugs,
            "counts": {
                "high": len(high_risk_drugs),
                "moderate": len(moderate_risk_drugs),
                "low": len(low_risk_drugs),
            },
        },
        "recommendations": recommendations,
        "report_text": "\n".join(report_text_lines),
    }
