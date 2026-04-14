"""
Main Analysis API Endpoint
Orchestrates the pharmacogenomic analysis workflow
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
import traceback

from backend.services.vcf_parser import parse_vcf_file, validate_vcf_format, get_variants_for_genes
from backend.services.variant_matcher import match_all_target_genes, get_matched_rsids
from backend.services.risk_predictor import predict_drug_risk, predict_risk_for_all_drugs
from backend.services.cpic_recommendations import get_recommendation, get_monitoring, get_dosing
from backend.services.llm_explainer import generate_llm_explanation
from backend.services.ml.ai_features import (
    build_gene_snapshot,
    generate_ai_summary,
    get_primary_genes_for_drug,
)
from backend.services.ml.predictor import GENE_TO_FEATURE_MAP
from backend.services.ml_service import analyze_ml_drug_response
from backend.utils.validators import validate_request_body, get_validation_errors, sanitize_file_input
from backend.utils.json_schema import validate_output, ensure_schema_compliance, validate_and_fix
from backend.utils.recommendation_logic import determine_final_recommendation
from backend.data.drug_gene_mapping import get_drug_genes, get_all_supported_drugs

# Create Blueprint
analysis_bp = Blueprint('analysis', __name__, url_prefix='/api')


@analysis_bp.route('/analyze', methods=['POST'])
def analyze():
    """
    Main endpoint: POST /api/analyze

    Request JSON:
    {
        "vcf_file": "<file_content>",
        "drugs": ["CODEINE", "WARFARIN"],
        "patient_id": "PATIENT_XXX" (optional)
    }

    Response: Pharmacogenomic analysis results for each drug as an array
    """
    try:
        # Parse request
        if not request.is_json:
            return jsonify({
                "error": "Request must be JSON",
                "status": "failed"
            }), 400

        request_data = request.get_json()

        # Validate request
        is_valid, error = validate_request_body(request_data)
        if not is_valid:
            return jsonify({
                "error": error,
                "status": "validation_error"
            }), 400

        # Extract and sanitize inputs
        vcf_content = sanitize_file_input(request_data.get('vcf_file', ''))
        drugs = [d.upper() for d in request_data.get('drugs', [])]
        patient_id = request_data.get('patient_id', f"PATIENT_{uuid.uuid4().hex[:8].upper()}")

        # Step 1: Validate VCF format
        is_valid, vcf_error = validate_vcf_format(vcf_content)
        if not is_valid:
            return jsonify({
                "error": f"Invalid VCF file: {vcf_error}",
                "status": "vcf_validation_error"
            }), 400

        # Step 2: Parse VCF file
        vcf_data = parse_vcf_file(vcf_content)

        if "error" in vcf_data:
            return jsonify({
                "error": f"VCF parsing error: {vcf_data['error']}",
                "status": "vcf_parsing_error"
            }), 400

        variants = vcf_data.get('variants', [])

        if not variants:
            return jsonify({
                "error": "No variants found in VCF file",
                "status": "no_variants_found"
            }), 400

        # Step 3: Match variants for all target genes
        all_target_genes = set()
        for drug in drugs:
            genes = get_drug_genes(drug)
            all_target_genes.update(genes)
        all_target_genes.update(GENE_TO_FEATURE_MAP.keys())

        gene_matches = match_all_target_genes(variants, list(all_target_genes))

        # Organize matched variants by gene
        variants_by_gene = {}
        for gene, matches in gene_matches.items():
            variants_by_gene[gene] = matches.get('matched_variants', [])

        # Step 4: Analyze each drug
        results = []

        for drug in drugs:
            drug_ml_result = analyze_ml_drug_response(drug, variants_by_gene)
            drug_result = analyze_drug(
                drug,
                variants_by_gene,
                patient_id,
                drug_ml_result,
            )
            results.append(drug_result)

        # Step 6: Build a drug-specific AI summary for each result so the
        # summary only reports pharmacogenes relevant to that drug.
        for index, result in enumerate(results):
            result["ai_summary"] = generate_ai_summary(result)
            results[index], _ = validate_and_fix(result)

        # Return array of results
        return jsonify(results), 200

    except Exception as e:
        traceback.print_exc()
        return jsonify({
            "error": f"Internal server error: {str(e)}",
            "status": "error"
        }), 500


def analyze_drug(
    drug_name: str,
    variants_by_gene: dict,
    patient_id: str,
    ml_result: dict,
) -> dict:
    """
    Analyze a single drug for the patient

    Args:
        drug_name: Name of drug
        variants_by_gene: Dictionary of matched variants organized by gene
        patient_id: Patient identifier

    Returns:
        Analysis result dictionary for single drug
    """
    try:
        # Get primary gene for this drug
        genes = get_drug_genes(drug_name)
        primary_gene = genes[0] if genes else None

        if not primary_gene:
            return {
                "patient_id": patient_id,
                "drug": drug_name,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error": f"No gene information found for {drug_name}",
                "status": "error"
            }

        # Get variants for the primary gene used by the legacy risk pipeline.
        drug_variants = variants_by_gene.get(primary_gene, [])

        # Build a filtered detected-variant list for the drug-specific summary.
        relevant_summary_genes = get_primary_genes_for_drug(drug_name) or [primary_gene]
        filtered_detected_variants = []
        for gene_name in relevant_summary_genes:
            for variant in variants_by_gene.get(gene_name, []):
                filtered_detected_variants.append({
                    "rsid": variant.get('patient_rsid'),
                    "gene": gene_name,
                    "consequence": variant.get('db_info', {}).get('consequence', 'Unknown')
                })
        gene_snapshot = build_gene_snapshot(drug_name, variants_by_gene)
        detected_gene_names = []
        for variant in filtered_detected_variants:
            gene_name = str(variant.get("gene", "")).upper()
            if gene_name and gene_name not in detected_gene_names:
                detected_gene_names.append(gene_name)
        gene_variants = {gene_name: 1 for gene_name in detected_gene_names}

        # Step 1: Predict risk
        risk_result = predict_drug_risk(drug_name, drug_variants, primary_gene)

        if "error" in risk_result:
            # No variants for this drug - safe dosing
            risk_result = {
                "drug": drug_name,
                "gene": primary_gene,
                "phenotype": "NM",
                "risk_label": "Safe",
                "severity": "none",
                "confidence_score": 0.8,
                "reasoning": "No known variants detected"
            }

        # Step 2: Get CPIC recommendations
        phenotype = risk_result.get('phenotype', 'Unknown')
        cpic_rec = get_recommendation(drug_name, phenotype)
        final_recommendation, final_alternatives = determine_final_recommendation(
            drug_name=drug_name,
            phenotype=phenotype,
            severity=risk_result.get('severity', ml_result.get('severity', 'moderate')),
            risk_label=risk_result.get('risk_label', 'Unknown'),
        )

        # Step 3: Generate LLM explanation
        llm_explanation = generate_llm_explanation(
            drug_name=drug_name,
            phenotype=phenotype,
            detected_variants=drug_variants,
            risk_label=risk_result.get('risk_label', 'Unknown'),
            gene_name=primary_gene
        )

        # Step 4: Build response
        response = {
            "patient_id": patient_id,
            "drug": drug_name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "primary_gene": relevant_summary_genes[0] if relevant_summary_genes else primary_gene,
            "detected_variants": filtered_detected_variants,
            "gene_snapshot": gene_snapshot,
            "gene_variants": gene_variants,
            "genes_detected": detected_gene_names,
            "drug_recommendation": final_recommendation,
            "ml_prediction": ml_result.get('ml_prediction', 'Unavailable'),
            "confidence": ml_result.get('confidence', 0.0),
            "risk_score": ml_result.get('risk_score', 0.0),
            "risk_level": ml_result.get('risk_level', 'Low'),
            "alternative_drugs": final_alternatives if "Avoid" in final_recommendation else [],
            "adr_prediction": ml_result.get('adr_prediction', {}),
            "cpic_recommendation": final_recommendation,
            "ml_model_status": ml_result.get('ml_model_status', 'unavailable'),
            "ml_probabilities": ml_result.get('ml_probabilities', {}),
            "ml_features": ml_result.get('ml_features', {}),
            "risk_assessment": {
                "risk_label": risk_result.get('risk_label', 'Unknown'),
                "confidence_score": risk_result.get('confidence_score', 0.5),
                "severity": risk_result.get('severity', ml_result.get('severity', 'moderate'))
            },
            "pharmacogenomic_profile": {
                "primary_gene": relevant_summary_genes[0] if relevant_summary_genes else primary_gene,
                "diplotype": risk_result.get('diplotype', '*1/*1'),
                "phenotype": phenotype,
                "detected_variants": filtered_detected_variants
            },
            "clinical_recommendation": {
                "action": final_recommendation,
                "cpic_guideline": cpic_rec.get('dosing', ''),
                "monitoring": cpic_rec.get('monitoring', '')
            },
            "llm_generated_explanation": {
                "summary": llm_explanation.get('summary', ''),
                "biological_mechanism": llm_explanation.get('biological_mechanism', ''),
                "variant_effects": llm_explanation.get('variant_effects', {})
            },
            "quality_metrics": {
                "vcf_parsing_success": True,
                "variant_confidence": risk_result.get('confidence_score', 0.5),
                "completeness": len(drug_variants) / max(len(drug_variants), 1)
            }
        }

        # Validate and fix compliance
        response, errors = validate_and_fix(response)

        return response

    except Exception as e:
        traceback.print_exc()
        return {
            "patient_id": patient_id,
            "drug": drug_name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": f"Error analyzing {drug_name}: {str(e)}",
            "status": "error"
        }


@analysis_bp.route('/supported-drugs', methods=['GET'])
def get_supported_drugs():
    """
    Get list of supported drugs

    Returns:
        JSON array of supported drug names
    """
    drugs = get_all_supported_drugs()
    return jsonify({
        "supported_drugs": drugs,
        "count": len(drugs)
    }), 200


@analysis_bp.route('/validate-vcf', methods=['POST'])
def validate_vcf():
    """
    Validate a VCF file without full analysis

    Request JSON:
    {
        "vcf_file": "<file_content>"
    }

    Returns:
        Validation result
    """
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400

        vcf_content = request.get_json().get('vcf_file', '')

        if not vcf_content:
            return jsonify({"error": "vcf_file is required"}), 400

        # Validate
        is_valid, error = validate_vcf_format(vcf_content)

        if is_valid:
            # Parse to get variant count
            data = parse_vcf_file(vcf_content)
            variant_count = len(data.get('variants', []))
            return jsonify({
                "valid": True,
                "message": "VCF file is valid",
                "variant_count": variant_count
            }), 200
        else:
            return jsonify({
                "valid": False,
                "error": error
            }), 400

    except Exception as e:
        return jsonify({
            "valid": False,
            "error": f"Validation error: {str(e)}"
        }), 500
