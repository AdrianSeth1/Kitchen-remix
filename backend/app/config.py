from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[2]  # kitchen-remix/

MODELS_DIR = ROOT / "models"
SAMPLES_DIR = ROOT / "samples"
FINISHES_JSON = Path(__file__).parent / "finishes.json"
STRUCTURAL_JSON = Path(__file__).parent / "structural.json"
REFERENCES_JSON = Path(__file__).parent / "references.json"

HF_TOKEN = os.getenv("HF_TOKEN", "")

# Model identifiers — verify against HF before loading
KONTEXT_MODEL_ID = "black-forest-labs/FLUX.1-Kontext-dev"
QWEN_MODEL_ID = "Qwen/Qwen-Image-Edit-2509"

DEFAULT_SEED = 42
DEFAULT_WIDTH = 1024
DEFAULT_HEIGHT = 1024
NUM_INFERENCE_STEPS = 28
GUIDANCE_SCALE = 2.5
QWEN_NUM_INFERENCE_STEPS = 28
QWEN_GUIDANCE_SCALE = 7.5

# fp8-quantize the FLUX transformer to ~12 GB (vs ~24 GB) so it fits a 24 GB card
# with headroom — no spill into shared system RAM, much faster. Needs optimum-quanto.
# Set USE_FP8=0 in the environment to fall back to full bf16.
USE_FP8 = os.getenv("USE_FP8", "1") != "0"
