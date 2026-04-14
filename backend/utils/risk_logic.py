"""
Canonical risk normalization rules for pharmacogenomic analysis.
"""

from typing import Dict, List, Tuple


LOW_MAX_EXCLUSIVE = 0.3
MODERATE_MAX_EXCLUSIVE = 0.7

SEVERITY_TO_RISK_LEVEL = {
    "none": "Low",
    "mild": "Low",
    "moderate": "Moderate",
    "high": "High",
    "critical": "High",
}

SEVERITY_SCORE_RANGES = {
    "none": (0.0, 0.29),
    "mild": (0.0, 0.29),
    "moderate": (0.3, 0.69),
    "high": (0.7, 1.0),
    "critical": (0.7, 1.0),
}


def clamp_risk_score(score: float) -> float:
    """Clamp and round a risk score into the supported 0..1 range."""
    return round(min(max(float(score), 0.0), 1.0), 2)


def risk_level_from_score(score: float) -> str:
    """Map numeric score to risk level using the canonical thresholds."""
    score = clamp_risk_score(score)
    if score < LOW_MAX_EXCLUSIVE:
        return "Low"
    if score < MODERATE_MAX_EXCLUSIVE:
        return "Moderate"
    return "High"


def severity_from_score(score: float) -> str:
    """Derive a default severity from score when no better clinical label exists."""
    risk_level = risk_level_from_score(score)
    if risk_level == "Low":
        return "none"
    if risk_level == "Moderate":
        return "moderate"
    return "high"


def score_matches_severity(score: float, severity: str) -> bool:
    """Return True when a score lies inside the allowed range for a severity label."""
    normalized_severity = str(severity or "").strip().lower()
    allowed_range = SEVERITY_SCORE_RANGES.get(normalized_severity)
    if allowed_range is None:
        return False

    score = clamp_risk_score(score)
    minimum, maximum = allowed_range
    return minimum <= score <= maximum


def align_score_to_severity(score: float, severity: str) -> float:
    """
    Move a score into the valid range for the given severity, preserving it when already valid.
    """
    normalized_severity = str(severity or "").strip().lower()
    minimum, maximum = SEVERITY_SCORE_RANGES.get(normalized_severity, (0.0, 0.3))
    score = clamp_risk_score(score)

    if minimum <= score <= maximum:
        return score

    if score < minimum:
        return round(minimum, 2)
    return round(maximum, 2)


def normalize_risk_triplet(
    risk_score: float,
    severity: str = "",
    risk_level: str = "",
) -> Tuple[Dict, List[str]]:
    """
    Normalize risk_score, severity, and risk_level into a self-consistent state.

    Rules:
    - 0.00-0.29 -> Low
    - 0.30-0.69 -> Moderate
    - 0.70-1.00 -> High
    - severity none -> Low
    - severity moderate -> Moderate
    - severity high/critical -> High
    - severity wins when there is a mismatch; the score is corrected to match it
    """
    corrections = []
    normalized_score = clamp_risk_score(risk_score)
    normalized_severity = str(severity or "").strip().lower()
    normalized_level = str(risk_level or "").strip().title()

    if normalized_severity not in SEVERITY_TO_RISK_LEVEL:
        derived_severity = severity_from_score(normalized_score)
        corrections.append(
            f"severity '{severity}' invalid or missing; set to '{derived_severity}' from risk_score"
        )
        normalized_severity = derived_severity

    expected_level = SEVERITY_TO_RISK_LEVEL[normalized_severity]
    if normalized_level != expected_level:
        corrections.append(
            f"risk_level '{risk_level}' corrected to '{expected_level}' for severity '{normalized_severity}'"
        )
        normalized_level = expected_level

    aligned_score = align_score_to_severity(normalized_score, normalized_severity)
    if aligned_score != normalized_score:
        corrections.append(
            f"risk_score {normalized_score} corrected to {aligned_score} for severity '{normalized_severity}'"
        )
        normalized_score = aligned_score

    expected_level_from_score = risk_level_from_score(normalized_score)
    if normalized_level != expected_level_from_score:
        corrections.append(
            f"risk_level '{normalized_level}' corrected to '{expected_level_from_score}' to match risk_score"
        )
        normalized_level = expected_level_from_score

    return {
        "risk_score": normalized_score,
        "severity": normalized_severity,
        "risk_level": normalized_level,
    }, corrections
