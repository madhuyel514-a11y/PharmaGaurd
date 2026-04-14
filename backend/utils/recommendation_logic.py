"""
Centralized recommendation decision and response consistency helpers.
"""

from typing import Dict, List, Tuple

from backend.services.ml.ai_features import ALTERNATIVE_DRUG_RULES

SIMVASTATIN_SLCO1B1_RECOMMENDATION = (
    "Use lower dose or consider alternative statin (pravastatin or rosuvastatin)"
)


def _resolve_simvastatin_variant_override(response: Dict, current_recommendation: str) -> str:
    """
    Apply the Simvastatin-only recommendation override when SLCO1B1 variants are present.
    """
    if response.get("drug") != "SIMVASTATIN":
        return current_recommendation

    primary_gene = response.get("pharmacogenomic_profile", {}).get("primary_gene")
    detected_variants = response.get("detected_variants", []) or []
    has_variant = bool(detected_variants)

    if primary_gene == "SLCO1B1" and has_variant:
        return SIMVASTATIN_SLCO1B1_RECOMMENDATION

    return current_recommendation


def determine_final_recommendation(
    drug_name: str,
    phenotype: str,
    severity: str,
    risk_label: str,
) -> Tuple[str, List[str]]:
    """
    Resolve a single final recommendation string from phenotype, severity, and drug.
    """
    normalized_drug = str(drug_name or "").upper()
    normalized_phenotype = str(phenotype or "").upper()
    normalized_severity = str(severity or "").lower()
    normalized_risk_label = str(risk_label or "").lower()
    alternatives = ALTERNATIVE_DRUG_RULES.get(normalized_drug, [])

    if normalized_drug == "CLOPIDOGREL" and normalized_phenotype == "PM":
        return "Avoid Clopidogrel; use prasugrel or ticagrelor", ["Prasugrel", "Ticagrelor"]

    if normalized_drug == "SIMVASTATIN" and normalized_phenotype in {"IM", "PM"}:
        return "Use lower dose or consider alternative statin (pravastatin or rosuvastatin)", alternatives

    if normalized_risk_label == "ineffective" or normalized_phenotype == "PM":
        if alternatives:
            return f"Avoid {normalized_drug.title()}; use {', '.join(alternatives)}", alternatives
        return f"Avoid {normalized_drug.title()}", alternatives

    if normalized_risk_label == "toxic" and normalized_severity in {"high", "critical"}:
        if alternatives:
            return f"Avoid {normalized_drug.title()}; use {', '.join(alternatives)}", alternatives
        return f"Avoid {normalized_drug.title()}", alternatives

    if normalized_phenotype == "IM":
        if normalized_drug == "WARFARIN":
            return "Reduce dose", alternatives
        return "Use caution", alternatives

    if normalized_phenotype == "NM":
        return "Standard dosing", alternatives

    return "Use caution", alternatives


