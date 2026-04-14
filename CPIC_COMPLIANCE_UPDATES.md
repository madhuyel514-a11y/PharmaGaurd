# CPIC Pharmacogenomics Compliance Updates

## Summary
Updated PharmaGuard backend code to enforce CPIC (Clinical Pharmacogenetics Implementation Consortium) guidelines for SLCO1B1/SIMVASTATIN and DPYD/FLUOROURACIL.

---

## Files Modified

### 1. `/backend/data/pharmacogenomic_db.py`
**Changes:**
- Added `star_allele` field to SLCO1B1 variants:
  - `rs4149056` → `"star_allele": "*5"`
  - `rs11045819` → `"star_allele": "*5"`
  
- Added `star_allele` field to DPYD variants:
  - `rs3918290` → `"star_allele": "*2A"` (Loss of function - severe)
  - `rs55886062` → `"star_allele": "*13"` (Loss of function)

**Impact:** Enables proper diplotype inference from detected variants

---

### 2. `/backend/services/risk_predictor.py`
**New Function: `validate_cpic_compliance()`**

Validates and corrects diplotype/phenotype combinations according to CPIC rules:

#### SLCO1B1 - SIMVASTATIN Rules:
```python
# If rs4149056 or rs11045819 detected:
# - Diplotype must contain *5 allele
# - If diplotype is *1/*1 → Corrected to *1/*5
# - Phenotype must be IM (Intermediate Metabolizer)
```

#### DPYD - FLUOROURACIL Rules:
```python
# If rs3918290 (DPYD*2A) detected:
# - Diplotype cannot be *1/*1
# - Corrected to *1/*2A with IM phenotype

# If rs55886062 (DPYD*13) detected:
# - Diplotype cannot be *1/*1
# - Corrected to *1/*13 with IM phenotype

# If BOTH variants detected:
# - Diplotype → *2A/*13 (PM - Poor Metabolizer)
# - Phenotype → PM
```

**Updated `predict_drug_risk()` function:**
- Now calls `validate_cpic_compliance()` before generating risk recommendations
- Corrects invalid diplotype/phenotype combinations
- Returns `cpic_corrections` array documenting any corrections made

---

## CPIC Guideline Compliance

### SLCO1B1 (SIMVASTATIN)
| Diplotype | Phenotype | Clinical Action |
|-----------|-----------|-----------------|
| *1/*1 | NM | Standard dosing (40-80 mg/day) |
| *1/*5 | **IM** | **Reduce dose to max 20 mg/day** ✓ |
| *5/*5 | PM | Use alternative statin |

### DPYD (FLUOROURACIL)
| Diplotype | Phenotype | Clinical Action |
|-----------|-----------|-----------------|
| *1/*1 | NM | Standard dosing |
| *1/*2A | **IM** | **Reduce to 25-50% of dose** ✓ |
| *2A/*2A | PM | **CONTRAINDICATED** ✗ |
| *1/*13 | **IM** | **Reduce to 25-50% of dose** ✓ |
| *2A/*13 | **PM** | **CONTRAINDICATED** ✗ |

---

## Testing

The code has been validated for:
- ✅ Python syntax compliance
- ✅ Database schema consistency
- ✅ CPIC rule application logic

### Example Scenario:
**Input:** Patient with rs3918290 + rs55886062 variants, reported as *1/*1 diplotype with IM phenotype

**Processing:** `validate_cpic_compliance()` detects inconsistency
- Detects both loss-of-function variants
- Corrects diplotype from *1/*1 → *2A/*13
- Corrects phenotype from IM → PM
- Sets risk_label to "Contraindicated"

**Output:** Corrected recommendation: "Do not use fluorouracil; select alternative chemotherapy"

---

## Impact on API Response

Updated `/api/analysis` endpoint now includes:
```json
{
  "pharmacogenomic_profile": {
    "diplotype": "*2A/*13",
    "phenotype": "PM",
    "detected_variants": [...]
  },
  "cpic_corrections": [
    "CPIC Rule: Loss-of-function variant(s) detected. Corrected diplotype to *2A/*13 with PM phenotype"
  ],
  "clinical_recommendation": {
    "action": "Contraindicated",
    "cpic_guideline": "Do not use fluorouracil; select alternative chemotherapy"
  }
}
```

---

## Benefits

1. **Automatic Compliance:** Backend automatically validates against CPIC guidelines
2. **Clinical Safety:** Prevents unsafe drug recommendations
3. **Data Integrity:** Corrects inconsistent variant-phenotype assignments
4. **Transparency:** Documents all corrections in response
5. **Auditability:** CPIC corrections logged for clinical review

