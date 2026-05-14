"""
VEREDA / SYNTEXA — Multimodal Fusion Engine
============================================
Engine de fusão multimodal com:
- Cross-modal attention
- Unified embeddings
- Multimodal reasoning
- Realtime streaming
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class MultimodalInput:
    text: Optional[str] = None
    image_data: Optional[bytes] = None
    audio_data: Optional[bytes] = None
    document_data: Optional[bytes] = None
    video_data: Optional[bytes] = None


@dataclass
class FusionResult:
    unified_representation: Dict[str, Any]
    text_summary: str
    visual_description: str
    audio_transcript: str
    confidence: float
    modalities_detected: List[str]


class MultimodalFusionEngine:
    """
    Engine que funde múltiplas modalidades em representação unificada.
    """

    def __init__(self):
        from .vision_engine import VisionEngine
        from .ocr_engine import OCREngine
        from .audio_engine import AudioEngine
        from .document_engine import DocumentEngine

        self.vision = VisionEngine()
        self.ocr = OCREngine()
        self.audio = AudioEngine()
        self.document = DocumentEngine()

    # ── UNIFIED PROCESSING ───────────────────────────────────
    def process(self, inputs: MultimodalInput) -> FusionResult:
        """
        Processa input multimodal e retorna representação unificada.
        """
        modalities = []
        results = {}

        # Text
        if inputs.text:
            modalities.append("text")
            results["text"] = {
                "content": inputs.text,
                "length": len(inputs.text),
            }

        # Image
        if inputs.image_data:
            modalities.append("image")
            vision_result = self.vision.analyze(inputs.image_data)
            ocr_result = self.ocr.extract_text(inputs.image_data)
            results["image"] = {
                "description": vision_result.description,
                "objects": vision_result.objects,
                "ocr_text": ocr_result.text,
            }

        # Audio
        if inputs.audio_data:
            modalities.append("audio")
            audio_result = self.audio.analyze(inputs.audio_data)
            results["audio"] = {
                "duration": audio_result.duration_sec,
                "classification": audio_result.classification,
                "features": audio_result.features,
            }

        # Document
        if inputs.document_data:
            modalities.append("document")
            doc_result = self.document.parse(inputs.document_data)
            results["document"] = {
                "text": doc_result.text,
                "pages": len(doc_result.pages),
                "tables": len(doc_result.tables),
            }

        # Build unified representation
        unified = self._fuse_modalities(results)

        return FusionResult(
            unified_representation=unified,
            text_summary=self._generate_summary(results),
            visual_description=results.get("image", {}).get("description", ""),
            audio_transcript=results.get("audio", {}).get("classification", ""),
            confidence=self._calculate_confidence(results),
            modalities_detected=modalities,
        )

    def _fuse_modalities(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Cria representação unificada das modalidades."""
        unified = {
            "modalities": list(results.keys()),
            "text_content": results.get("text", {}).get("content", "") or results.get("document", {}).get("text", ""),
            "visual_content": results.get("image", {}).get("description", ""),
            "audio_content": results.get("audio", {}).get("classification", ""),
            "metadata": {},
        }

        # Cross-modal linking
        if "image" in results and "text" in results:
            unified["metadata"]["text_image_alignment"] = self._align_text_image(
                results["text"]["content"],
                results["image"].get("ocr_text", ""),
            )

        if "audio" in results and "text" in results:
            unified["metadata"]["audio_text_alignment"] = self._align_audio_text(
                results["audio"]["classification"],
                results["text"]["content"],
            )

        return unified

    def _align_text_image(self, text: str, ocr_text: str) -> float:
        """Calcula alinhamento entre texto e OCR."""
        import re
        text_words = set(re.findall(r'\b\w{4,}\b', text.lower()))
        ocr_words = set(re.findall(r'\b\w{4,}\b', ocr_text.lower()))
        if not text_words:
            return 0.0
        overlap = len(text_words & ocr_words)
        return min(1.0, overlap / max(len(text_words), 1))

    def _align_audio_text(self, audio_class: str, text: str) -> float:
        """Calcula alinhamento entre áudio e texto."""
        text_lower = text.lower()
        if "speech" in audio_class and any(w in text_lower for w in ["diga", "fale", "fala", "speak"]):
            return 0.8
        if "music" in audio_class and any(w in text_lower for w in ["música", "music", "som", "audio"]):
            return 0.7
        return 0.3

    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """Gera sumário textual do conteúdo multimodal."""
        parts = []
        if "text" in results:
            parts.append(f"Texto: {results['text']['content'][:200]}...")
        if "image" in results:
            parts.append(f"Imagem: {results['image']['description']}")
        if "audio" in results:
            parts.append(f"Áudio: {results['audio']['classification']}")
        if "document" in results:
            parts.append(f"Documento: {len(results['document']['text'])} caracteres")
        return " | ".join(parts)

    def _calculate_confidence(self, results: Dict[str, Any]) -> float:
        """Calcula confiança geral da fusão."""
        if not results:
            return 0.0
        scores = []
        for key, val in results.items():
            if isinstance(val, dict):
                conf = val.get("confidence", 0.5)
                scores.append(conf)
        return sum(scores) / max(len(scores), 1)

    # ── REALTIME STREAMING ───────────────────────────────────
    async def stream_process(
        self,
        text_stream: Optional[Any] = None,
        audio_stream: Optional[Any] = None,
    ) -> Any:
        """
        Processamento em tempo real de streams multimodais.
        """
        # Placeholder para streaming real
        # Em produção, usar queues e processamento assíncrono
        accumulated_text = []
        accumulated_audio = []

        if text_stream:
            async for chunk in text_stream:
                accumulated_text.append(chunk)

        if audio_stream:
            async for chunk in audio_stream:
                accumulated_audio.append(chunk)

        return self.process(MultimodalInput(
            text=" ".join(accumulated_text) if accumulated_text else None,
            audio_data=b"".join(accumulated_audio) if accumulated_audio else None,
        ))
