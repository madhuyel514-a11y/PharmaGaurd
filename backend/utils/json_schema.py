"""
JSON Schema Validator
Ensures API responses match required schema for hackathon
"""

import json
from typing import Tuple, List
from datetime import datetime
from backend.utils.risk_logic import normalize_risk_triplet
from backend.utils.recommendation_logic import (
    apply_recommendation_consistency,
    validate_gene_fields,
    validate_recommendation_consistency,
)
from backend.services.llm_explainer import (
    SLCO1B1_SIMVASTATIN_MECHANISM,
    SLCO1B1_SIMVASTATIN_SUMMARY,
    WARFARIN_IM_MECHANISM,
    WARFARIN_IM_SUMMARY,
)


def _normalize_warfarin_explanation(response: dict) -> Tuple[dict, List[str]]:
    """
    Warfarin-only explanation guard for CYP2C9 IM phenotype.
    """
    corrected = response
    corrections = []

    if corrected.get("drug") != "WARFARIN":
        return corrected, corrections

    profile = corrected.get("pharmacogenomic_profile", {})
    if profile.get("primary_gene") != "CYP2C9" or profile.get("phenotype") != "IM":
        return corrected, corrections

    llm_explanation = corrected.setdefault("llm_generated_explanation", {})
    existing_summary = str(llm_explanation.get("summary", "")).upper()
    existing_mechanism = str(llm_explanation.get("biological_mechanism", "")).upper()

    if "NM" in existing_summary or "NORMAL METABOLIZER" in existing_summary or "NM" in existing_mechanism or "NORMAL METABOLIZER" in existing_mechanism:
        corrections.append("Warfarin explanation corrected to match CYP2C9 IM phenotype")

    llm_explanation["summary"] = WARFARIN_IM_SUMMARY
    llm_explanation["biological_mechanism"] = WARFARIN_IM_MECHANISM

    return corrected, corrections


def _lock_warfarin_cyp2c9_phenotype(response: dict) -> Tuple[dict, List[str]]:
    """
    Warfarin-only phenotype/diplotype lock.

    This prevents downstream defaults such as NM or *1/*1 from overriding the
    CYP2C9 variant-derived interpretation when reduced-function alleles are
    already present in detected_variants.
    """
    corrected = response
    corrections = []

    if corrected.get("drug") != "WARFARIN":
        return corrected, corrections

    detected_variants = corrected.get("detected_variants", []) or []
    detected_rsids = {str(variant.get("rsid", "")).strip() for variant in detected_variants}
    primary_gene = corrected.get("pharmacogenomic_profile", {}).get("primary_gene")

    if primary_gene != "CYP2C9":
        return corrected, corrections

    has_star2 = "rs1799853" in detected_rsids
    has_star3 = "rs1057910" in detected_rsids
    has_reduced_function = has_star2 or has_star3

    profile = corrected.setdefault("pharmacogenomic_profile", {})
    current_diplotype = str(profile.get("diplotype", ""))
    current_phenotype = str(profile.get("phenotype", ""))

    if has_star2 and has_star3:
        if current_diplotype != "*2/*3" or current_phenotype != "IM":
            corrections.append("Warfarin CYP2C9 phenotype lock reapplied from detected variants")
        profile["diplotype"] = "*2/*3"
        profile["phenotype"] = "IM"
    elif has_reduced_function:
        if current_diplotype == "*1/*1":
            corrections.append("Warfarin CYP2C9 diplotype corrected from default *1/*1")
            profile["diplotype"] = "*1/*2" if has_star2 else "*1/*3"
        if current_phenotype == "NM":
            corrections.append("Warfarin CYP2C9 phenotype corrected from default NM")
            profile["phenotype"] = "IM"

    return corrected, corrections


