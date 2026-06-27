from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[2]  # kitchen-remix/

MODELS_DIR = ROOT / "models"
SAMPLES_DIR = ROOT / "samples"
FINISHES_JSON = Path(__file__).parent / "finishes.json"
STRUCTURAL_JSON = Path(__file__).parent / "structural.json"

HF_TOKEN = os.getenv("HF_TOKEN", "")

# Model identifiers — verify against HF before loading
KONTEXT_MODEL_ID = "black-forest-labs/FLUX.1-Kontext-dev"

DEFAULT_SEED = 42
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 1024
NUM_INFERENCE_STEPS = 28
GUIDANCE_SCALE = 2.5
