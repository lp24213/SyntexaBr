import subprocess
import tempfile
from pathlib import Path


class CodeExecutor:
    """
    Execução de código em sandbox leve.
    IMPORTANTE: para produção, substitua por sandbox reforçada (Docker, firejail, etc).
    """

    def run_python(self, code: str, timeout_s: int = 5) -> str:
        with tempfile.TemporaryDirectory() as tmpdir:
            file = Path(tmpdir) / "main.py"
            file.write_text(code, encoding="utf-8")
            proc = subprocess.run(
                ["python", str(file)],
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
            return proc.stdout + proc.stderr

