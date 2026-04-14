# Drug-to-Gene Mapping and Risk Assessment Rules
# This file maps each supported drug to the genes that affect its metabolism
# and defines the risk phenotype mapping

DRUG_GENE_MAPPING = {
    "CODEINE": {
        "primary_gene": "CYP2D6",
        "secondary_genes": [],
        "description": "Opioid pain medication - metabolism depends on CYP2D6 enzyme activity",
        "risk_phenotype_mapping": {
            "PM": {
                "risk_label": "Toxic",
                "severity": "critical",
                "confidence": 0.95,
                "reason": "Poor metabolizer - no conversion to active form",
                "recommendation": "Avoid use or use alternative opioid"
            },
            "IM": {
                "risk_label": "Adjust Dosage",
                "severity": "moderate",
                "confidence": 0.90,
                "reason": "Intermediate metabolizer - reduced analgesic effect",
                "recommendation": "Consider dose reduction and monitor closely"
            },
            "NM": {
                "risk_label": "Safe",
                "severity": "none",
                "confidence": 0.98,
                "reason": "Normal metabolizer - standard dosing appropriate",
                "recommendation": "Standard dosing"
            },
            "RM": {
                "risk_label": "Adjust Dosage",
                "severity": "moderate",
                "confidence": 0.85,
                "reason": "Rapid metabolizer - increased metabolism rate",
                "recommendation": "Consider dose increase and monitor"
            },
            "URM": {
                "risk_label": "Ineffective",
                "severity": "high",
                "confidence": 0.90,
                "reason": "Ultra-rapid metabolizer - very rapid metabolism",
                "recommendation": "Consider alternative medication"
            }
        }
    },
    "WARFARIN": {
        "primary_gene": "CYP2C9",
        "secondary_genes": ["VKORC1"],
        "description": "Anticoagulant - metabolism affected by CYP2C9 variants",
        "risk_phenotype_mapping": {
            "PM": {
                "risk_label": "Toxic",
                "severity": "critical",
                "confidence": 0.95,
                "reason": "Poor metabolizer - accumulation risk",
                "recommendation": "Significant dose reduction required with very low starting dose and frequent INR monitoring"
            },
            "IM": {
                "risk_label": "Adjust Dosage",
                "severity": "high",
                "confidence": 0.92,
                "reason": "Intermediate metabolizer - slower metabolism",
                "recommendation": "Dose reduction required with lower starting dose and frequent INR checks"
            },
            "NM": {
                "risk_label": "Safe",
                "severity": "none",
                "confidence": 0.98,
                "reason": "Normal metabolizer - standard dosing appropriate",
                "recommendation": "Standard dosing with routine INR monitoring"
            },
            "RM": {
                "risk_label": "Adjust Dosage",
                "severity": "moderate",
                "confidence": 0.88,
                "reason": "Rapid metabolizer - increased metabolism",
                "recommendation": "May require higher doses"
            },
            "URM": {
                "risk_label": "Ineffective",
                "severity": "high",
                "confidence": 0.85,
                "reason": "Ultra-rapid metabolizer - very rapid clearance",
                "recommendation": "High doses may be needed; close monitoring essential"
            }
        }
    },
    "CLOPIDOGREL": {
        "primary_gene": "CYP2C19",
        "secondary_genes": [],
        "description": "Antiplatelet medication - requires CYP2C19 activation",
        "risk_phenotype_mapping": {
            "PM": {
                "risk_label": "Ineffective",
                "severity": "critical",
                "confidence": 0.96,
                "reason": "Poor metabolizer - cannot activate prodrug",
                "recommendation": "Consider alternative P2Y12 inhibitor (prasugrel or ticagrelor)"
            },
            "IM": {
                "risk_label": "Ineffective",
                "severity": "high",
                "confidence": 0.93,
                "reason": "Intermediate metabolizer - reduced activation",
                "recommendation": "Consider alternative antiplatelet agent or higher dose"
            },
            "NM": {
                "risk_label": "Safe",
                "severity": "none",
                "confidence": 0.98,
                "reason": "Normal metabolizer - adequate activation",
                "recommendation": "Standard dosing"
            },
            "RM": {
                "risk_label": "Safe",
                "severity": "none",
                "confidence": 0.96,
                "reason": "Rapid metabolizer - adequate activation",
                "recommendation": "Standard dosing"
            },
            "URM": {
                "risk_label": "Safe",
                "severity": "none",
                "confidence": 0.94,
                "reason": "Ultra-rapid metabolizer - adequate activation",
                "recommendation": "Standard dosing"
            }
        }
    },
    "SIMVASTATIN": {
        "primary_gene": "SLCO1B1",
        "secondary_genes": ["CYP3A4"],
        "description": "Statin medication - SLCO1B1 affects transporter activity",
        "risk_phenotype_mapping": {
            "PM": {
                "risk_label": "Toxic",
                "severity": "high",
                "confidence": 0.90,
                "reason": "Poor metabolizer - increased myopathy risk",
                "recommendation": "Use alternative statin (pravastatin, rosuvastatin) or very low dose"
            },
            "IM": {
                "risk_label": "Adjust Dosage",
                "severity": "moderate",
                "confidence": 0.85,
                "reason": "Intermediate metabolizer - increased drug levels",
                "recommendation": "Consider dose reduction or alternative statin"
            },
            "NM": {
                "risk_label": "Safe",
                "severity": "none",
                "confidence": 0.98,
                "reason": "Normal metabolizer - standard dosing appropriate",
                "recommendation": "Standard dosing"
            },
            "RM": {
                "risk_label": "Safe",
                "severity": "none",
                "confidence": 0.96,
                "reason": "Rapid metabolizer - normal clearance",
                "recommendation": "Standard dosing"
            },
            "URM": {
                "risk_label": "Safe",
                "severity": "none",
                "confidence": 0.94,
                "reason": "Ultra-rapid metabolizer - increased clearance",
                "recommendation": "Standard dosing"
            }
        }
    },
    "AZATHIOPRINE": {
        "primary_gene": "TPMT",
        "secondary_genes": [],
        "description": "Immunosuppressant - TPMT enzyme metabolizes thiopurine drugs",
        "risk_phenotype_mapping": {
            "PM": {
                "risk_label": "Toxic",
                "severity": "critical",
                "confidence": 0.97,
                "reason": "Poor metabolizer - severe toxicity risk (bone marrow suppression)",
                "recommendation": "Avoid use or use extreme caution with 10-15% of normal dose"
            },
            "IM": {
                "risk_label": "Toxic",
                "severity": "high",
                "confidence": 0.92,
                "reason": "Intermediate metabolizer - increased toxicity risk",
                "recommendation": "Use 50-75% of normal dose with frequent monitoring"
            },
            "NM": {
                "risk_label": "Safe",
                "severity": "none",
                "confidence": 0.98,
                "reason": "Normal metabolizer - standard dosing appropriate",
                "recommendation": "Standard dosing with routine monitoring"
            },
            "RM": {
                "risk_label": "Safe",
                "severity": "none",
                "confidence": 0.96,
                "reason": "Rapid metabolizer - normal metabolism",
                "recommendation": "Standard dosing"
            },
            "URM": {
                "risk_label": "Safe",
                "severity": "none",
                "confidence": 0.94,
                "reason": "Ultra-rapid metabolizer - normal metabolism",
                "recommendation": "Standard dosing"
            }
        }
    },
    "FLUOROURACIL": {
        "primary_gene": "DPYD",
        "secondary_genes": [],
        "description": "Chemotherapy agent - DPYD deficiency causes severe toxicity",
        "risk_phenotype_mapping": {
            "PM": {
                "risk_label": "Toxic",
                "severity": "critical",
                "confidence": 0.98,
                "reason": "Poor metabolizer - severe life-threatening toxicity risk",
                "recommendation": "CONTRAINDICATED - do not use or use alternative chemotherapy"
            },
            "IM": {
                "risk_label": "Toxic",
                "severity": "critical",
                "confidence": 0.95,
                "reason": "Intermediate metabolizer - high toxicity risk",
                "recommendation": "Consider alternative chemotherapy or significantly reduced dose (25-50%) with close monitoring"
            },
            "NM": {
                "risk_label": "Safe",
                "severity": "none",
                "confidence": 0.98,
                "reason": "Normal metabolizer - standard dosing appropriate",
                "recommendation": "Standard dosing with routine monitoring"
            },
            "RM": {
                "risk_label": "Safe",
                "severity": "none",
                "confidence": 0.96,
                "reason": "Rapid metabolizer - normal metabolism",
                "recommendation": "Standard dosing"
            },
            "URM": {
                "risk_label": "Safe",
                "severity": "none",
                "confidence": 0.94,
                "reason": "Ultra-rapid metabolizer - normal metabolism",
                "recommendation": "Standard dosing"
            }
        }
    }
}

def get_drug_genes(drug_name):
    """Get genes associated with a drug"""
    drug = DRUG_GENE_MAPPING.get(drug_name.upper())
    if drug:
        genes = [drug['primary_gene']] + drug.get('secondary_genes', [])
        return list(set(genes))  # Remove duplicates
    return []

def get_drug_risk(drug_name, phenotype):
    """Get risk assessment for a drug-phenotype combination"""
    drug = DRUG_GENE_MAPPING.get(drug_name.upper())
    if drug:
        return drug['risk_phenotype_mapping'].get(phenotype)
    return None

def get_all_supported_drugs():
    """Get list of all supported drugs"""
    return list(DRUG_GENE_MAPPING.keys())

def is_drug_supported(drug_name):
    """Check if a drug is supported"""
    return drug_name.upper() in DRUG_GENE_MAPPING
