import json
import sys
from pathlib import Path

# Add the apps/api directory to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from helix.main import app


def export():
    schema = app.openapi()
    # Write to root of apps/api for easy access
    output_path = Path(__file__).resolve().parent.parent / "openapi.json"
    output_path.write_text(json.dumps(schema, indent=2))

if __name__ == "__main__":
    export()
