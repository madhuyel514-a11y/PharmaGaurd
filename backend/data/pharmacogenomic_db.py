# Pharmacogenomic Database
# Contains gene variants and their functional annotations

PHARMACOGENOMIC_DB = {
    "CYP2D6": {
        "full_name": "Cytochrome P450 2D6",
        "chromosome": "22",
        "description": "Primary drug-metabolizing enzyme affected by codeine, atomoxetine, venlafaxine, and tricyclic antidepressants",
        "phenotypes": {
            "PM": {"name": "Poor Metabolizer", "activity_score": 0},
            "IM": {"name": "Intermediate Metabolizer", "activity_score": 0.5},
            "NM": {"name": "Normal Metabolizer", "activity_score": 1.0},
            "RM": {"name": "Rapid Metabolizer", "activity_score": 1.25},
            "URM": {"name": "Ultra-rapid Metabolizer", "activity_score": 2.0}
        },
        "variants": {
            "rs1065852": {
                "rsid": "rs1065852",
                "star_allele": "*4",
                "consequence": "Loss of function",
                "phenotype_effect": "poor_metabolizer",
                "functional_status": "Non-functional",
                "evidence_level": "A"
            },
            "rs28363170": {
                "rsid": "rs28363170",
                "star_allele": "*6",
                "consequence": "Loss of function",
                "phenotype_effect": "poor_metabolizer",
                "functional_status": "Non-functional",
                "evidence_level": "A"
            },
            "rs5030655": {
                "rsid": "rs5030655",
                "star_allele": "*41",
                "consequence": "Reduced function",
                "phenotype_effect": "intermediate_metabolizer",
                "functional_status": "Decreased",
                "evidence_level": "B"
            }
        }
    },
    "CYP2C19": {
        "full_name": "Cytochrome P450 2C19",
        "chromosome": "10",
        "description": "Affects metabolism of clopidogrel, omeprazole, SSRIs, and other drugs",
        "phenotypes": {
            "PM": {"name": "Poor Metabolizer", "activity_score": 0},
            "IM": {"name": "Intermediate Metabolizer", "activity_score": 0.5},
            "NM": {"name": "Normal Metabolizer", "activity_score": 1.0},
            "RM": {"name": "Rapid Metabolizer", "activity_score": 1.25},
            "URM": {"name": "Ultra-rapid Metabolizer", "activity_score": 2.0}
        },
        "variants": {
            "rs4244285": {
                "rsid": "rs4244285",
                "star_allele": "*2",
                "consequence": "Loss of function",
                "phenotype_effect": "poor_metabolizer",
                "functional_status": "Non-functional",
                "evidence_level": "A"
            },
            "rs4986893": {
                "rsid": "rs4986893",
                "star_allele": "*3",
                "consequence": "Loss of function",
                "phenotype_effect": "poor_metabolizer",
                "functional_status": "Non-functional",
                "evidence_level": "A"
            }
        }
    },
    "CYP2C9": {
        "full_name": "Cytochrome P450 2C9",
        "chromosome": "10",
        "description": "Primary enzyme for warfarin metabolism",
        "phenotypes": {
            "PM": {"name": "Poor Metabolizer", "activity_score": 0},
            "IM": {"name": "Intermediate Metabolizer", "activity_score": 0.5},
            "NM": {"name": "Normal Metabolizer", "activity_score": 1.0},
            "RM": {"name": "Rapid Metabolizer", "activity_score": 1.25},
            "URM": {"name": "Ultra-rapid Metabolizer", "activity_score": 2.0}
        },
        "variants": {
            "rs1799853": {
                "rsid": "rs1799853",
                "star_allele": "*2",
                "consequence": "Reduced function",
                "phenotype_effect": "intermediate_metabolizer",
                "functional_status": "Decreased",
                "evidence_level": "A"
            },
            "rs1057910": {
                "rsid": "rs1057910",
                "star_allele": "*3",
                "consequence": "Reduced function",
                "phenotype_effect": "intermediate_metabolizer",
                "functional_status": "Decreased",
                "evidence_level": "A"
            }
        }
    },
    "SLCO1B1": {
        "full_name": "Solute Carrier Organic Anion Transporter Family Member 1B1",
        "chromosome": "12",
        "description": "Affects simvastatin and other statin metabolism",
        "phenotypes": {
            "PM": {"name": "Poor Metabolizer", "activity_score": 0},
            "IM": {"name": "Intermediate Metabolizer", "activity_score": 0.5},
            "NM": {"name": "Normal Metabolizer", "activity_score": 1.0}
        },
        "variants": {
            "rs11045819": {
                "rsid": "rs11045819",
                "star_allele": "*5",
                "consequence": "Reduced transporter activity",
                "phenotype_effect": "intermediate_metabolizer",
                "functional_status": "Decreased",
                "evidence_level": "A"
            },
            "rs4149056": {
                "rsid": "rs4149056",
                "star_allele": "*5",
                "consequence": "Reduced transporter activity",
                "phenotype_effect": "intermediate_metabolizer",
                "functional_status": "Decreased",
                "evidence_level": "A"
            }
        }
    },
    "TPMT": {
        "full_name": "Thiopurine Methyltransferase",
        "chromosome": "6",
        "description": "Enzyme for azathioprine and 6-mercaptopurine metabolism",
        "phenotypes": {
            "PM": {"name": "Poor Metabolizer", "activity_score": 0},
            "IM": {"name": "Intermediate Metabolizer", "activity_score": 0.5},
            "NM": {"name": "Normal Metabolizer", "activity_score": 1.0}
        },
        "variants": {
            "rs1800462": {
                "rsid": "rs1800462",
                "star_allele": "*3",
                "consequence": "Loss of function",
                "phenotype_effect": "poor_metabolizer",
                "functional_status": "Non-functional",
                "evidence_level": "A"
            },
            "rs1800460": {
                "rsid": "rs1800460",
                "star_allele": "*2",
                "consequence": "Reduced function",
                "phenotype_effect": "intermediate_metabolizer",
                "functional_status": "Decreased",
                "evidence_level": "A"
            }
        }
    },
    "DPYD": {
        "full_name": "Dihydropyrimidine Dehydrogenase",
        "chromosome": "1",
        "description": "Enzyme for 5-fluorouracil (chemotherapy) metabolism",
        "phenotypes": {
            "PM": {"name": "Poor Metabolizer", "activity_score": 0},
            "IM": {"name": "Intermediate Metabolizer", "activity_score": 0.5},
            "NM": {"name": "Normal Metabolizer", "activity_score": 1.0}
        },
        "variants": {
            "rs3918290": {
                "rsid": "rs3918290",
                "star_allele": "*2A",
                "consequence": "Loss of function - severe",
                "phenotype_effect": "poor_metabolizer",
                "functional_status": "Non-functional",
                "evidence_level": "A"
            },
            "rs55886062": {
                "rsid": "rs55886062",
                "star_allele": "*13",
                "consequence": "Loss of function",
                "phenotype_effect": "poor_metabolizer",
                "functional_status": "Non-functional",
                "evidence_level": "A"
            }
        }
    }
}

def get_gene_info(gene_name):
    """Get information about a specific gene"""
    return PHARMACOGENOMIC_DB.get(gene_name, None)

def get_variant_info(gene_name, rsid):
    """Get information about a specific variant"""
    gene_data = get_gene_info(gene_name)
    if gene_data and 'variants' in gene_data:
        return gene_data['variants'].get(rsid, None)
    return None

def get_all_genes():
    """Get list of all genes in the database"""
    return list(PHARMACOGENOMIC_DB.keys())

def get_phenotype_from_activity_score(gene_name, activity_score):
    """Determine phenotype based on activity score"""
    gene_data = get_gene_info(gene_name)
    if not gene_data:
        return "Unknown"

    phenotypes = gene_data.get('phenotypes', {})

    # Map activity score to phenotype
    if activity_score == 0:
        return "PM"  # Poor Metabolizer
    elif 0 < activity_score < 1:
        return "IM"  # Intermediate Metabolizer
    elif activity_score == 1.0:
        return "NM"  # Normal Metabolizer
    elif 1 < activity_score < 2:
        return "RM"  # Rapid Metabolizer
    elif activity_score >= 2:
        return "URM"  # Ultra-rapid Metabolizer
    else:
        return "Unknown"
