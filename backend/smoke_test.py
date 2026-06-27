"""
Smoke test — run without a GPU or model weights.
Validates that all imports, config paths, and JSON files load correctly.

  cd backend
  .venv/Scripts/python smoke_test.py
"""
import sys, json
from pathlib import Path

errors = []

# 1. Core web framework imports
try:
    import fastapi, uvicorn, pydantic, PIL
    print(f"  fastapi {fastapi.__version__}  uvicorn {uvicorn.__version__}  "
          f"pydantic {pydantic.__version__}  Pillow {PIL.__version__}")
except ImportError as e:
    errors.append(f"web framework import failed: {e}")

# 2. App module imports (no torch / diffusers needed)
sys.path.insert(0, str(Path(__file__).parent))
try:
    from app import config
    from app.schemas import EditRequest, ABRequest, LayerRequest
    print(f"  config OK — MODELS_DIR={config.MODELS_DIR}")
    print(f"  schemas OK")
except Exception as e:
    errors.append(f"app import failed: {e}")

# 3. JSON presets
try:
    finishes = json.loads(config.FINISHES_JSON.read_text())
    cats = list(finishes.keys())
    total = sum(len(v) for v in finishes.values())
    print(f"  finishes.json OK — {len(cats)} categories, {total} presets: {cats}")
except Exception as e:
    errors.append(f"finishes.json failed: {e}")

try:
    structural = json.loads(config.STRUCTURAL_JSON.read_text())
    print(f"  structural.json OK — keys: {list(structural.keys())}")
except Exception as e:
    errors.append(f"structural.json failed: {e}")

# 4. .gitignore sanity — models/ must be excluded
gi = Path(__file__).parents[1] / ".gitignore"
if gi.exists():
    content = gi.read_text()
    for pattern in ["models/", "*.safetensors", ".env", "__pycache__"]:
        if pattern not in content:
            errors.append(f".gitignore missing: {pattern}")
    print(f"  .gitignore OK")

if errors:
    print("\nFAILED:")
    for e in errors:
        print(f"  ✗ {e}")
    sys.exit(1)
else:
    print("\nAll smoke tests passed.")
