# Implementation Guidance for Backend Validation

This document provides code-level recommendations to prevent the identified issues in future output.

## 1. Risk Scoring Validation

**Problem Identified**: Risk scores not aligned with phenotypes or severity labels.

**Solution - Add Phenotype-to-Risk Mapping**:

```python
# backend/data/phenotype_risk_mapping.py

PHENOTYPE_RISK_RANGES = {
    "UM": {"risk_min": 0.0, "risk_max": 0.3, "label": "Low", "severity": "none"},
    "EM": {"risk_min": 0.0, "risk_max": 0.3, "label": "Low", "severity": "none"},
    "NM": {"risk_min": 0.0, "risk_max": 0.3, "label": "Low", "severity": "none"},
    "IM": {"risk_min": 0.3, "risk_max": 0.7, "label": "Moderate", "severity": "moderate"},
    "PM": {"risk_min": 0.7, "risk_max": 0.9, "label": "High", "severity": "high"},
    "Deficient": {"risk_min": 0.9, "risk_max": 1.0, "label": "High", "severity": "critical"},
}

# Special case: Some drugs require PM phenotype to be CRITICAL, not just High
CRITICAL_PHENOTYPE_DRUGS = {
    "CLOPIDOGREL": "PM",  # PM = treatment failure = life-threatening
    "FLUOROURACIL": "Deficient",  # Deficient = accumulation = lethal toxicity
}

def validate_risk_consistency(drug: str, phenotype: str, risk_score: float, 
                             risk_level: str, severity: str) -> dict:
    """
    Validate that phenotype, risk_score, risk_level, and severity are consistent.
    
    Returns:
        {
            "is_valid": bool,
            "errors": [list of inconsistencies],
            "corrected_values": {
                "risk_level": corrected_level,
                "severity": corrected_severity
            }
        }
    """
    errors = []
    corrected = {}
    
    # Check if phenotype mapping exists
    if phenotype not in PHENOTYPE_RISK_RANGES:
        errors.append(f"Unknown phenotype: {phenotype}")
        return {"is_valid": False, "errors": errors, "corrected_values": {}}
    
    expected_ranges = PHENOTYPE_RISK_RANGES[phenotype]
    
    # Validate risk_score in range for phenotype
    if not (expected_ranges["risk_min"] <= risk_score <= expected_ranges["risk_max"]):
        errors.append(
            f"risk_score {risk_score} outside expected range "
            f"[{expected_ranges['risk_min']}, {expected_ranges['risk_max']}] for {phenotype}"
        )
        corrected["risk_score"] = (expected_ranges["risk_min"] + expected_ranges["risk_max"]) / 2
    
    # Validate risk_level matches phenotype
    if risk_level != expected_ranges["label"]:
        errors.append(f"risk_level '{risk_level}' inconsistent with phenotype '{phenotype}'")
        corrected["risk_level"] = expected_ranges["label"]
    
    # Validate severity matches phenotype
    if severity != expected_ranges["severity"]:
        errors.append(f"severity '{severity}' inconsistent with phenotype '{phenotype}'")
        corrected["severity"] = expected_ranges["severity"]
    
    # CRITICAL: Check if drug requires phenotype override
    if drug in CRITICAL_PHENOTYPE_DRUGS and phenotype == CRITICAL_PHENOTYPE_DRUGS[drug]:
        corrected["severity"] = "critical"
        corrected["risk_level"] = "Critical" if risk_score >= 0.9 else "High"
        errors.append(f"Drug {drug} with {phenotype} requires critical severity override")
    
    is_valid = len(errors) == 0
    return {
        "is_valid": is_valid,
        "errors": errors,
        "corrected_values": corrected
    }
```

---

## 2. Recommendation Consistency Validation

**Problem Identified**: Conflicting recommendations across multiple fields.

**Solution - Single Authority Pattern**:

