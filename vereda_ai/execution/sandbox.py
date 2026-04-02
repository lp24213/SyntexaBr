import subprocess
import tempfile
from pathlib import Path
from typing import List


class Sandbox:
    """
    Sandbox genérica para executar código em linguagens diferentes.
    Esta implementação é apenas ilustrativa; para produção use containers isolados.
    """

    def run(
        self, language: str, code: str, timeout_s: int = 5, args: List[str] | None = None
    ) -> str:
        if language == "python":
            return self._run_python(code, timeout_s, args or [])
        raise NotImplementedError(f"Linguagem não suportada: {language}")

    def _run_python(self, code: str, timeout_s: int, args: List[str]) -> str:
        with tempfile.TemporaryDirectory() as tmpdir:
            file = Path(tmpdir) / "main.py"
            file.write_text(code, encoding="utf-8")
            proc = subprocess.run(
                ["python", str(file), *args],
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
            return proc.stdout + proc.stderr

