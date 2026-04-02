class CodeValidator:
    """
    Validador simples de código: aplica filtros básicos antes da execução.
    """

    def is_safe_python(self, code: str) -> bool:
        banned = ["import os", "import sys", "subprocess", "shutil", "open(", "eval("]
        lowered = code.lower()
        return not any(bad in lowered for bad in banned)