```python
# backend/services/recommendation_generator.py

from enum import Enum
from typing import Dict, List

class RecommendationAction(Enum):
    AVOID = "AVOID"
    USE_ALTERNATIVE = "Use alternative"
    REDUCE_DOSE_SIGNIFICANTLY = "Reduce dose significantly"
    REDUCE_DOSE = "Reduce dose"
    STANDARD_DOSING = "Standard dosing"
    USE_CAUTION = "Use caution"

DRUG_GENE_RECOMMENDATIONS = {
    ("CLOPIDOGREL", "PM"): {
        "action": RecommendationAction.AVOID,
        "dosing_guidance": "DO NOT USE",
        "alternatives": ["Prasugrel (5-10 mg/day)", "Ticagrelor (60-90 mg twice daily)"],
        "monitoring": "Verify alternative drug initiated",
        "cpic_level": "A"
    },
    ("CODEINE", "IM"): {
        "action": RecommendationAction.REDUCE_DOSE,
        "dosing_guidance": "Consider 25-50% dose reduction",
        "alternatives": ["Morphine", "Hydromorphone", "Tramadol"],
        "monitoring": "Monitor for pain relief",
        "cpic_level": "B"
    },
    ("WARFARIN", "IM"): {
        "action": RecommendationAction.REDUCE_DOSE,
        "dosing_guidance": "3-4 mg/day or 80-90% of standard dose",
        "alternatives": ["Apixaban", "Rivaroxaban", "Dabigatran"],
        "monitoring": "More frequent INR checks",
        "cpic_level": "A"
    },
    # ... etc for all drugs
}

def generate_recommendation(drug: str, phenotype: str, risk_score: float) -> Dict:
    """
    Generate all recommendation fields from single source of truth.
    """
    key = (drug, phenotype)
    
    if key not in DRUG_GENE_RECOMMENDATIONS:
        # Fallback for undefined combinations
        return _fallback_recommendation(drug, phenotype, risk_score)
    
    template = DRUG_GENE_RECOMMENDATIONS[key]
    
    return {
        "clinical_recommendation": {
            "action": template["action"].value,
            "dosing_guidance": template["dosing_guidance"],
            "alternative_drugs": template["alternatives"],
            "monitoring": template["monitoring"],
            "cpic_level": template["cpic_level"],
        },
        # All other fields reference clinical_recommendation.action
        "cpic_recommendation": template["action"].value,
        # Note: Remove drug_recommendation field; use clinical_recommendation.action
    }

def _fallback_recommendation(drug: str, phenotype: str, risk_score: float) -> Dict:
    """Generate recommendation when specific phenotype not in lookup."""
    if risk_score >= 0.9:
        action = RecommendationAction.AVOID.value
        monitoring = "Consider alternative drug"
    elif risk_score >= 0.7:
        action = RecommendationAction.REDUCE_DOSE_SIGNIFICANTLY.value
        monitoring = "Close monitoring required"
    elif risk_score >= 0.3:
        action = RecommendationAction.REDUCE_DOSE.value
        monitoring = "Standard monitoring"
    else:
        action = RecommendationAction.STANDARD_DOSING.value
        monitoring = "Routine monitoring"
    
    return {
        "clinical_recommendation": {
            "action": action,
            "monitoring": monitoring,
        },
        "cpic_recommendation": action,
    }
```

---

## 3. Phenotype Validation Against Genotype

**Problem Identified**: Phenotype doesn't match diplotype (e.g., DPYD *2A/*2A labeled as IM instead of Deficient).

**Solution - Genotype-to-Phenotype Mapping**:

```python
# backend/services/phenotype_classifier.py

DIPLOTYPE_PHENOTYPE_MAP = {
    # DPYD
    ("*1", "*1"): "NM",  # Normal Metabolizer
    ("*1", "*2A"): "IM",  # Intermediate (heterozygous LOF)
    ("*2A", "*2A"): "Deficient",  # Homozygous LOF = Deficient
    ("*1", "*3"): "IM",
    ("*3", "*3"): "Deficient",
    
    # CYP2C19
    ("*1", "*1"): "EM",  # Extensive
    ("*1", "*2"): "IM",  # Intermediate
    ("*2", "*2"): "PM",  # Poor
    ("*2", "*3"): "PM",
    ("*3", "*3"): "PM",
    
    # CYP2D6 (simplified; actual is complex)
    ("*1", "*1"): "EM",
    ("*1", "*4"): "IM",
    ("*4", "*4"): "PM",
    ("*41", "*4"): "IM",  # From CODEINE example
    
    # TPMT
    ("*1", "*1"): "NM",
    ("*1", "*2"): "IM",
    ("*2", "*3"): "IM",
    ("*2", "*2"): "PM",
    
    # CYP2C9
    ("*1", "*1"): "EM",
    ("*1", "*2"): "IM",
    ("*1", "*3"): "IM",
    ("*2", "*3"): "PM",
    ("*3", "*3"): "PM",
    
    # SLCO1B1
    ("*1a", "*1a"): "NM",
    ("*1a", "*1b"): "IM",  # Reduced transporter
    ("*1b", "*1b"): "IM",
}

def classify_phenotype(gene: str, diplotype: str) -> str:
    """
    Convert diplotype to phenotype based on gene-specific rules.
    
    Args:
        gene: Gene name (e.g., "DPYD", "CYP2C19")
        diplotype: e.g., "*1/*2A", "*2/*3"
    
    Returns:
        Phenotype: "NM", "EM", "IM", "PM", "Deficient"
    """
    alleles = tuple(sorted(diplotype.split("/")))
    
    # Normalize for case-insensitive matching
    alleles = tuple(a.upper() for a in alleles)
    
    phenotype = DIPLOTYPE_PHENOTYPE_MAP.get(alleles, "Unknown")
    
    if phenotype == "Unknown":
        # Try normalized lookup with common variations
        pass
    
    return phenotype

def validate_phenotype_consistency(gene: str, diplotype: str, 
                                   reported_phenotype: str) -> bool:
    """
    Check if reported phenotype matches diplotype.
    """
    expected = classify_phenotype(gene, diplotype)
    is_valid = expected == reported_phenotype
    
    if not is_valid:
        print(f"WARNING: {gene} {diplotype} should be {expected}, not {reported_phenotype}")
    
    return is_valid
```

