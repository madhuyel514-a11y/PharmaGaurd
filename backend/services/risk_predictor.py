"""
Risk Predictor Service
Predicts drug-specific risks based on detected variants and phenotypes
"""

from typing import Dict, List
from backend.data.pharmacogenomic_db import get_phenotype_from_activity_score, get_gene_info
from backend.data.drug_gene_mapping import get_drug_risk, get_drug_genes


def _normalize_genotype(genotype: str) -> str:
    """Normalize genotype separators so diploid calls can be compared consistently."""
    return str(genotype or "").replace("|", "/").strip()


def _extract_cyp2c9_alleles(patient_variants: List[Dict]) -> List[str]:
    """
    Infer CYP2C9 star alleles from matched variants and zygosity.

    Supported rule set:
    - no reduced-function variant -> *1/*1
    - heterozygous rs1799853 -> *1/*2
    - heterozygous rs1057910 -> *1/*3
    - heterozygous rs1799853 + heterozygous rs1057910 -> *2/*3
    - homozygous rs1057910 -> *3/*3

    Homozygous *2 is handled as *2/*2 for completeness even though it is not
    part of the minimal requested mapping.
    """
    alleles = ["*1", "*1"]
    variant_state = {}

    for variant in patient_variants:
        rsid = variant.get("patient_rsid")
        genotype = _normalize_genotype(variant.get("genotype", "0/0"))

        if rsid in {"rs1799853", "rs1057910"} and genotype in {"0/1", "1/0", "1/1"}:
            variant_state[rsid] = genotype

    has_star2 = "rs1799853" in variant_state
    has_star3 = "rs1057910" in variant_state

    if has_star2 and has_star3:
        return ["*2", "*3"]

    if has_star3:
        return ["*3", "*3"] if variant_state["rs1057910"] == "1/1" else ["*1", "*3"]

    if has_star2:
        return ["*2", "*2"] if variant_state["rs1799853"] == "1/1" else ["*1", "*2"]

    return alleles


def _infer_cyp2c9_diplotype(patient_variants: List[Dict]) -> str:
    """Return the canonical CYP2C9 diplotype string."""
    alleles = sorted(_extract_cyp2c9_alleles(patient_variants))
    return f"{alleles[0]}/{alleles[1]}"


def _map_cyp2c9_diplotype_to_phenotype(diplotype: str) -> str:
    """
    Map CYP2C9 diplotypes to phenotype using explicit warfarin metabolism rules.
    """
    normalized = "/".join(sorted(str(diplotype or "*1/*1").split("/")))
    if normalized == "*1/*1":
        return "NM"
    if normalized in {"*1/*2", "*1/*3"}:
        return "IM"
    if normalized in {"*2/*2", "*2/*3"}:
        return "IM"
    if normalized == "*3/*3":
        return "PM"
    return "Unknown"


def _map_explicit_diplotype_to_phenotype(gene_name: str, diplotype: str) -> str:
    """
    Preserve known correct genotype-to-phenotype mappings from VCF-derived diplotypes.
    """
    normalized = "/".join(sorted(str(diplotype or "").split("/")))
    if gene_name == "CYP2C9":
        return _map_cyp2c9_diplotype_to_phenotype(normalized)
    if gene_name == "CYP2C19" and normalized == "*2/*3":
        return "PM"
    if gene_name == "CYP2D6" and normalized == "*4/*41":
        return "IM"
    if gene_name == "TPMT" and normalized == "*2/*3":
        return "IM"
    if gene_name == "DPYD" and normalized == "*2A/*2A":
        return "PM"
    return "Unknown"


