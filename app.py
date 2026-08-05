"""Render entrypoint for monorepo root deployments.

This wrapper loads the Flask app defined in diligencia-elite-rj/app.py
so services configured at repository root can run with `gunicorn app:app`.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
TARGET_DIR = BASE_DIR / "diligencia-elite-rj"
TARGET_APP = TARGET_DIR / "app.py"

# Add the target directory to sys.path so imports work correctly
sys.path.insert(0, str(TARGET_DIR))

spec = importlib.util.spec_from_file_location("diligencia_app", TARGET_APP)
if spec is None or spec.loader is None:
    raise RuntimeError(f"Unable to load Flask app module from {TARGET_APP}")

module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

app = module.app
app.template_folder = str(BASE_DIR / "diligencia-elite-rj" / "templates")
app.static_folder = str(BASE_DIR / "diligencia-elite-rj" / "static")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