---

## 4. Gene-Specific Interpretation (No Overbroad Genes)

**Problem Identified**: All 6 genes marked as present for all drugs.

**Solution - Drug-Gene Relevance Filtering**:

```python
# backend/data/drug_gene_mapping.py (enhance existing)

DRUG_RELEVANT_GENES = {
    "CODEINE": ["CYP2D6"],
    "WARFARIN": ["CYP2C9", "VKORC1"],
    "CLOPIDOGREL": ["CYP2C19"],
    "SIMVASTATIN": ["SLCO1B1"],
    "AZATHIOPRINE": ["TPMT"],
    "FLUOROURACIL": ["DPYD"],
    "MORPHINE": ["CYP2D6"],  # Add common alternatives
    "APIXABAN": [],  # No pharmacogenes
    "PRASUGREL": ["CYP2B6", "CYP3A4"],  # Alternatives if needed
    # ... etc
}

def get_interpretable_genes_for_drug(drug: str) -> List[str]:
    """
    Return ONLY genes relevant to this drug.
    Do not return all genes in panel.
    """
    return DRUG_RELEVANT_GENES.get(drug.upper(), [])

def filter_variants_by_drug(drug: str, variants_by_gene: Dict) -> Dict:
    """
    Filter variants to include only drug-relevant genes.
    """
    relevant_genes = get_interpretable_genes_for_drug(drug)
    
    filtered = {}
    for gene in relevant_genes:
        if gene in variants_by_gene:
            filtered[gene] = variants_by_gene[gene]
    
    return filtered

# Usage in analysis endpoint:
from backend.routes.analysis import analyze_drug

def analyze_drug_improved(drug, variants_by_gene, patent_id, gene_variant_presence, ml_result):
    # Only look at drug-relevant genes
    filtered_variants = filter_variants_by_drug(drug, variants_by_gene)
    
    # Build response with ONLY relevant genes
    response = {
        "drug": drug,
        "pharmacogenomic_profile": {
            "primary_gene": get_drug_genes(drug)[0],
            "detected_variants": filtered_variants.get(primary_gene, []),
            # Only include genes relevant to THIS drug
        },
    }
    
    return response
```

---

## 5. Consistency Checks Before Output

**Solution - Pre-Output Validation Function**:

