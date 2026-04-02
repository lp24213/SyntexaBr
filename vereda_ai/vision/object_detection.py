from typing import Any, List


class ObjectDetection:
    """
    Stub para detecção de objetos em imagens.
    """

    def detect(self, image_bytes: bytes) -> List[dict[str, Any]]:
        raise NotImplementedError("Integre com YOLO, DETR ou modelo equivalente.")

