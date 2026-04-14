# CPIC (Clinical Pharmacogenetics Implementation Consortium) Guidelines
# Dosing recommendations based on phenotype classifications

CPIC_GUIDELINES = {
    "CODEINE": {
        "gene": "CYP2D6",
        "recommendations": {
            "PM": {
                "action": "Use alternative medication",
                "dosing": "Avoid codeine",
                "monitoring": "Not applicable",
                "evidence": "CPIC Level A - Strong",
                "clinical_notes": "No benefit expected; increased risk of adverse effects"
            },
            "IM": {
                "action": "Reduce dose",
                "dosing": "Consider 25-50% dose reduction",
                "monitoring": "Monitor for pain relief; if inadequate, consider alternative",
                "evidence": "CPIC Level B - Moderate",
                "clinical_notes": "Patient may not achieve adequate pain control at normal doses"
            },
            "NM": {
                "action": "Normal dosing",
                "dosing": "Standard dosing",
                "monitoring": "Routine monitoring",
                "evidence": "CPIC Level A",
                "clinical_notes": "Normal metabolism expected"
            },
            "RM": {
                "action": "Monitor closely",
                "dosing": "Standard dosing; can increase if needed",
                "monitoring": "Monitor for toxicity",
                "evidence": "CPIC Level B",
                "clinical_notes": "May metabolize faster than average"
            },
            "URM": {
                "action": "Use alternative medication",
                "dosing": "Avoid codeine or consider alternative",
                "monitoring": "If used, monitor closely",
                "evidence": "CPIC Level B",
                "clinical_notes": "May not achieve therapeutic benefit"
            }
        }
    },
    "WARFARIN": {
        "gene": "CYP2C9/VKORC1",
        "recommendations": {
            "PM": {
                "action": "Significantly reduce dose",
                "dosing": "Start with 2-3 mg/day (vs. 5-7 mg typical)",
                "monitoring": "More frequent INR checks (every 2-3 days initially)",
                "evidence": "CPIC Level A - Strong",
                "clinical_notes": "Expect slower metabolism; increased bleeding risk"
            },
            "IM": {
                "action": "Reduce dose",
                "dosing": "3-4 mg/day or 80-90% of standard dose",
                "monitoring": "More frequent INR checks",
                "evidence": "CPIC Level B - Moderate",
                "clinical_notes": "Slower metabolism; monitor INR closely"
            },
            "NM": {
                "action": "Standard dosing",
                "dosing": "5-7 mg/day with titration to INR target",
                "monitoring": "Routine INR monitoring (5-7 days after changes)",
                "evidence": "CPIC Level A",
                "clinical_notes": "Standard management expected"
            },
            "RM": {
                "action": "Consider higher dose",
                "dosing": "May need 10-15% higher doses",
                "monitoring": "Monitor INR at standard intervals",
                "evidence": "CPIC Level B",
                "clinical_notes": "Faster metabolism may require dose adjustment"
            },
            "URM": {
                "action": "Consider much higher dose",
                "dosing": "May need 20-30% higher doses",
                "monitoring": "Monitor INR at standard intervals",
                "evidence": "CPIC Level B",
                "clinical_notes": "Very rapid metabolism"
            }
        }
    },
    "CLOPIDOGREL": {
        "gene": "CYP2C19",
        "recommendations": {
            "PM": {
                "action": "Use alternative P2Y12 inhibitor",
                "dosing": "Use prasugrel or ticagrelor instead",
                "monitoring": "N/A",
                "evidence": "CPIC Level A - Strong",
                "clinical_notes": "Cannot activate prodrug; poor antiplatelet effect"
            },
            "IM": {
                "action": "Consider alternative P2Y12 inhibitor",
                "dosing": "Consider prasugrel or ticagrelor; or use 600mg loading dose",
                "monitoring": "If clopidogrel used, monitor for efficacy",
                "evidence": "CPIC Level B - Moderate",
                "clinical_notes": "Reduced activation; may have inadequate antiplatelet effect"
            },
            "NM": {
                "action": "Standard dosing",
                "dosing": "300-600 mg loading dose, 75 mg daily",
                "monitoring": "Routine monitoring",
                "evidence": "CPIC Level A",
                "clinical_notes": "Normal activation and antiplatelet effect"
            },
            "RM": {
                "action": "Standard dosing",
                "dosing": "300-600 mg loading dose, 75 mg daily",
                "monitoring": "Routine monitoring",
                "evidence": "CPIC Level A",
                "clinical_notes": "Adequate activation expected"
            },
            "URM": {
                "action": "Standard dosing",
                "dosing": "300-600 mg loading dose, 75 mg daily",
                "monitoring": "Routine monitoring",
                "evidence": "CPIC Level A",
                "clinical_notes": "Adequate activation expected"
            }
        }
    },
    "SIMVASTATIN": {
        "gene": "SLCO1B1",
        "recommendations": {
            "PM": {
                "action": "Use alternative statin",
                "dosing": "Avoid simvastatin; use pravastatin or rosuvastatin",
                "monitoring": "N/A",
                "evidence": "CPIC Level A - Strong",
                "clinical_notes": "Significantly increased myopathy risk"
            },
            "IM": {
                "action": "Reduce dose or use alternative",
                "dosing": "Max 20 mg/day or use pravastatin/rosuvastatin",
                "monitoring": "Monitor for muscle pain/CK elevation",
                "evidence": "CPIC Level B",
                "clinical_notes": "Increased myopathy risk; monitor closely"
            },
            "NM": {
                "action": "Standard dosing",
                "dosing": "Up to 40-80 mg/day based on indication",
                "monitoring": "Routine lipid monitoring",
                "evidence": "CPIC Level A",
                "clinical_notes": "Normal metabolism and clearance"
            },
            "RM": {
                "action": "Standard dosing",
                "dosing": "Up to 40-80 mg/day based on indication",
                "monitoring": "Routine lipid monitoring",
                "evidence": "CPIC Level A",
                "clinical_notes": "Normal metabolism expected"
            },
            "URM": {
                "action": "Standard dosing",
                "dosing": "Up to 40-80 mg/day based on indication",
                "monitoring": "Routine lipid monitoring",
                "evidence": "CPIC Level A",
                "clinical_notes": "Adequate metabolism expected"
            }
        }
    },
    "AZATHIOPRINE": {
        "gene": "TPMT",
        "recommendations": {
            "PM": {
                "action": "Avoid or use extreme caution",
                "dosing": "Avoid completely or max 10-15% of normal dose (0.1-0.15 mg/kg/day)",
                "monitoring": "Very frequent CBC monitoring if used; baseline and weekly x 4, then monthly",
                "evidence": "CPIC Level A - Strong",
                "clinical_notes": "Very high risk of severe myelosuppression and fatal bone marrow toxicity"
            },
            "IM": {
                "action": "Reduce dose significantly",
                "dosing": "50-75% of normal dose (0.5-0.75 mg/kg/day)",
                "monitoring": "Frequent CBC monitoring: baseline, then at days 3, 7, 14, then monthly",
                "evidence": "CPIC Level B",
                "clinical_notes": "Increased toxicity risk; frequent monitoring mandatory"
            },
            "NM": {
                "action": "Standard dosing",
                "dosing": "1-2.5 mg/kg/day based on indication",
                "monitoring": "Routine CBC monitoring",
                "evidence": "CPIC Level A",
                "clinical_notes": "Normal metabolism; standard management"
            },
            "RM": {
                "action": "Standard dosing",
                "dosing": "1-2.5 mg/kg/day based on indication",
                "monitoring": "Routine CBC monitoring",
                "evidence": "CPIC Level A",
                "clinical_notes": "Normal metabolism expected"
            },
            "URM": {
                "action": "Standard dosing",
                "dosing": "1-2.5 mg/kg/day based on indication",
                "monitoring": "Routine CBC monitoring",
                "evidence": "CPIC Level A",
                "clinical_notes": "Adequate metabolism expected"
            }
        }
    },
    "FLUOROURACIL": {
        "gene": "DPYD",
        "recommendations": {
            "PM": {
                "action": "Contraindicated",
                "dosing": "DO NOT USE - use alternative chemotherapy",
                "monitoring": "N/A",
                "evidence": "CPIC Level A - Strong",
                "clinical_notes": "Risk of life-threatening toxicity (severe mucositis, diarrhea, myelosuppression)"
            },
            "IM": {
                "action": "Significantly reduce dose",
                "dosing": "Start at 25-50% of standard dose with careful escalation",
                "monitoring": "Close clinical and laboratory monitoring for toxicity",
                "evidence": "CPIC Level B",
                "clinical_notes": "High toxicity risk; consider alternative chemotherapy if available"
            },
            "NM": {
                "action": "Standard dosing",
                "dosing": "Standard 5-FU chemotherapy dosing per protocol",
                "monitoring": "Routine monitoring per protocol",
                "evidence": "CPIC Level A",
                "clinical_notes": "Normal metabolism expected"
            },
            "RM": {
                "action": "Standard dosing",
                "dosing": "Standard 5-FU chemotherapy dosing per protocol",
                "monitoring": "Routine monitoring per protocol",
                "evidence": "CPIC Level A",
                "clinical_notes": "Adequate metabolism expected"
            },
            "URM": {
                "action": "Standard dosing",
                "dosing": "Standard 5-FU chemotherapy dosing per protocol",
                "monitoring": "Routine monitoring per protocol",
                "evidence": "CPIC Level A",
                "clinical_notes": "Adequate metabolism expected"
            }
        }
    }
}

def get_cpic_recommendation(drug_name, phenotype):
    """Get CPIC guidelines for a drug-phenotype pair"""
    drug = CPIC_GUIDELINES.get(drug_name.upper())
    if drug:
        return drug['recommendations'].get(phenotype)
    return None

def get_cpic_action(drug_name, phenotype):
    """Get the recommended action from CPIC guidelines"""
    rec = get_cpic_recommendation(drug_name, phenotype)
    if rec:
        return rec.get('action')
    return None

def get_cpic_dosing(drug_name, phenotype):
    """Get dosing recommendations from CPIC guidelines"""
    rec = get_cpic_recommendation(drug_name, phenotype)
    if rec:
        return rec.get('dosing')
    return None

def get_cpic_monitoring(drug_name, phenotype):
    """Get monitoring recommendations from CPIC guidelines"""
    rec = get_cpic_recommendation(drug_name, phenotype)
    if rec:
        return rec.get('monitoring')
    return None