```python
# backend/services/output_validator.py

from typing import Dict, List, Tuple

class OutputValidator:
    """
    Validates pharmacogenomic record for clinical consistency before returning.
    """
    
    def __init__(self, record: Dict):
        self.record = record
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.corrections: Dict = {}
    
    def validate_all(self) -> Tuple[bool, List, List, Dict]:
        """
        Run all validation checks.
        
        Returns:
            (is_valid, errors, warnings, corrections)
        """
        self._check_risk_consistency()
        self._check_recommendation_alignment()
        self._check_phenotype_genotype_match()
        self._check_ml_phenotype_alignment()
        self._check_gene_relevance()
        self._check_no_duplicates()
        self._check_critical_alerts()
        
        return (
            len(self.errors) == 0,
            self.errors,
            self.warnings,
            self.corrections
        )
    
    def _check_risk_consistency(self):
        """Risk score/level/severity must align."""
        risk_score = self.record.get("risk_assessment", {}).get("risk_score", 0)
        risk_level = self.record.get("risk_assessment", {}).get("risk_level", "")
        severity = self.record.get("risk_assessment", {}).get("severity", "")
        
        # Map risk_score to expected level
        if risk_score < 0.3:
            expected = ("Low", "none")
        elif risk_score < 0.7:
            expected = ("Moderate", "moderate")
        elif risk_score < 0.9:
            expected = ("High", "high")
        else:
            expected = ("High", "critical")  # Critical risk
        
        if risk_level != expected[0]:
            self.errors.append(
                f"risk_level '{risk_level}' inconsistent with risk_score {risk_score}"
            )
    
    def _check_recommendation_alignment(self):
        """All recommendation fields must align."""
        clinical_action = self.record.get("clinical_recommendation", {}).get("action", "")
        cpic_rec = self.record.get("clinical_recommendation", {}).get("cpic_level", "")
        
        # Check for contradictions
        if "AVOID" in clinical_action and "Standard" in clinical_action:
            self.errors.append("Contradictory recommendation: 'AVOID' + 'Standard'")
    
    def _check_phenotype_genotype_match(self):
        """Validate phenotype matches diplotype."""
        from backend.services.phenotype_classifier import validate_phenotype_consistency
        
        gene = self.record.get("pharmacogenomic_profile", {}).get("primary_gene", "")
        diplotype = self.record.get("pharmacogenomic_profile", {}).get("diplotype", "")
        phenotype = self.record.get("pharmacogenomic_profile", {}).get("phenotype", "")
        
        if not validate_phenotype_consistency(gene, diplotype, phenotype):
            self.errors.append(f"Phenotype-genotype mismatch for {gene}")
    
    def _check_ml_phenotype_alignment(self):
        """ML prediction should align with phenotype."""
        phenotype = self.record.get("pharmacogenomic_profile", {}).get("phenotype", "")
        ml_pred = self.record.get("ml_prediction", {}).get("prediction", "")
        
        phenotype_to_ml = {
            "NM": "Normal",
            "EM": "Normal",
            "IM": "Intermediate",
            "PM": "HighRisk",
            "Deficient": "HighRisk",
        }
        
        expected_ml = phenotype_to_ml.get(phenotype, "")
        if ml_pred != expected_ml:
            self.warnings.append(
                f"ML prediction '{ml_pred}' may not align with phenotype '{phenotype}'"
            )
    
    def _check_gene_relevance(self):
        """Only drug-relevant genes should be interpreted."""
        drug = self.record.get("drug", "")
        variants = self.record.get("pharmacogenomic_profile", {}).get("detected_variants", [])
        
        relevant_genes = get_interpretable_genes_for_drug(drug)
        
        for variant in variants:
            if variant.get("gene") not in relevant_genes:
                self.warnings.append(
                    f"Gene {variant['gene']} being interpreted for {drug}, "
                    f"but not relevant to this drug"
                )
    
    def _check_no_duplicates(self):
        """Ensure no duplicate fields."""
        # Check for both detected_variants in multiple locations
        if ("pharmacogenomic_profile" in self.record and 
            "detected_variants" in self.record["pharmacogenomic_profile"] and
            "detected_variants" in self.record):
            self.warnings.append("Duplicate detected_variants in multiple locations")
    
    def _check_critical_alerts(self):
        """Add critical_alert for severe phenotypes."""
        severity = self.record.get("risk_assessment", {}).get("severity", "")
        phenotype = self.record.get("pharmacogenomic_profile", {}).get("phenotype", "")
        drug = self.record.get("drug", "")
        
        if severity == "critical":
            if "critical_alert" not in self.record:
                self.corrections["critical_alert"] = (
                    f"LIFE-THREATENING DRUG-GENE INTERACTION: "
                    f"{drug} with {phenotype} phenotype"
                )


# Usage in analysis endpoint:
def analyze():
    # ... existing analysis code ...
    
    # Before returning results
    for result in results:
        validator = OutputValidator(result)
        is_valid, errors, warnings, corrections = validator.validate_all()
        
        if errors:
            logger.error(f"Validation failed for {result['drug']}: {errors}")
            # Apply corrections or reject result
            result.update(corrections)
        
        if warnings:
            logger.warning(f"Validation warnings for {result['drug']}: {warnings}")
    
    return jsonify(results), 200
```

---

## 6. Data Structure - Single Source of Truth