def _normalize_simvastatin_explanation(response: dict) -> Tuple[dict, List[str]]:
    """
    Simvastatin-only explanation guard.

    Ensures SLCO1B1 output uses the transporter-based explanation template and
    contains no CYP3A4 or metabolizer language in explanation fields.
    """
    corrected = response
    corrections = []

    if corrected.get("drug") != "SIMVASTATIN":
        return corrected, corrections

    primary_gene = corrected.get("pharmacogenomic_profile", {}).get("primary_gene")
    if primary_gene != "SLCO1B1":
        return corrected, corrections

    llm_explanation = corrected.setdefault("llm_generated_explanation", {})
    existing_summary = str(llm_explanation.get("summary", ""))
    existing_mechanism = str(llm_explanation.get("biological_mechanism", ""))
    ai_summary = corrected.get("ai_summary")
    ai_interpretation = str(ai_summary.get("clinical_interpretation", "")) if isinstance(ai_summary, dict) else ""

    combined_text = " ".join([existing_summary, existing_mechanism, ai_interpretation]).upper()
    contains_forbidden_terms = "CYP3A4" in combined_text or "METABOLIZER" in combined_text
    lacks_transporter_logic = "TRANSPORTER" not in combined_text and "HEPATIC UPTAKE" not in combined_text

    if contains_forbidden_terms or lacks_transporter_logic:
        corrections.append("Simvastatin explanation corrected to SLCO1B1 transporter-based template")

    llm_explanation["summary"] = SLCO1B1_SIMVASTATIN_SUMMARY
    llm_explanation["biological_mechanism"] = SLCO1B1_SIMVASTATIN_MECHANISM

    if isinstance(ai_summary, dict):
        ai_summary["clinical_interpretation"] = SLCO1B1_SIMVASTATIN_SUMMARY
        report_text = str(ai_summary.get("report_text", ""))
        if report_text:
            lines = report_text.splitlines()
            rewritten_lines = []
            for line in lines:
                if line.startswith("Clinical Interpretation:"):
                    rewritten_lines.append(f"Clinical Interpretation: {SLCO1B1_SIMVASTATIN_SUMMARY}")
                else:
                    upper_line = line.upper()
                    if "CYP3A4" in upper_line or "METABOLIZER" in upper_line:
                        continue
                    rewritten_lines.append(line)
            ai_summary["report_text"] = "\n".join(rewritten_lines)

    return corrected, corrections


PHARMACOGUARD_OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["patient_id", "drug", "timestamp", "risk_assessment", "pharmacogenomic_profile", "clinical_recommendation", "llm_generated_explanation", "quality_metrics"],
    "properties": {
        "patient_id": {
            "type": "string"
        },
        "drug": {
            "type": "string",
            "enum": ["CODEINE", "WARFARIN", "CLOPIDOGREL", "SIMVASTATIN", "AZATHIOPRINE", "FLUOROURACIL"]
        },
        "timestamp": {
            "type": "string"
        },
        "risk_assessment": {
            "type": "object",
            "required": ["risk_label", "confidence_score", "severity"],
            "properties": {
                "risk_label": {
                    "type": "string",
                    "enum": ["Safe", "Adjust Dosage", "Toxic", "Ineffective", "Unknown"]
                },
                "confidence_score": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1
                },
                "severity": {
                    "type": "string",
                    "enum": ["none", "mild", "moderate", "high", "critical"]
                }
            }
        },
        "pharmacogenomic_profile": {
            "type": "object",
            "required": ["primary_gene", "phenotype"],
            "properties": {
                "primary_gene": {
                    "type": "string"
                },
                "diplotype": {
                    "type": "string"
                },
                "phenotype": {
                    "type": "string",
                    "enum": ["PM", "IM", "NM", "RM", "URM"]
                },
                "detected_variants": {
                    "type": "array",
                    "items": {
                        "type": "object"
                    }
                }
            }
        },
        "clinical_recommendation": {
            "type": "object",
            "properties": {
                "action": {"type": "string"},
                "cpic_guideline": {"type": "string"},
                "monitoring": {"type": "string"}
            }
        },
        "llm_generated_explanation": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "biological_mechanism": {"type": "string"},
                "variant_effects": {"type": "object"}
            }
        },
        "quality_metrics": {
            "type": "object",
            "properties": {
                "vcf_parsing_success": {"type": "boolean"},
                "variant_confidence": {"type": "number"},
                "completeness": {"type": "number"}
            }
        }
    }
}


