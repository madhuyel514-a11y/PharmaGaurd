"""
VCF File Parser Service
Parses Variant Call Format (VCF) files and extracts genetic variants
"""

import re
from typing import Dict, List, Tuple


def validate_vcf_format(file_content: str) -> Tuple[bool, str]:
    """
    Validate VCF file format (v4.2)

    Args:
        file_content: Raw VCF file content

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    lines = file_content.strip().split('\n')

    if not lines:
        return False, "Empty file"

    # Check for VCF header
    has_header = False
    header_line = None

    for line in lines:
        if line.startswith('##fileformat='):
            has_header = True
            if 'VCF' not in line:
                return False, "Invalid VCF format line"
        elif line.startswith('#CHROM'):
            header_line = line
            break

    if not has_header:
        return False, "Missing ##fileformat=VCF header"

    if not header_line:
        return False, "Missing #CHROM header line"

    # Check header columns
    expected_cols = ['#CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'INFO']
    header_cols = header_line.split('\t')[:8]

    if header_cols != expected_cols:
        return False, f"Invalid header columns. Expected {expected_cols}, got {header_cols}"

    return True, ""


def parse_vcf_file(file_content: str) -> Dict:
    """
    Parse VCF file content and extract variants

    Args:
        file_content: Raw VCF file content

    Returns:
        Dictionary with metadata and variants:
        {
            "metadata": {...},
            "variants": [
                {
                    "rsid": "rs1065852",
                    "chromosome": "22",
                    "position": 42521919,
                    "ref": "A",
                    "alt": "G",
                    "genotype": "0/1",
                    "quality": 60,
                    "info": {...}
                }
            ]
        }
    """
    lines = file_content.strip().split('\n')

    result = {
        "metadata": {},
        "variants": []
    }

    metadata_lines = []
    header_line = None
    data_lines = []

    # Parse lines
    for line in lines:
        if line.startswith('##'):
            metadata_lines.append(line)
        elif line.startswith('#CHROM'):
            header_line = line
        elif line and not line.startswith('#'):
            data_lines.append(line)

    # Parse metadata
    for meta_line in metadata_lines:
        if meta_line.startswith('##fileformat='):
            result['metadata']['format'] = meta_line.split('=')[1]
        elif meta_line.startswith('##fileDate='):
            result['metadata']['fileDate'] = meta_line.split('=')[1]
        elif meta_line.startswith('##reference='):
            result['metadata']['reference'] = meta_line.split('=')[1]

    # Parse variants
    for line in data_lines:
        if not line.strip():
            continue

        columns = line.split('\t')

        if len(columns) < 8:
            continue

        try:
            chrom = columns[0]
            pos = int(columns[1])
            rsid = columns[2] if columns[2] != '.' else None
            ref = columns[3]
            alt = columns[4]
            qual = columns[5]
            filter_val = columns[6]
            info = columns[7]

            # Parse genotype if present (sample column)
            genotype = None
            if len(columns) >= 10:
                genotype = columns[9].split(':')[0]  # Get GT field (first field in sample)

            # Parse INFO field
            info_dict = {}
            if info != '.':
                for item in info.split(';'):
                    if '=' in item:
                        key, value = item.split('=', 1)
                        info_dict[key] = value
                    else:
                        info_dict[item] = True

            variant = {
                "chromosome": chrom,
                "position": pos,
                "rsid": rsid,
                "ref": ref,
                "alt": alt,
                "quality": float(qual) if qual != '.' else None,
                "filter": filter_val,
                "genotype": genotype,
                "info": info_dict
            }

            result['variants'].append(variant)

        except (ValueError, IndexError) as e:
            # Skip malformed variant lines
            continue

    return result


def get_variants_for_genes(variants: List[Dict], genes: List[str]) -> List[Dict]:
    """
    Filter variants matching target genes
    Uses gene annotations from INFO field or simple heuristics

    Args:
        variants: List of variant dictionaries
        genes: List of gene names to filter for (e.g., ['CYP2D6', 'CYP2C19'])

    Returns:
        Filtered list of variants matching target genes
    """
    filtered = []

    for variant in variants:
        # Check if gene is mentioned in INFO field
        gene_info = variant.get('info', {}).get('Gene')

        if gene_info:
            for gene in genes:
                if gene.upper() in gene_info.upper():
                    filtered.append(variant)
                    break
        else:
            # In real implementation, would use annotation tools
            # For now, include all variants for manual filtering
            filtered.append(variant)

    return filtered


def extract_rsids(variants: List[Dict]) -> List[str]:
    """
    Extract RS IDs from variant list for database lookup

    Args:
        variants: List of variant dictionaries

    Returns:
        List of RS IDs (excluding None values)
    """
    rsids = []
    for variant in variants:
        rsid = variant.get('rsid')
        if rsid:
            rsids.append(rsid)
    return rsids


def extract_chromosomal_variants(variants: List[Dict]) -> List[Dict]:
    """
    Extract chromosomal position-based variant information

    Args:
        variants: List of variant dictionaries

    Returns:
        List of simplified variant data (chrom:pos:ref:alt format)
    """
    chrom_variants = []

    for variant in variants:
        chrom_var = {
            "chromosome": variant.get('chromosome'),
            "position": variant.get('position'),
            "ref": variant.get('ref'),
            "alt": variant.get('alt'),
            "rsid": variant.get('rsid'),
            "genotype": variant.get('genotype')
        }
        chrom_variants.append(chrom_var)

    return chrom_variants


def parse_vcf_from_file(filepath: str) -> Dict:
    """
    Parse VCF file from file path

    Args:
        filepath: Path to VCF file

    Returns:
        Parsed VCF data dictionary
    """
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        return parse_vcf_file(content)
    except Exception as e:
        return {
            "error": str(e),
            "metadata": {},
            "variants": []
        }
