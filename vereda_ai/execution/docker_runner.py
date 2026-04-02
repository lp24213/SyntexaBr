from typing import List


class DockerRunner:
    """
    Stub para execução de código em containers Docker isolados.
    """

    def run_image(self, image: str, command: List[str], timeout_s: int = 10) -> str:
        # Em produção, chame `docker run` ou use SDK do Docker com limites de recursos.
        raise NotImplementedError("Integração real com Docker ainda não implementada.")