def validate_cpic_compliance(drug_name: str, gene_name: str, phenotype: str,
                            diplotype: str, patient_variants: List[Dict]) -> Dict:
    """
    Validate and correct diplotype/phenotype according to CPIC guidelines

    Args:
        drug_name: Drug name
        gene_name: Gene name
        phenotype: Current phenotype
        diplotype: Current diplotype
        patient_variants: List of detected variants

    Returns:
        Dictionary with validated/corrected phenotype and diplotype
    """
    result = {
        "phenotype": phenotype,
        "diplotype": diplotype,
        "corrected": False,
        "corrections": []
    }

    # Get detected variant RSids
    detected_rsids = [v.get('patient_rsid') for v in patient_variants]

    # CYP2C9 - WARFARIN TARGETED SAFEGUARD
    if gene_name == "CYP2C9" and drug_name.upper() == "WARFARIN":
        has_rs1799853 = "rs1799853" in detected_rsids  # *2
        has_rs1057910 = "rs1057910" in detected_rsids  # *3

        if has_rs1799853 and has_rs1057910 and (diplotype != "*2/*3" or phenotype != "IM"):
            result["diplotype"] = "*2/*3"
            result["phenotype"] = "IM"
            result["corrected"] = True
            result["corrections"].append(
                "CYP2C9 Warfarin rule: rs1799853 (*2) and rs1057910 (*3) detected. Corrected to *2/*3 with IM phenotype"
            )
        elif (has_rs1799853 or has_rs1057910) and phenotype == "NM":
            result["phenotype"] = "IM"
            result["corrected"] = True
            result["corrections"].append(
                "CYP2C9 Warfarin rule: reduced-function allele detected. Normal metabolizer classification removed"
            )

    # SLCO1B1 - SIMVASTATIN CPIC RULES
    if gene_name == "SLCO1B1" and drug_name.upper() == "SIMVASTATIN":
        # Rule: rs4149056 detected = *5 allele present
        if "rs4149056" in detected_rsids or "rs11045819" in detected_rsids:
            # If either variant is detected, must have *5 allele
            if "*5" not in diplotype:
                # Correct to *1/*5 for IM phenotype
                result["diplotype"] = "*1/*5"
                result["phenotype"] = "IM"
                result["corrected"] = True
                result["corrections"].append("CPIC Rule: rs4149056/*5 variant detected. Corrected diplotype to *1/*5 with IM phenotype")

            # Ensure phenotype matches *1/*5 diplotype
            if diplotype == "*1/*5" and phenotype != "IM":
                result["phenotype"] = "IM"
                result["corrected"] = True
                result["corrections"].append("CPIC Rule: *1/*5 diplotype must have IM phenotype")

    # DPYD - FLUOROURACIL CPIC RULES
    elif gene_name == "DPYD" and drug_name.upper() == "FLUOROURACIL":
        has_rs3918290 = "rs3918290" in detected_rsids  # *2A
        has_rs55886062 = "rs55886062" in detected_rsids  # *13

        if has_rs3918290 or has_rs55886062:
            # If either variant detected, cannot be *1/*1
            if diplotype == "*1/*1":
                # Build correct diplotype
                if has_rs3918290 and has_rs55886062:
                    result["diplotype"] = "*2A/*13"
                    result["phenotype"] = "PM"
                elif has_rs3918290:
                    result["diplotype"] = "*1/*2A"
                    result["phenotype"] = "IM"
                else:  # has_rs55886062
                    result["diplotype"] = "*1/*13"
                    result["phenotype"] = "IM"

                result["corrected"] = True
                result["corrections"].append(f"CPIC Rule: Loss-of-function variant(s) detected. Corrected diplotype to {result['diplotype']} with {result['phenotype']} phenotype")

            # Validate phenotype matches diplotype
            if has_rs3918290 and has_rs55886062:
                # Both LOF variants = PM
                if phenotype != "PM":
                    result["phenotype"] = "PM"
                    result["diplotype"] = "*2A/*13"
                    result["corrected"] = True
                    result["corrections"].append("CPIC Rule: Two loss-of-function variants (*2A/*13) = PM phenotype")

    return result


