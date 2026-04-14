import sys, pathlib, traceback

# Ensure project module imports work
sys.path.insert(0, 'PharmaGuard-HealthTech')

from backend.routes.analysis import analyze_drug
from backend.services.vcf_parser import parse_vcf_file
from backend.services.variant_matcher import match_all_target_genes
from backend.data.drug_gene_mapping import get_drug_genes

vcf_text = pathlib.Path('PharmaGuard-HealthTech/backend/sample_data/sample.vcf').read_text()
vcf_data = parse_vcf_file(vcf_text)
variants = vcf_data.get('variants', [])

# Build variants_by_gene
all_target_genes = set()
for drug in ['CODEINE']:
    genes = get_drug_genes(drug)
    all_target_genes.update(genes)

gene_matches = match_all_target_genes(variants, list(all_target_genes))
variants_by_gene = {g: m.get('matched_variants', []) for g, m in gene_matches.items()}

try:
    res = analyze_drug('CODEINE', variants_by_gene, 'PATIENT_TEST')
    print('Result:', res)
except Exception:
    traceback.print_exc()
