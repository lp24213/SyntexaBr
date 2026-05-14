"""
VEREDA / SYNTEXA — Multimodal Engine
======================================
Engine multimodal soberana com:
- Vision runtime
- OCR runtime
- Audio runtime
- Document runtime
- Multimodal fusion
"""

from .vision_engine import VisionEngine
from .ocr_engine import OCREngine
from .audio_engine import AudioEngine
from .document_engine import DocumentEngine
from .fusion_engine import MultimodalFusionEngine

__all__ = [
    "VisionEngine",
    "OCREngine",
    "AudioEngine",
    "DocumentEngine",
    "MultimodalFusionEngine",
]