def validate_output(response: dict) -> Tuple[bool, List[str]]:
    """
    Validate output JSON against required schema

    Args:
        response: Response dictionary to validate

    Returns:
        Tuple of (is_valid: bool, error_messages: list)
    """
    errors = []

    # Check required root fields
    required_fields = ["patient_id", "drug", "timestamp", "risk_assessment", "pharmacogenomic_profile", "clinical_recommendation", "llm_generated_explanation", "quality_metrics"]

    for field in required_fields:
        if field not in response:
            errors.append(f"Missing required field: {field}")
        elif response[field] is None:
            errors.append(f"Field '{field}' is null")

    # Validate field types
    if "drug" in response and response["drug"] not in ["CODEINE", "WARFARIN", "CLOPIDOGREL", "SIMVASTATIN", "AZATHIOPRINE", "FLUOROURACIL"]:
        errors.append(f"Invalid drug: {response['drug']}")

    # Validate risk_assessment
    if "risk_assessment" in response:
        risk = response["risk_assessment"]
        if not isinstance(risk, dict):
            errors.append("risk_assessment must be an object")
        else:
            if "risk_label" not in risk:
                errors.append("Missing risk_assessment.risk_label")
            elif risk["risk_label"] not in ["Safe", "Adjust Dosage", "Toxic", "Ineffective", "Unknown"]:
                errors.append(f"Invalid risk_label: {risk['risk_label']}")

            if "confidence_score" not in risk:
                errors.append("Missing risk_assessment.confidence_score")
            elif not isinstance(risk["confidence_score"], (int, float)):
                errors.append("confidence_score must be a number")
            elif not (0 <= risk["confidence_score"] <= 1):
                errors.append(f"confidence_score must be between 0 and 1, got {risk['confidence_score']}")

            if "severity" not in risk:
                errors.append("Missing risk_assessment.severity")
            elif risk["severity"] not in ["none", "mild", "moderate", "high", "critical"]:
                errors.append(f"Invalid severity: {risk['severity']}")

    risk_score = response.get("risk_score")
    risk_level = response.get("risk_level")
    severity = response.get("risk_assessment", {}).get("severity")
    if isinstance(risk_score, (int, float)) and severity is not None:
        normalized_risk, _ = normalize_risk_triplet(risk_score, severity, risk_level)
        if response.get("risk_level") != normalized_risk["risk_level"]:
            errors.append(
                f"risk_level '{response.get('risk_level')}' inconsistent with severity '{severity}' and risk_score {risk_score}"
            )
        if round(float(risk_score), 2) != normalized_risk["risk_score"]:
            errors.append(
                f"risk_score {risk_score} inconsistent with severity '{severity}'"
            )
        if severity != normalized_risk["severity"]:
            errors.append(
                f"severity '{severity}' inconsistent with normalized severity '{normalized_risk['severity']}'"
            )

    # Validate pharmacogenomic_profile
    if "pharmacogenomic_profile" in response:
        profile = response["pharmacogenomic_profile"]
        if not isinstance(profile, dict):
            errors.append("pharmacogenomic_profile must be an object")
        else:
            if "primary_gene" not in profile:
                errors.append("Missing pharmacogenomic_profile.primary_gene")

            if "phenotype" not in profile:
                errors.append("Missing pharmacogenomic_profile.phenotype")
            elif profile["phenotype"] not in ["PM", "IM", "NM", "RM", "URM"]:
                errors.append(f"Invalid phenotype: {profile['phenotype']}")

            if "detected_variants" in profile and not isinstance(profile["detected_variants"], list):
                errors.append("detected_variants must be an array")

    # Validate llm_generated_explanation
    if "llm_generated_explanation" in response:
        exp = response["llm_generated_explanation"]
        if not isinstance(exp, dict):
            errors.append("llm_generated_explanation must be an object")
        else:
            if "summary" not in exp:
                errors.append("Missing llm_generated_explanation.summary")
            elif not exp["summary"]:
                errors.append("llm_generated_explanation.summary cannot be empty")

    # Validate quality_metrics
    if "quality_metrics" in response:
        metrics = response["quality_metrics"]
        if not isinstance(metrics, dict):
            errors.append("quality_metrics must be an object")

    errors.extend(validate_recommendation_consistency(response))

    return len(errors) == 0, errors