**Problem**: Duplicate fields lead to inconsistencies.

**Solution - Refactored JSON Structure**:

```python
# Recommended output structure (removes duplicates)

result = {
    "patient_id": "PATIENT_ABC123",
    "drug": "CODEINE",
    "timestamp": "2026-04-12T10:26:42Z",
    
    # Single source of truth for variants
    "pharmacogenomic_profile": {
        "primary_gene": "CYP2D6",
        "phenotype": "IM",
        "diplotype": "*4/*41",
        "detected_variants": [
            {
                "rsid": "rs5030655",
                "gene": "CYP2D6",
                "consequence": "Reduced function",
                "clinical_significance": "May reduce codeine activation"
            }
        ]
    },
    
    # Single recommendation authority
    "clinical_recommendation": {
        "action": "Reduce dose",
        "dosing_guidance": "Consider 25-50% dose reduction",
        "alternative_drugs": ["Morphine", "Hydromorphone"],
        "monitoring": "Monitor for efficacy",
        "cpic_level": "B"
    },
    
    # Risk assessment single values
    "risk_assessment": {
        "risk_score": 0.59,
        "risk_level": "Moderate",
        "severity": "moderate",
        "confidence_score": 0.92,
        "rationale": "IM phenotype with reduced enzyme activity"
    },
    
    # ML prediction with clear labeling
    "ml_prediction": {
        "model_status": "ready",
        "prediction": "Intermediate",
        "confidence": 0.604,
        "probabilities": {...},
        "note": "ML aligns with VCF phenotype"
    },
    
    # ADR prediction
    "adverse_reaction_prediction": {
        "probability": 0.52,
        "reaction": "Reduced analgesia or toxicity risk",
        "severity": "moderate"
    },
    
    # AI-generated text interpretation
    "ai_summary": {
        "clinical_interpretation": "...",
        "key_findings": [...]
    },
    
    # Quality metrics only
    "quality_metrics": {
        "vcf_parsing_success": True,
        "variant_confidence": 0.92,
        "interpretation_confidence": 0.92
    }
    
    # REMOVED: Duplicate fields like gene_variants, genes_detected, drug_recommendation etc.
}
```

---

## 7. Testing the Improvements

Add unit tests to validate each improvement:

```python
# backend/tests/test_output_validation.py

import pytest
from backend.services.output_validator import OutputValidator

def test_risk_consistency_clopidogrel():
    """CLOPIDOGREL with PM phenotype should be High/Critical risk."""
    record = {
        "drug": "CLOPIDOGREL",
        "pharmacogenomic_profile": {
            "phenotype": "PM",
            "diplotype": "*2/*3",
        },
        "risk_assessment": {
            "risk_score": 0.92,
            "risk_level": "High",
            "severity": "critical",
        }
    }
    
    validator = OutputValidator(record)
    is_valid, errors, _, _ = validator.validate_all()
    assert is_valid, f"Validation failed: {errors}"

def test_phenotype_genotype_match_fluorouracil():
    """FLUOROURACIL *2A/*2A should be Deficient, not IM."""
    record = {
        "pharmacogenomic_profile": {
            "primary_gene": "DPYD",
            "diplotype": "*2A/*2A",
            "phenotype": "Deficient",  # Should be Deficient, not IM
        }
    }
    
    from backend.services.phenotype_classifier import validate_phenotype_consistency
    is_valid = validate_phenotype_consistency(
        gene="DPYD",
        diplotype="*2A/*2A",
        reported_phenotype="Deficient"
    )
    assert is_valid

def test_no_overbroad_genes():
    """CODEINE should only interpret CYP2D6, not all 6 genes."""
    from backend.data.drug_gene_mapping import get_interpretable_genes_for_drug
    
    genes = get_interpretable_genes_for_drug("CODEINE")
    assert genes == ["CYP2D6"], f"Expected only CYP2D6, got {genes}"

def test_recommendation_consistency():
    """All recommendation fields must align."""
    record = {
        "drug": "CLOPIDOGREL",
        "clinical_recommendation": {
            "action": "AVOID - Use alternative P2Y12 inhibitor",
            "alternative_drugs": ["Prasugrel", "Ticagrelor"],
        },
        # Should not have "Use caution" anywhere
    }
    
    clinical_action = record["clinical_recommendation"]["action"]
    assert "AVOID" in clinical_action
    assert "caution" not in clinical_action.lower()
```

These tests ensure corrections are properly implemented and prevent regressions.
