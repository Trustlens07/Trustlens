import os

structure = {
    "backend": {
        "app": {
            "__init__.py": "",
            "main.py": "",
            "config.py": "",
            "models": {
                "__init__.py": "",
                "resume.py": "",
                "scoring.py": "",
            },
            "services": {
                "__init__.py": "",
                "parser.py": "",
                "scorer.py": "",
                "explainer.py": "",
                "feedback.py": "",
            },
            "utils": {
                "__init__.py": "",
                "text_processor.py": "",
                "validators.py": "",
            },
            "api": {
                "__init__.py": "",
                "endpoints.py": "",
            },
        },
        "requirements.txt": "",
        ".env": "",
        "run.py": "",
    }
}

def create_structure(base, struct):
    for name, content in struct.items():
        path = os.path.join(base, name)
        if isinstance(content, dict):
            os.makedirs(path, exist_ok=True)
            create_structure(path, content)
        else:
            with open(path, "w") as f:
                f.write(content)

create_structure(".", structure)
print("✅ Project structure created!")