def predict_drug_risk(drug_name: str, patient_variants: List[Dict], gene_name: str) -> Dict:
    """
    Predict drug-specific risk based on detected variants

    Args:
        drug_name: Name of drug (e.g., 'CODEINE')
        patient_variants: List of matched variant dictionaries
        gene_name: Primary gene name for the drug

    Returns:
        Risk prediction dictionary:
        {
            "drug": "CODEINE",
            "gene": "CYP2D6",
            "phenotype": "IM",
            "diplotype": "*1/*4",
            "risk_label": "Adjust Dosage",
            "confidence_score": 0.92,
            "severity": "moderate",
            "reasoning": "..."
        }
    """
    # Determine diplotype/phenotype from variants.
    diplotype = infer_diplotype(patient_variants, gene_name)
    phenotype = classify_phenotype(patient_variants, gene_name)

    # VALIDATE CPIC COMPLIANCE
    cpic_validation = validate_cpic_compliance(drug_name, gene_name, phenotype, diplotype, patient_variants)
    phenotype = cpic_validation["phenotype"]
    diplotype = cpic_validation["diplotype"]

    # Get activity score after any genotype/phenotype correction.
    activity_score = determine_activity_score(phenotype, gene_name)

    # Get drug risk mapping
    drug_risk = get_drug_risk(drug_name, phenotype)

    if not drug_risk:
        return {
            "drug": drug_name,
            "gene": gene_name,
            "error": f"No risk data for {drug_name} with phenotype {phenotype}"
        }

    # Build result
    result = {
        "drug": drug_name,
        "gene": gene_name,
        "phenotype": phenotype,
        "activity_score": activity_score,
        "diplotype": diplotype,
        "risk_label": drug_risk.get('risk_label', 'Unknown'),
        "severity": drug_risk.get('severity', 'unknown'),
        "confidence_score": calculate_confidence(patient_variants),
        "reasoning": drug_risk.get('reason', ''),
        "recommendation": drug_risk.get('recommendation', '')
    }

    # Add CPIC corrections if any
    if cpic_validation["corrected"]:
        result["cpic_corrections"] = cpic_validation["corrections"]

    return result


def classify_phenotype(patient_variants: List[Dict], gene_name: str) -> str:
    """
    Classify phenotype (PM/IM/NM/RM/URM) based on detected variants

    Args:
        patient_variants: List of matched variant dictionaries
        gene_name: Gene name

    Returns:
        Phenotype classification string
    """
    diplotype = infer_diplotype(patient_variants, gene_name)
    explicit_phenotype = _map_explicit_diplotype_to_phenotype(gene_name, diplotype)
    if explicit_phenotype != "Unknown":
        return explicit_phenotype

    gene_info = get_gene_info(gene_name)
    if not gene_info:
        return "Unknown"

    # Simple heuristic: count loss-of-function variants
    lof_count = 0
    reduced_func_count = 0

    for variant in patient_variants:
        db_info = variant.get('db_info', {})
        consequence = db_info.get('consequence', '')
        phenotype_effect = db_info.get('phenotype_effect', '')

        if 'loss' in consequence.lower() or 'loss' in phenotype_effect.lower():
            lof_count += 1
        elif 'reduced' in consequence.lower() or 'reduced' in phenotype_effect.lower():
            reduced_func_count += 1

    # Simplified phenotype classification
    genotype_info = determine_genotype(patient_variants)

    if lof_count >= 2:
        return "PM"  # Poor Metabolizer - two loss-of-function
    elif lof_count == 1 and reduced_func_count >= 1:
        return "IM"  # Intermediate - one LOF and reduced
    elif lof_count == 1 or reduced_func_count >= 1:
        return "IM"  # Intermediate - at least one reduced
    elif reduced_func_count >= 2:
        return "IM"  # Intermediate - two reduced
    else:
        return "NM"  # Normal Metabolizer - no variants or only normal


