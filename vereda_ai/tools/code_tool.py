# -*- coding: utf-8 -*-
"""Execução segura de snippets Python. Timeout e sandbox leve. Offline."""
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict

from vereda_ai.tools.base_tool import BaseTool


class CodeTool(BaseTool):
    name = "code"

    def run(self, code: str, timeout_seconds: int = 5, **kwargs: Any) -> Dict[str, Any]:
        """
        Executa snippet Python em processo isolado com timeout.
        Código malicioso deve ser bloqueado em produção (sandbox reforçada).
        """
        code = (code or "").strip()
        if not code:
            return {"ok": False, "error": "Código vazio."}
        if "import os" in code and "system" in code or "subprocess" in code and "shell" in code:
            return {"ok": False, "error": "Comandos de sistema não permitidos."}
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                fpath = Path(tmpdir) / "run.py"
                fpath.write_text(code, encoding="utf-8")
                proc = subprocess.run(
                    ["python", str(fpath)],
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    cwd=tmpdir,
                )
                out = (proc.stdout or "").strip()
                err = (proc.stderr or "").strip()
                return {
                    "ok": proc.returncode == 0,
                    "stdout": out,
                    "stderr": err,
                    "returncode": proc.returncode,
                }
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": f"Timeout após {timeout_seconds}s."}
        except Exception as e:
            return {"ok": False, "error": str(e)}
