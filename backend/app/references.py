"""
Loads references.json and exposes the curated templates as module constants.

Mirrors how structural.py reads structural.json — the JSON is the single source
of truth for the prompt wording and caveats; this module just surfaces it as
Python dicts so routes.py and pipeline.py can import it.
"""
from __future__ import annotations

import json

from . import config

_data = json.loads(config.REFERENCES_JSON.read_text(encoding="utf-8"))

FINISH_REFERENCE_TEMPLATES: dict[str, str] = _data["finish_reference_templates"]
OBJECT_REFERENCE_TEMPLATES: dict[str, str] = _data["object_reference_templates"]
CAVEATS: dict[str, str] = _data["caveats"]
