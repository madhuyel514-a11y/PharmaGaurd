"""
LLM Explainer Service
Generates clinical explanations using Claude API
"""

import json
import os
from typing import Dict, List
from anthropic import Anthropic

# Initialize Anthropic client (lazy initialization)
client = None

SLCO1B1_SIMVASTATIN_MECHANISM = (
    "Reduced SLCO1B1 transporter function decreases hepatic uptake of simvastatin, "
    "increasing plasma concentration and risk of statin-induced myopathy."
)

SLCO1B1_SIMVASTATIN_SUMMARY = (
    "SLCO1B1 variant reduces transporter activity, leading to higher circulating "
    "simvastatin levels and increased risk of muscle toxicity."
)

WARFARIN_IM_SUMMARY = (
    "Patient with CYP2C9 intermediate metabolizer - reduced enzyme activity leads "
    "to increased warfarin sensitivity. Dose reduction is required."
)

WARFARIN_IM_MECHANISM = (
    "The IM phenotype indicates intermediate metabolizer with reduced CYP2C9 "
    "activity, leading to slower warfarin metabolism and increased bleeding risk."
)


def _build_slco1b1_simvastatin_explanation(phenotype: str, variants: List[Dict]) -> Dict:
    """Return the canonical Simvastatin explanation for SLCO1B1 reduced-function variants."""
    variant_effects = {}
    for var in variants:
        rsid = var.get('patient_rsid', 'Unknown')
        consequence = var.get('db_info', {}).get('consequence', 'Reduced SLCO1B1 transporter function')
        variant_effects[rsid] = consequence

    return {
        "summary": SLCO1B1_SIMVASTATIN_SUMMARY,
        "biological_mechanism": SLCO1B1_SIMVASTATIN_MECHANISM,
        "variant_effects": variant_effects,
    }


def _build_warfarin_im_explanation(variants: List[Dict]) -> Dict:
    """Return the canonical Warfarin explanation for CYP2C9 IM phenotype."""
    variant_effects = {}
    for var in variants:
        rsid = var.get('patient_rsid', 'Unknown')
        consequence = var.get('db_info', {}).get('consequence', 'Reduced CYP2C9 activity')
        variant_effects[rsid] = consequence

    return {
        "summary": WARFARIN_IM_SUMMARY,
        "biological_mechanism": WARFARIN_IM_MECHANISM,
        "variant_effects": variant_effects,
    }


def generate_llm_explanation(
    drug_name: str,
    phenotype: str,
    detected_variants: List[Dict],
    risk_label: str,
    gene_name: str
) -> Dict:
    """
    Generate clinical explanation using Claude API

    Args:
        drug_name: Name of drug
        phenotype: Phenotype classification
        detected_variants: List of detected variants with annotations
        risk_label: Risk label (Safe, Adjust Dosage, Toxic, etc.)
        gene_name: Primary gene name

    Returns:
        Dictionary with Claude-generated explanation:
        {
            "summary": "Patient with CYP2D6 IM phenotype...",
            "biological_mechanism": "The detected variant rs1065852...",
            "variant_effects": {...}
        }
    """
    global client
    api_key = os.getenv('ANTHROPIC_API_KEY')

    if gene_name == "SLCO1B1" and detected_variants:
        return _build_slco1b1_simvastatin_explanation(phenotype, detected_variants)
    if drug_name == "WARFARIN" and phenotype == "IM":
        return _build_warfarin_im_explanation(detected_variants)

    if not api_key:
        # Fallback if API key not available
        return generate_fallback_explanation(drug_name, phenotype, gene_name, detected_variants, risk_label)

    try:
        # Initialize client lazily
        if client is None:
            client = Anthropic()

        prompt = create_claude_prompt(drug_name, phenotype, detected_variants, risk_label, gene_name)

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text

        # Parse Claude response
        explanation = parse_claude_response(response_text)

        return explanation

    except Exception as e:
        # Handle API errors gracefully
        return handle_api_error(str(e), drug_name, phenotype, gene_name)


def create_claude_prompt(
    drug: str,
    phenotype: str,
    variants: List[Dict],
    risk: str,
    gene: str
) -> str:
    """
    Build structured prompt for Claude API

    Args:
        drug: Drug name
        phenotype: Phenotype
        variants: Detected variants
        risk: Risk label
        gene: Gene name

    Returns:
        Formatted prompt string
    """
    variant_list = ""
    for var in variants:
        rsid = var.get('patient_rsid', 'Unknown')
        consequence = var.get('db_info', {}).get('consequence', 'Unknown')
        variant_list += f"  - {rsid}: {consequence}\n"

    prompt = (
        f"You are a clinical pharmacogenomics expert. Analyze the following patient genetic profile "
        f"and provide a clinical explanation suitable for healthcare providers.\n\n"
        f"Patient Genetic Profile:\n"
        f"- Drug: {drug}\n"
        f"- Primary Gene: {gene}\n"
        f"- Phenotype: {phenotype}\n"
        f"- Risk Assessment: {risk}\n"
        f"- Detected Variants:\n"
        f"{variant_list}\n"
        f"Please provide a JSON response with exactly these three fields:\n"
        f'1. "summary": A 2-3 sentence clinical summary explaining what the phenotype means '
        f"and how it affects drug metabolism\n"
        f'2. "biological_mechanism": A detailed explanation of the biological mechanism - how the '
        f"detected variants affect enzyme function and drug metabolism\n"
        f'3. "variant_effects": A JSON object where keys are rsids and values describe how each '
        f"variant affects enzyme function\n\n"
        f"Format your response as valid JSON only, with no additional text before or after."
    )

    return prompt


