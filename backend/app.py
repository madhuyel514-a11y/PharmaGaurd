from flask import Flask
from flask_cors import CORS
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Allow `python backend/app.py` and `python app.py` from the backend folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv()

def create_app():
    """Flask app factory"""
    app = Flask(__name__)

    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_VCF_FILE_SIZE', 5242880))  # 5MB

    # Enable CORS for React frontend
    CORS(app, resources={r"/api/*": {"origins": os.getenv('FRONTEND_URL', '*')}})

    # Register blueprints
    from backend.routes.health import health_bp
    from backend.routes.analysis import analysis_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(analysis_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