def apply_recommendation_consistency(response: Dict) -> Tuple[Dict, List[str]]:
    """
    Normalize recommendation fields without modifying genotype or phenotype.
    """
    corrected = dict(response)
    corrections = []

    phenotype = corrected.get("pharmacogenomic_profile", {}).get("phenotype", "Unknown")
    severity = corrected.get("risk_assessment", {}).get("severity", "")
    risk_label = corrected.get("risk_assessment", {}).get("risk_label", "")
    drug_name = corrected.get("drug", "")

    final_recommendation, alternatives = determine_final_recommendation(
        drug_name=drug_name,
        phenotype=phenotype,
        severity=severity,
        risk_label=risk_label,
    )
    final_recommendation = _resolve_simvastatin_variant_override(corrected, final_recommendation)

    if corrected.get("drug_recommendation") != final_recommendation:
        corrections.append("drug_recommendation corrected to centralized final recommendation")
    corrected["drug_recommendation"] = final_recommendation

    if corrected.get("cpic_recommendation") != final_recommendation:
        corrections.append("cpic_recommendation corrected to centralized final recommendation")
    corrected["cpic_recommendation"] = final_recommendation

    clinical = corrected.setdefault("clinical_recommendation", {})
    if clinical.get("action") != final_recommendation:
        corrections.append("clinical_recommendation.action corrected to centralized final recommendation")
    clinical["action"] = final_recommendation

    if "Avoid" in final_recommendation:
        corrected["alternative_drugs"] = alternatives
    else:
        corrected["alternative_drugs"] = []

    ai_summary = corrected.get("ai_summary")
    if isinstance(ai_summary, dict):
        if ai_summary.get("recommendations") != [final_recommendation]:
            corrections.append("ai_summary.recommendations corrected to centralized final recommendation")
        ai_summary["recommendations"] = [final_recommendation]
        report_text = str(ai_summary.get("report_text", ""))
        if "Recommendation:" in report_text:
            prefix = report_text.split("Recommendation:")[0].rstrip()
            ai_summary["report_text"] = f"{prefix}\n\nRecommendation:\n{final_recommendation}"

    return corrected, corrections


def validate_gene_fields(response: Dict) -> Tuple[Dict, List[str]]:
    """
    Keep gene fields aligned with actually detected variants for the current drug.
    """
    corrected = dict(response)
    corrections = []

    detected_variants = corrected.get("detected_variants", []) or []
    detected_genes = []
    seen = set()
    for variant in detected_variants:
        gene_name = str(variant.get("gene", "")).upper()
        if gene_name and gene_name not in seen:
            seen.add(gene_name)
            detected_genes.append(gene_name)

    expected_gene_variants = {gene_name: 1 for gene_name in detected_genes}
    if corrected.get("gene_variants") != expected_gene_variants:
        corrections.append("gene_variants corrected to reflect only detected genes")
    corrected["gene_variants"] = expected_gene_variants

    if corrected.get("genes_detected") != detected_genes:
        corrections.append("genes_detected corrected to include only genes present in detected_variants")
    corrected["genes_detected"] = detected_genes

    return corrected, corrections


def validate_recommendation_consistency(response: Dict) -> List[str]:
    """
    Report recommendation-level contradictions without changing phenotype/genotype.
    """
    errors = []
    phenotype = response.get("pharmacogenomic_profile", {}).get("phenotype", "Unknown")
    severity = response.get("risk_assessment", {}).get("severity", "")
    risk_label = response.get("risk_assessment", {}).get("risk_label", "")
    final_recommendation, _ = determine_final_recommendation(
        response.get("drug", ""),
        phenotype,
        severity,
        risk_label,
    )
    final_recommendation = _resolve_simvastatin_variant_override(response, final_recommendation)

    recommendation_fields = {
        "drug_recommendation": response.get("drug_recommendation"),
        "cpic_recommendation": response.get("cpic_recommendation"),
        "clinical_recommendation.action": response.get("clinical_recommendation", {}).get("action"),
    }
    for field_name, value in recommendation_fields.items():
        if value != final_recommendation:
            errors.append(f"{field_name} inconsistent with centralized final recommendation")

    ai_summary_recommendations = response.get("ai_summary", {}).get("recommendations")
    if ai_summary_recommendations not in (None, [final_recommendation]):
        errors.append("ai_summary.recommendations inconsistent with centralized final recommendation")

    if (
        response.get("drug") == "SIMVASTATIN"
        and response.get("pharmacogenomic_profile", {}).get("primary_gene") == "SLCO1B1"
        and (response.get("detected_variants", []) or [])
        and final_recommendation == "Standard dosing"
    ):
        errors.append("Simvastatin with SLCO1B1 variant cannot keep Standard dosing recommendation")

    if phenotype == "NM" and "Avoid" in final_recommendation:
        errors.append("normal metabolizer cannot have avoid-drug recommendation")

    return errors
