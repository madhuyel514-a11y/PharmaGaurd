"""
Input Validators
Validates VCF files, drug names, and other inputs
"""

import re
from typing import Tuple
from backend.data.drug_gene_mapping import is_drug_supported


def validate_vcf_file(file_content: str, max_size: int = 5242880) -> Tuple[bool, str]:
    """
    Validate VCF file format and size

    Args:
        file_content: Raw file content
        max_size: Maximum file size in bytes (default 5MB)

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    # Check size
    if len(file_content.encode('utf-8')) > max_size:
        return False, f"File size exceeds maximum ({max_size} bytes)"

    # Check for VCF header
    lines = file_content.strip().split('\n')

    if not lines:
        return False, "File is empty"

    # Look for VCF format declaration
    has_format = False
    has_header = False

    for line in lines[:100]:  # Check first 100 lines for headers
        if line.startswith('##fileformat=VCF'):
            has_format = True
        if line.startswith('#CHROM\tPOS\tID\tREF\tALT'):
            has_header = True

    if not has_format:
        return False, "Missing VCFfileformat declaration"

    if not has_header:
        return False, "Missing #CHROM header line"

    return True, ""


def validate_drug_name(drug_name: str) -> Tuple[bool, str]:
    """
    Check if drug is supported

    Args:
        drug_name: Name of drug

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not drug_name or not isinstance(drug_name, str):
        return False, "Drug name must be a non-empty string"

    drug_name = drug_name.strip().upper()

    if not drug_name.isalpha():
        return False, "Drug name must contain only letters"

    if is_drug_supported(drug_name):
        return True, ""
    else:
        return False, f"Drug '{drug_name}' is not supported. Supported drugs: CODEINE, WARFARIN, CLOPIDOGREL, SIMVASTATIN, AZATHIOPRINE, FLUOROURACIL"


def validate_drug_list(drugs: list) -> Tuple[bool, str, list]:
    """
    Validate a list of drug names

    Args:
        drugs: List of drug names

    Returns:
        Tuple of (is_valid: bool, error_message: str, valid_drugs: list)
    """
    if not drugs:
        return False, "Drug list cannot be empty", []

    if not isinstance(drugs, list):
        return False, "Drugs must be provided as a list", []

    valid_drugs = []
    invalid_drugs = []

    for drug in drugs:
        is_valid, error = validate_drug_name(str(drug))
        if is_valid:
            valid_drugs.append(drug.upper())
        else:
            invalid_drugs.append(str(drug))

    if invalid_drugs:
        return False, f"Invalid drugs: {', '.join(invalid_drugs)}", valid_drugs

    return True, "", valid_drugs


def validate_patient_id(patient_id: str) -> Tuple[bool, str]:
    """
    Validate patient ID format

    Args:
        patient_id: Patient identifier

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not patient_id:
        # Patient ID is optional
        return True, ""

    if not isinstance(patient_id, str):
        return False, "Patient ID must be a string"

    if len(patient_id) > 50:
        return False, "Patient ID exceeds maximum length (50 characters)"

    # Allow alphanumeric and underscore
    if not re.match(r'^[A-Za-z0-9_-]+$', patient_id):
        return False, "Patient ID can only contain letters, numbers, underscores, and hyphens"

    return True, ""


def sanitize_file_input(file_content: str) -> str:
    """
    Remove potential malicious content from file

    Args:
        file_content: Raw file content

    Returns:
        Sanitized file content
    """
    # Remove null bytes
    sanitized = file_content.replace('\x00', '')

    # Remove control characters except standard ones
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\r\t')

    # Limit line length to prevent issues
    lines = sanitized.split('\n')
    lines = [line[:10000] for line in lines]  # Max 10KB per line
    sanitized = '\n'.join(lines)

    return sanitized


def validate_request_body(request_data: dict) -> Tuple[bool, str]:
    """
    Validate the overall request body

    Args:
        request_data: Dictionary with request data

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if not isinstance(request_data, dict):
        return False, "Request must be JSON object"

    # Check for VCF file
    vcf_file = request_data.get('vcf_file')
    if not vcf_file:
        return False, "Missing required field: vcf_file"

    if not isinstance(vcf_file, str):
        return False, "vcf_file must be a string"

    # Validate VCF
    is_valid, error = validate_vcf_file(vcf_file)
    if not is_valid:
        return False, f"Invalid VCF file: {error}"

    # Check for drugs
    drugs = request_data.get('drugs')
    if not drugs:
        return False, "Missing required field: drugs"

    if not isinstance(drugs, list):
        return False, "drugs must be a list"

    # Validate drugs
    is_valid, error, _ = validate_drug_list(drugs)
    if not is_valid:
        return False, f"Invalid drugs: {error}"

    # Optional: patient_id
    patient_id = request_data.get('patient_id', '')
    if patient_id:
        is_valid, error = validate_patient_id(patient_id)
        if not is_valid:
            return False, f"Invalid patient_id: {error}"

    return True, ""


def get_validation_errors(request_data: dict) -> list:
    """
    Get detailed list of validation errors

    Args:
        request_data: Dictionary with request data

    Returns:
        List of error messages
    """
    errors = []

    # Check VCF
    vcf_file = request_data.get('vcf_file')
    if not vcf_file:
        errors.append("Missing vcf_file")
    else:
        is_valid, error = validate_vcf_file(vcf_file)
        if not is_valid:
            errors.append(f"VCF validation error: {error}")

    # Check drugs
    drugs = request_data.get('drugs')
    if not drugs:
        errors.append("Missing drugs")
    else:
        is_valid, error, _ = validate_drug_list(drugs)
        if not is_valid:
            errors.append(f"Drug validation error: {error}")

    # Check patient_id if provided
    patient_id = request_data.get('patient_id')
    if patient_id:
        is_valid, error = validate_patient_id(patient_id)
        if not is_valid:
            errors.append(f"Patient ID validation error: {error}")

    return errors