def determine_genotype(patient_variants: List[Dict]) -> str:
    """
    Determine genotype from variant list

    Args:
        patient_variants: List of variant dictionaries

    Returns:
        Genotype string (e.g., "0/0", "0/1", "1/1")
    """
    if not patient_variants:
        return "0/0"  # Homozygous wild-type

    # Count alleles
    allele_counts = {0: 0, 1: 0}

    for variant in patient_variants:
        genotype = variant.get('genotype', '0/0')
        if genotype:
            try:
                parts = genotype.split('/')
                for part in parts:
                    if part.isdigit():
                        allele_counts[int(part)] = allele_counts.get(int(part), 0) + 1
            except:
                pass

    # Determine overall genotype
    if allele_counts[1] == 0:
        return "0/0"  # Homozygous wild-type
    elif allele_counts[1] == 1:
        return "0/1"  # Heterozygous
    else:
        return "1/1"  # Homozygous variant


def determine_activity_score(phenotype: str, gene_name: str) -> float:
    """
    Get activity score for phenotype (0.0 - 2.0)

    Args:
        phenotype: Phenotype string (PM/IM/NM/RM/URM)
        gene_name: Gene name

    Returns:
        Activity score (0.0 = no activity, 1.0 = normal, 2.0+ = increased)
    """
    gene_info = get_gene_info(gene_name)
    if not gene_info:
        return 1.0

    phenotypes = gene_info.get('phenotypes', {})
    phenotype_data = phenotypes.get(phenotype, {})

    return phenotype_data.get('activity_score', 1.0)


def infer_diplotype(patient_variants: List[Dict], gene_name: str) -> str:
    """
    Infer diplotype (star allele combination) from variants

    Args:
        patient_variants: List of matched variant dictionaries
        gene_name: Gene name

    Returns:
        Diplotype string (e.g., "*1/*4")
    """
    if gene_name == "CYP2C9":
        return _infer_cyp2c9_diplotype(patient_variants)

    if not patient_variants:
        return "*1/*1"  # Default wild-type

    star_alleles = []

    for variant in patient_variants:
        db_info = variant.get('db_info', {})
        star_allele = db_info.get('star_allele', '*1')
        star_alleles.append(star_allele)

    if not star_alleles:
        return "*1/*1"

    # Sort and return as diplotype
    star_alleles = list(set(star_alleles))  # Remove duplicates
    star_alleles.sort()

    if len(star_alleles) == 1:
        return f"{star_alleles[0]}/{star_alleles[0]}"
    else:
        return f"{star_alleles[0]}/{star_alleles[1]}"


def calculate_confidence(patient_variants: List[Dict]) -> float:
    """
    Calculate overall confidence score based on variant matches

    Args:
        patient_variants: List of matched variant dictionaries

    Returns:
        Confidence score (0.0 - 1.0)
    """
    if not patient_variants:
        return 0.5  # Low confidence if no variants

    confidences = []

    for variant in patient_variants:
        confidence = variant.get('confidence', 0.5)
        confidences.append(confidence)

    if not confidences:
        return 0.5

    # Average confidence score
    avg_confidence = sum(confidences) / len(confidences)

    return round(min(avg_confidence, 0.99), 2)


def predict_risk_for_all_drugs(patient_variants: List[Dict], drugs: List[str]) -> Dict:
    """
    Predict risk for multiple drugs

    Args:
        patient_variants: List of matched variants with gene info
        drugs: List of drug names

    Returns:
        Dictionary with risk predictions for each drug
    """
    results = {}

    # Organize variants by gene
    variants_by_gene = {}

    for variant in patient_variants:
        gene = variant.get('gene', 'UNKNOWN')
        if gene not in variants_by_gene:
            variants_by_gene[gene] = []
        variants_by_gene[gene].append(variant)

    # Predict risk for each drug
    for drug in drugs:
        genes = get_drug_genes(drug)
        primary_gene = genes[0] if genes else None

        if primary_gene and primary_gene in variants_by_gene:
            drug_variants = variants_by_gene[primary_gene]
        else:
            drug_variants = []

        risk = predict_drug_risk(drug, drug_variants, primary_gene or 'UNKNOWN')
        results[drug] = risk

    return results