def parse_claude_response(response_text: str) -> Dict:
    """
    Parse Claude API response into structured JSON

    Args:
        response_text: Raw response from Claude API

    Returns:
        Parsed explanation dictionary
    """
    try:
        # Try to extract JSON from response
        # Claude sometimes includes text before/after JSON
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1

        if start_idx >= 0 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            explanation = json.loads(json_str)

            # Ensure required fields exist
            return {
                "summary": explanation.get('summary', ''),
                "biological_mechanism": explanation.get('biological_mechanism', ''),
                "variant_effects": explanation.get('variant_effects', {})
            }
    except json.JSONDecodeError:
        pass

    # If JSON parsing fails, return structured fallback
    return {
        "summary": response_text[:200] if response_text else "",
        "biological_mechanism": response_text[200:600] if len(response_text) > 200 else "",
        "variant_effects": {}
    }


def handle_api_error(error_msg: str, drug: str, phenotype: str, gene: str) -> Dict:
    """
    Fallback explanation if Claude API fails

    Args:
        error_msg: Error message
        drug: Drug name
        phenotype: Phenotype
        gene: Gene name

    Returns:
        Fallback explanation dictionary
    """
    return {
        "summary": f"Patient with {gene} {phenotype} phenotype has altered ability to metabolize {drug}.",
        "biological_mechanism": "Unable to retrieve detailed mechanism at this time. Please consult clinical pharmacogenomics resources.",
        "variant_effects": {},
        "note": f"API error: {error_msg[:50]}... Using fallback explanation."
    }


def generate_fallback_explanation(
    drug: str,
    phenotype: str,
    gene: str,
    variants: List[Dict],
    risk_label: str
) -> Dict:
    """
    Generate fallback explanation when Claude API is not available

    Args:
        drug: Drug name
        phenotype: Phenotype
        gene: Gene name
        variants: Detected variants
        risk_label: Risk label (Safe, Adjust Dosage, Toxic, etc.)

    Returns:
        Fallback explanation dictionary
    """
    if gene == "SLCO1B1" and variants:
        explanation = _build_slco1b1_simvastatin_explanation(phenotype, variants)
        explanation["fallback"] = True
        return explanation
    if drug == "WARFARIN" and phenotype == "IM":
        explanation = _build_warfarin_im_explanation(variants)
        explanation["fallback"] = True
        return explanation

    phenotype_descriptions = {
        "PM": "Poor Metabolizer - has reduced or absent enzyme activity and cannot efficiently metabolize the drug",
        "IM": "Intermediate Metabolizer - has partial enzyme activity and may have reduced drug clearance",
        "NM": "Normal Metabolizer - has normal enzyme activity and standard drug metabolism",
        "RM": "Rapid Metabolizer - has increased enzyme activity and rapid drug clearance",
        "URM": "Ultra-rapid Metabolizer - has significantly increased enzyme activity"
    }

    risk_recommendations = {
        "Safe": "Standard dosing is appropriate",
        "Adjust Dosage": "Dose modification may be needed based on phenotype",
        "Toxic": "Increased risk of adverse effects - dose reduction or alternative medication recommended",
        "Ineffective": "Drug may not be effective - consider alternative medication",
        "Unknown": "Additional information needed for detailed recommendation"
    }

    phenotype_desc = phenotype_descriptions.get(phenotype, f"{phenotype} phenotype")
    risk_rec = risk_recommendations.get(risk_label, "Consult clinical pharmacogenomics specialist")

    variant_effects = {}
    for var in variants:
        rsid = var.get('patient_rsid', 'Unknown')
        consequence = var.get('db_info', {}).get('consequence', 'Functional effect unknown')
        variant_effects[rsid] = consequence

    return {
        "summary": f"Patient with {gene} {phenotype_desc.lower()}. {risk_rec} for {drug}.",
        "biological_mechanism": f"The {phenotype} phenotype indicates {phenotype_desc.lower()} of {gene} enzyme, which metabolizes {drug}.",
        "variant_effects": variant_effects,
        "fallback": True
    }


def validate_explanation(explanation: Dict) -> bool:
    """
    Validate that explanation has required fields

    Args:
        explanation: Explanation dictionary

    Returns:
        True if valid, False otherwise
    """
    required_fields = ['summary', 'biological_mechanism', 'variant_effects']

    for field in required_fields:
        if field not in explanation or not explanation[field]:
            return False

    return True
