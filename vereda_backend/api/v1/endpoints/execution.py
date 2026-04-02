from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from vereda_backend.ai_runtime import code_validator, sandbox
from vereda_backend.core.security import get_current_admin


router = APIRouter(prefix="/execute")


@router.post("/code")
def execute_code(
    language: str,
    code: str,
    _: Any = Depends(get_current_admin),
) -> Dict[str, Any]:
    """
    Executa código em sandbox leve. Por segurança, apenas Python é permitido por enquanto.
    """
    if language != "python":
        raise HTTPException(status_code=400, detail="Apenas Python é suportado neste endpoint.")

    if not code_validator.is_safe_python(code):
        raise HTTPException(
            status_code=400,
            detail="Código rejeitado pelo validador de segurança.",
        )

    output = sandbox.run(language="python", code=code, timeout_s=5)
    return {"ok": True, "language": language, "output": output}

