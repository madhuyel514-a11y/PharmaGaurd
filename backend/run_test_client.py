import sys
import pathlib
import traceback

# Ensure project root is on sys.path so the backend package can be imported
BACKEND_DIR = pathlib.Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import create_app

# Create app and test client
app = create_app()
client = app.test_client()

# Load sample VCF
vcf_path = BACKEND_DIR / 'sample_data' / 'sample.vcf'
vcf_content = vcf_path.read_text(encoding='utf-8')

payload = {
    'vcf_file': vcf_content,
    'drugs': ['CODEINE']
}

try:
    resp = client.post('/api/analyze', json=payload)
    print('Status', resp.status_code)
    print('Data', resp.get_data(as_text=True))
except Exception as e:
    print('Exception during request:', e)
    traceback.print_exc()
