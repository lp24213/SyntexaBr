"""
VEREDA / SYNTEXA — Vision Engine
=================================
Engine de visão computacional com:
- Image classification
- Object detection
- Scene understanding
- Visual QA
"""

import base64
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import torch
    from torchvision import transforms
    TORCHVISION_AVAILABLE = True
except ImportError:
    TORCHVISION_AVAILABLE = False

log = logging.getLogger(__name__)


@dataclass
class VisionResult:
    description: str
    objects: List[Dict[str, Any]]
    scene_type: str
    confidence: float
    metadata: Dict[str, Any]


class VisionEngine:
    """
    Engine de visão para análise de imagens.
    """

    def __init__(self, model_name: str = "resnet50"):
        self.model_name = model_name
        self._model = None
        self._transform = None
        self._labels = self._load_labels()

        if TORCHVISION_AVAILABLE:
            self._init_model()

    def _init_model(self) -> None:
        try:
            import torchvision.models as models
            if self.model_name == "resnet50":
                self._model = models.resnet50(pretrained=True)
            elif self.model_name == "mobilenet":
                self._model = models.mobilenet_v2(pretrained=True)
            else:
                self._model = models.resnet18(pretrained=True)

            self._model.eval()
            self._transform = transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ])
            log.info("Vision model loaded: %s", self.model_name)
        except Exception as e:
            log.error("Failed to load vision model: %s", e)
            self._model = None

    def _load_labels(self) -> List[str]:
        # ImageNet 1000 classes (subset)
        return [
            "tench", "goldfish", "great_white_shark", "tiger_shark", "hammerhead",
            "electric_ray", "stingray", "cock", "hen", "ostrich",
            "brambling", "goldfinch", "house_finch", "junco", "indigo_bunting",
            "robin", "bulbul", "jay", "magpie", "chickadee",
            "water_ouzel", "kite", "bald_eagle", "vulture", "great_grey_owl",
            "fire_salamander", "salamander", "newt", "spotted_salamander", "axolotl",
            "bullfrog", "tree_frog", "tailed_frog", "loggerhead", "leatherback_turtle",
            "mud_turtle", "terrapin", "box_turtle", "banded_gecko", "common_iguana",
            "American_chameleon", "whiptail", "agama", "frilled_lizard", "alligator_lizard",
            "Gila_monster", "green_lizard", "African_chameleon", "Komodo_dragon", "African_crocodile",
            # ... (truncado para brevidade)
            "person", "dog", "cat", "car", "bus", "truck", "motorcycle", "bicycle",
            "traffic_light", "fire_hydrant", "stop_sign", "parking_meter", "bench",
            "bird", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe",
            "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis",
            "snowboard", "sports_ball", "kite", "baseball_bat", "baseball_glove",
            "skateboard", "surfboard", "tennis_racket", "bottle", "wine_glass", "cup",
            "fork", "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
            "broccoli", "carrot", "hot_dog", "pizza", "donut", "cake", "chair", "couch",
            "potted_plant", "bed", "dining_table", "toilet", "tv", "laptop", "mouse",
            "remote", "keyboard", "cell_phone", "microwave", "oven", "toaster", "sink",
            "refrigerator", "book", "clock", "vase", "scissors", "teddy_bear", "hair_drier",
            "toothbrush",
        ]

    # ── IMAGE ANALYSIS ───────────────────────────────────────
    def analyze(self, image_data: bytes) -> VisionResult:
        """
        Analisa imagem e retorna descrição estruturada.
        """
        if not PIL_AVAILABLE:
            return self._fallback_result()

        try:
            img = Image.open(__import__('io').BytesIO(image_data))
            return self._analyze_image(img)
        except Exception as e:
            log.error("Image analysis failed: %s", e)
            return self._fallback_result()

    def analyze_base64(self, image_base64: str) -> VisionResult:
        """Analisa imagem em base64."""
        image_data = base64.b64decode(image_base64)
        return self.analyze(image_data)

    def _analyze_image(self, img: Any) -> VisionResult:
        if TORCHVISION_AVAILABLE and self._model is not None and self._transform is not None:
            return self._analyze_with_model(img)
        return self._analyze_heuristic(img)

    def _analyze_with_model(self, img: Any) -> VisionResult:
        import torch
        input_tensor = self._transform(img).unsqueeze(0)

        with torch.no_grad():
            outputs = self._model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs[0], dim=0)
            top5_prob, top5_idx = torch.topk(probabilities, 5)

        objects = []
        for i in range(min(5, len(top5_idx))):
            idx = top5_idx[i].item()
            label = self._labels[idx] if idx < len(self._labels) else f"class_{idx}"
            objects.append({
                "label": label,
                "confidence": round(top5_prob[i].item(), 4),
            })

        top_label = objects[0]["label"] if objects else "unknown"
        return VisionResult(
            description=f"Imagem contém: {top_label}",
            objects=objects,
            scene_type=self._infer_scene_type(objects),
            confidence=objects[0]["confidence"] if objects else 0.0,
            metadata={"width": img.width, "height": img.height, "mode": img.mode},
        )

    def _analyze_heuristic(self, img: Any) -> VisionResult:
        """Análise heurística quando modelo não disponível."""
        width, height = img.width, img.height
        aspect = width / max(height, 1)

        scene = "landscape" if aspect > 1.3 else "portrait" if aspect < 0.7 else "square"

        return VisionResult(
            description=f"Imagem de dimensões {width}x{height} ({scene})",
            objects=[{"label": "image", "confidence": 1.0}],
            scene_type=scene,
            confidence=0.5,
            metadata={"width": width, "height": height},
        )

    def _infer_scene_type(self, objects: List[Dict[str, Any]]) -> str:
        labels = [obj["label"] for obj in objects]
        if any(l in labels for l in ["person", "dog", "cat", "horse", "sheep"]):
            return "living_scene"
        if any(l in labels for l in ["car", "bus", "truck", "traffic_light"]):
            return "urban"
        if any(l in labels for l in ["bird", "tree", "mountain", "lake", "beach"]):
            return "nature"
        if any(l in labels for l in ["laptop", "keyboard", "cell_phone", "tv"]):
            return "indoor"
        return "general"

    def _fallback_result(self) -> VisionResult:
        return VisionResult(
            description="Análise de imagem não disponível (PIL não instalado)",
            objects=[],
            scene_type="unknown",
            confidence=0.0,
            metadata={},
        )

    # ── VISUAL QA ────────────────────────────────────────────
    def visual_qa(self, image_data: bytes, question: str) -> Dict[str, Any]:
        """
        Responde pergunta sobre imagem.
        """
        analysis = self.analyze(image_data)

        # Simple keyword matching for VQA
        q_lower = question.lower()
        if "quem" in q_lower or "who" in q_lower:
            people = [o for o in analysis.objects if o["label"] == "person"]
            return {"answer": f"Pessoa detectada com confiança {people[0]['confidence']:.2f}" if people else "Nenhuma pessoa detectada"}
        elif "o que" in q_lower or "what" in q_lower:
            return {"answer": analysis.description}
        elif "onde" in q_lower or "where" in q_lower:
            return {"answer": f"Cena do tipo: {analysis.scene_type}"}
        else:
            return {"answer": analysis.description}
