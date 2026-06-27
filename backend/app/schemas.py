from pydantic import BaseModel, Field
from typing import List, Optional


class EditRequest(BaseModel):
    image_b64: str
    instruction: str
    seed: int = 42


class EditResponse(BaseModel):
    image_b64: str


class ABRequest(BaseModel):
    image_b64: str
    base_instruction: str          # appended after each finish, e.g. "keep everything else unchanged"
    finishes: List[str]            # full finish instruction strings, one per variant
    labels: Optional[List[str]] = None  # display labels; if None, finishes strings are used as labels
    seed: int = 42


class ABResult(BaseModel):
    label: str
    image_b64: str


class ABResponse(BaseModel):
    results: List[ABResult]


class LayerRequest(BaseModel):
    image_b64: str
    steps: List[str]
    seed: int = 42


class LayerStep(BaseModel):
    instruction: str
    image_b64: str


class LayerResponse(BaseModel):
    final_b64: str
    steps: List[LayerStep]


class ExportSelection(BaseModel):
    label: str
    image_b64: str


class ExportRequest(BaseModel):
    original_b64: str
    selections: List[ExportSelection]
    final_b64: Optional[str] = None


class ExportResponse(BaseModel):
    html: str


# --- Structural / experimental ---

class RemoveRequest(BaseModel):
    image_b64: str
    target: str
    seed: int = 42


class RemoveResponse(BaseModel):
    image_b64: str


class MoveRequest(BaseModel):
    image_b64: str
    target: str
    destination: str
    seed: int = 42


class MoveResponse(BaseModel):
    image_b64: str
    approximate: bool = True


class OpenWallRequest(BaseModel):
    image_b64: str
    wall_description: str
    seed: int = 42


class OpenWallResponse(BaseModel):
    image_b64: str
    invented_space: bool = True
