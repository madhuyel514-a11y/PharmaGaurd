"""
Variant Matcher Service
Matches patient variants to pharmacogenomic database variants
"""

from typing import Dict, List, Tuple
from backend.data.pharmacogenomic_db import get_gene_info, get_variant_info, get_all_genes


def match_variants_to_db(patient_variants: List[Dict], gene_name: str) -> Dict:
    """
    Match patient variants to pharmacogenomic database

    Args:
        patient_variants: List of patient variant dictionaries
        gene_name: Target gene name (e.g., 'CYP2D6')

    Returns:
        Dictionary with:
        {
            "gene": "CYP2D6",
            "matched_variants": [
                {
                    "patient_rsid": "rs1065852",
                    "db_info": {...},
                    "confidence": 0.95
                }
            ],
            "unmatched_rsids": ["rs99999"],
            "match_confidence": 0.92
        }
    """
    result = {
        "gene": gene_name,
        "matched_variants": [],
        "unmatched_rsids": [],
        "match_confidence": 0.0
    }

    gene_info = get_gene_info(gene_name)
    if not gene_info:
        result["error"] = f"Gene {gene_name} not found in database"
        return result

    matched_count = 0
    total_count = 0

    for variant in patient_variants:
        rsid = variant.get('rsid')
        if not rsid:
            continue

        total_count += 1

        # Try to match by RSid
        variant_info = get_variant_info(gene_name, rsid)

        if variant_info:
            confidence = calculate_match_score(rsid, variant_info)
            result['matched_variants'].append({
                "patient_rsid": rsid,
                "chromosome": variant.get('chromosome'),
                "position": variant.get('position'),
                "ref": variant.get('ref'),
                "alt": variant.get('alt'),
                "genotype": variant.get('genotype'),
                "db_info": variant_info,
                "confidence": confidence
            })
            matched_count += 1
        else:
            result['unmatched_rsids'].append(rsid)

    # Calculate overall match confidence
    if total_count > 0:
        result['match_confidence'] = round(matched_count / total_count, 2)
    else:
        result['match_confidence'] = 1.0  # Perfect match if no variants

    return result


def get_variant_annotations(rsid: str, gene: str) -> Dict:
    """
    Get functional annotation for variant from database

    Args:
        rsid: RS ID of variant
        gene: Gene name

    Returns:
        Variant annotation dictionary
    """
    variant_info = get_variant_info(gene, rsid)

    if not variant_info:
        return {
            "error": f"Variant {rsid} not found for gene {gene}",
            "rsid": rsid,
            "gene": gene
        }

    return {
        "rsid": rsid,
        "gene": gene,
        "star_allele": variant_info.get('star_allele'),
        "consequence": variant_info.get('consequence'),
        "phenotype_effect": variant_info.get('phenotype_effect'),
        "functional_status": variant_info.get('functional_status'),
        "evidence_level": variant_info.get('evidence_level')
    }


def calculate_match_score(patient_rsid: str, db_variant: Dict) -> float:
    """
    Calculate confidence score for variant match

    Args:
        patient_rsid: Patient's RS ID
        db_variant: Database variant entry

    Returns:
        Confidence score (0.0 - 1.0)
    """
    # Start with base confidence based on evidence level
    evidence = db_variant.get('evidence_level', 'C')

    base_confidence = {
        'A': 0.95,  # Strong evidence
        'B': 0.85,  # Moderate evidence
        'C': 0.70,  # Limited evidence
    }.get(evidence, 0.5)

    # Adjust based on functional status
    functional = db_variant.get('functional_status', 'Unknown')

    functional_confidence = {
        'Non-functional': 0.98,
        'Decreased': 0.90,
        'Increased': 0.88,
        'Unknown': 0.70,
    }.get(functional, 0.70)

    # Combine scores
    combined = (base_confidence + functional_confidence) / 2

    return round(min(combined, 0.99), 2)


def match_all_target_genes(patient_variants: List[Dict], target_genes: List[str]) -> Dict:
    """
    Match variants against all target genes

    Args:
        patient_variants: List of patient variants
        target_genes: List of genes to check (e.g., ['CYP2D6', 'CYP2C19'])

    Returns:
        Dictionary of gene matches
    """
    results = {}

    for gene in target_genes:
        results[gene] = match_variants_to_db(patient_variants, gene)

    return results


def get_matched_rsids(gene_matches: Dict) -> List[str]:
    """
    Extract all successfully matched RS IDs from gene match results

    Args:
        gene_matches: Output from match_variants_to_db() call

    Returns:
        List of matched RS IDs
    """
    rsids = []
    for variant in gene_matches.get('matched_variants', []):
        rsid = variant.get('patient_rsid')
        if rsid:
            rsids.append(rsid)
    return rsids
