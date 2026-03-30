import os
import sys

def create_backend_structure():
    base_path = "backend"
    
    structure = {
        # Directories and their files
        "app/api/v1/endpoints": [
            "upload.py", "candidates.py", "scores.py", 
            "bias.py", "feedback.py", "reports.py"
        ],
        "app/api/v1/schemas": [
            "candidate.py", "score.py", "bias.py", 
            "feedback.py", "common.py"
        ],
        "app/core": [
            "config.py", "database.py", "security.py", "logging.py"
        ],
        "app/models": [
            "base.py", "candidate.py", "score.py", 
            "bias_metric.py", "feedback.py"
        ],
        "app/services": [
            "candidate_service.py", "score_service.py", 
            "bias_service.py", "feedback_service.py", 
            "storage_service.py", "ml_client.py"
        ],
        "app/orchestrators": [
            "upload_orchestrator.py", "scoring_orchestrator.py", 
            "report_orchestrator.py"
        ],
        "app/utils": [
            "file_validator.py", "pdf_parser.py", 
            "date_utils.py", "response_utils.py"
        ],
        "app/middlewares": [
            "error_handler.py", "request_logger.py", "rate_limiter.py"
        ],
        "app/tests/test_api": [
            "test_upload.py", "test_candidates.py", 
            "test_scores.py", "test_bias.py"
        ],
        "app/tests/test_services": [
            "test_score_service.py", "test_bias_service.py"
        ],
        "app/tests/test_integration": [
            "test_upload_flow.py"
        ],
        "migrations/versions": [],
        "scripts": [
            "seed_data.py", "cleanup_storage.py"
        ],
        "": [  # root directory
            ".env.example", ".gitignore", "Dockerfile",
            "requirements.txt", "requirements-dev.txt", 
            "alembic.ini", "README.md"
        ]
    }
    
    # Create all directories and files
    for dir_path, files in structure.items():
        full_dir_path = os.path.join(base_path, dir_path)
        
        # Create directory
        os.makedirs(full_dir_path, exist_ok=True)
        
        # Create __init__.py in all directories
        init_file = os.path.join(full_dir_path, "__init__.py")
        if not os.path.exists(init_file):
            open(init_file, 'a').close()
        
        # Create files
        for file in files:
            file_path = os.path.join(full_dir_path, file)
            if not os.path.exists(file_path):
                open(file_path, 'a').close()
                print(f"Created: {file_path}")
    
    # Create specific files that need content
    app_main = os.path.join(base_path, "app", "main.py")
    if not os.path.exists(app_main):
        with open(app_main, 'w') as f:
            f.write('"""FastAPI application entry point"""\n')
    
    api_router = os.path.join(base_path, "app", "api", "v1", "router.py")
    if not os.path.exists(api_router):
        with open(api_router, 'w') as f:
            f.write('"""API v1 router combining all endpoints"""\n')
    
    # Create migrations files
    migrations_env = os.path.join(base_path, "migrations", "env.py")
    if not os.path.exists(migrations_env):
        with open(migrations_env, 'w') as f:
            f.write('"""Alembic migration environment"""\n')
    
    print("\n✅ Backend structure created successfully!")
    print(f"📁 Location: {os.path.abspath(base_path)}")

if __name__ == "__main__":
    create_backend_structure()