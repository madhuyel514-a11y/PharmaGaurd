"""
CPIC Recommendations Service
Wraps the CPIC guidelines database and provides dosing recommendations
"""

from typing import Dict, Optional
from backend.data.cpic_guidelines import get_cpic_recommendation, get_cpic_action, get_cpic_dosing, get_cpic_monitoring


def get_recommendation(drug_name: str, phenotype: str) -> Dict:
    """
    Get CPIC guideline recommendations for a drug-phenotype pair

    Args:
        drug_name: Name of drug (e.g., 'CODEINE')
        phenotype: Phenotype classification (PM/IM/NM/RM/URM)

    Returns:
        Comprehensive CPIC recommendation dictionary
    """
    recommendation = get_cpic_recommendation(drug_name, phenotype)

    if not recommendation:
        return {
            "drug": drug_name,
            "phenotype": phenotype,
            "error": f"No CPIC guidelines found for {drug_name} with phenotype {phenotype}",
            "action": "Unknown",
            "dosing": "Consult pharmacist",
            "monitoring": "Regular monitoring"
        }

    return {
        "drug": drug_name,
        "phenotype": phenotype,
        "action": recommendation.get('action', 'Unknown'),
        "dosing": recommendation.get('dosing', ''),
        "monitoring": recommendation.get('monitoring', ''),
        "evidence": recommendation.get('evidence', ''),
        "clinical_notes": recommendation.get('clinical_notes', ''),
        "cpic_guidelines": True
    }


def get_action(drug_name: str, phenotype: str) -> Optional[str]:
    """
    Get the recommended action from CPIC guidelines

    Args:
        drug_name: Name of drug
        phenotype: Phenotype classification

    Returns:
        Action string or None if not found
    """
    return get_cpic_action(drug_name, phenotype)


def get_dosing(drug_name: str, phenotype: str) -> Optional[str]:
    """
    Get dosing recommendations from CPIC guidelines

    Args:
        drug_name: Name of drug
        phenotype: Phenotype classification

    Returns:
        Dosing string or None if not found
    """
    return get_cpic_dosing(drug_name, phenotype)


def get_monitoring(drug_name: str, phenotype: str) -> Optional[str]:
    """
    Get monitoring recommendations from CPIC guidelines

    Args:
        drug_name: Name of drug
        phenotype: Phenotype classification

    Returns:
        Monitoring string or None if not found
    """
    return get_cpic_monitoring(drug_name, phenotype)


def format_recommendation_for_clinical_use(drug_name: str, phenotype: str, risk_label: str) -> str:
    """
    Format CPIC recommendation as a clinical summary

    Args:
        drug_name: Drug name
        phenotype: Phenotype
        risk_label: Risk label (Safe, Adjust Dosage, Toxic, etc.)

    Returns:
        Formatted clinical recommendation string
    """
    rec = get_recommendation(drug_name, phenotype)

    if rec.get('error'):
        return f"Standard dosing and monitoring recommended for {drug_name}."

    action = rec.get('action', '')
    dosing = rec.get('dosing', '')
    monitoring = rec.get('monitoring', '')

    clinical_summary = f"Clinical Recommendation ({risk_label}): {action}. "

    if dosing:
        clinical_summary += f"Dosing: {dosing}. "

    if monitoring:
        clinical_summary += f"Monitoring: {monitoring}"

    return clinical_summary


def get_all_recommendations_for_drugs(drugs: list, phenotype_map: Dict) -> Dict:
    """
    Get CPIC recommendations for multiple drugs and their phenotypes

    Args:
        drugs: List of drug names
        phenotype_map: Dictionary mapping drug names to phenotypes

    Returns:
        Dictionary of recommendations for each drug
    """
    recommendations = {}

    for drug in drugs:
        phenotype = phenotype_map.get(drug, 'Unknown')
        rec = get_recommendation(drug, phenotype)
        recommendations[drug] = rec

    return recommendations


def prioritize_recommendations_by_risk(recommendations: Dict) -> list:
    """
    Prioritize recommendations by clinical urgency

    Args:
        recommendations: Dictionary from get_all_recommendations_for_drugs

    Returns:
        Sorted list of recommendations by clinical priority
    """
    priority_order = {
        'Standard dosing': 0,
        'Monitor': 1,
        'Reduce dose': 2,
        'Increase dose': 3,
        'Use alternative': 4,
        'Contraindicated': 5
    }

    sorted_recs = []

    for drug, rec in recommendations.items():
        action = rec.get('action', '')
        priority = priority_order.get(action, 0)
        sorted_recs.append((drug, rec, priority))

    # Sort by priority (higher = more important)
    sorted_recs.sort(key=lambda x: x[2], reverse=True)

    return [(item[0], item[1]) for item in sorted_recs]