def ensure_schema_compliance(data: dict) -> dict:
    """
    Add missing fields with defaults to ensure compliance

    Args:
        data: Potentially incomplete response data

    Returns:
        Compliant response dictionary
    """
    compliant = data.copy()

    # Add timestamp if missing
    if "timestamp" not in compliant or not compliant["timestamp"]:
        compliant["timestamp"] = datetime.utcnow().isoformat() + "Z"

    # Ensure patient_id exists
    if "patient_id" not in compliant:
        compliant["patient_id"] = "PATIENT_UNKNOWN"

    # Ensure drug exists
    if "drug" not in compliant:
        compliant["drug"] = "UNKNOWN"

    # Ensure risk_assessment structure
    if "risk_assessment" not in compliant:
        compliant["risk_assessment"] = {}

    risk = compliant["risk_assessment"]
    if "risk_label" not in risk:
        risk["risk_label"] = "Unknown"
    if "confidence_score" not in risk:
        risk["confidence_score"] = 0.5
    if "severity" not in risk:
        risk["severity"] = "moderate"

    # Ensure pharmacogenomic_profile structure
    if "pharmacogenomic_profile" not in compliant:
        compliant["pharmacogenomic_profile"] = {}

    profile = compliant["pharmacogenomic_profile"]
    if "primary_gene" not in profile:
        profile["primary_gene"] = "UNKNOWN"
    if "phenotype" not in profile:
        profile["phenotype"] = "Unknown"
    if "detected_variants" not in profile:
        profile["detected_variants"] = []

    # Ensure clinical_recommendation structure
    if "clinical_recommendation" not in compliant:
        compliant["clinical_recommendation"] = {}

    clinical = compliant["clinical_recommendation"]
    if "action" not in clinical:
        clinical["action"] = ""
    if "cpic_guideline" not in clinical:
        clinical["cpic_guideline"] = ""

    # Ensure llm_generated_explanation structure
    if "llm_generated_explanation" not in compliant:
        compliant["llm_generated_explanation"] = {}

    exp = compliant["llm_generated_explanation"]
    if "summary" not in exp:
        exp["summary"] = "Clinical explanation unavailable"
    if "biological_mechanism" not in exp:
        exp["biological_mechanism"] = ""
    if "variant_effects" not in exp:
        exp["variant_effects"] = {}

    # Ensure quality_metrics structure
    if "quality_metrics" not in compliant:
        compliant["quality_metrics"] = {}

    metrics = compliant["quality_metrics"]
    if "vcf_parsing_success" not in metrics:
        metrics["vcf_parsing_success"] = True
    if "variant_confidence" not in metrics:
        metrics["variant_confidence"] = 0.5
    if "completeness" not in metrics:
        metrics["completeness"] = 0.5

    return compliant


def format_output_json(data: dict) -> str:
    """
    Format response data as compliant JSON

    Args:
        data: Response data

    Returns:
        Formatted JSON string
    """
    # Ensure compliance first
    compliant = ensure_schema_compliance(data)

    # Convert to JSON with nice formatting
    return json.dumps(compliant, indent=2)


def validate_and_fix(response: dict) -> Tuple[dict, List[str]]:
    """
    Validate response and auto-fix common issues

    Args:
        response: Response to validate

    Returns:
        Tuple of (fixed_response: dict, remaining_errors: list)
    """
    # First try to ensure compliance
    fixed = ensure_schema_compliance(response)

    risk_assessment = fixed.get("risk_assessment", {})
    normalized_risk, corrections = normalize_risk_triplet(
        fixed.get("risk_score", 0.0),
        risk_assessment.get("severity", ""),
        fixed.get("risk_level", ""),
    )
    fixed["risk_score"] = normalized_risk["risk_score"]
    fixed["risk_level"] = normalized_risk["risk_level"]
    fixed["risk_assessment"]["severity"] = normalized_risk["severity"]
    fixed, warfarin_lock_corrections = _lock_warfarin_cyp2c9_phenotype(fixed)
    fixed, warfarin_explanation_corrections = _normalize_warfarin_explanation(fixed)
    fixed, simvastatin_explanation_corrections = _normalize_simvastatin_explanation(fixed)
    fixed, gene_corrections = validate_gene_fields(fixed)
    fixed, recommendation_corrections = apply_recommendation_consistency(fixed)

    # Then validate
    is_valid, errors = validate_output(fixed)

    return fixed, corrections + warfarin_lock_corrections + warfarin_explanation_corrections + simvastatin_explanation_corrections + gene_corrections + recommendation_corrections + errors
