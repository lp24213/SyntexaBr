from typing import Any, Dict

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.orm import Session

from vereda_backend.core.security import get_current_admin
from vereda_backend.db.session import get_db
from vereda_backend.services.tools import analyze_image_basic, evaluate_math_expression


router = APIRouter(prefix="/tools")


@router.post("/math")
def math_evaluate(expr: str = Form(...)) -> Dict[str, Any]:
    """
    Avalia expressões matemáticas simbólicas usando SymPy.
    Ex: 2+2, sin(pi/3), (2*x+1)**2 com x=...
    (Para segurança, não executa código arbitrário Python.)
    """
    return evaluate_math_expression(expr)


@router.post("/image/analyze")
async def image_analyze(
    file: UploadFile = File(...),
    _: Any = Depends(get_current_admin),
) -> Dict[str, Any]:
    """
    Análise básica de imagem (resolução e cor média).
    Restrito a admin.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Envie um arquivo de imagem.")
    return analyze_image_basic(file)


@router.post("/sql")
def sql_query(
    query: str = Form(...),
    db: Session = Depends(get_db),
    _: Any = Depends(get_current_admin),
) -> Dict[str, Any]:
    """
    Execução de consultas SQL somente-LEITURA na base da Syntexa.
    Apenas SELECT é permitido, para evitar destruição de dados.
    """
    stripped = query.lstrip().upper()
    if not stripped.startswith("SELECT"):
        raise HTTPException(
            status_code=400,
            detail="Apenas consultas SELECT são permitidas neste endpoint.",
        )

    result = db.execute(text(query))
    rows = [dict(row._mapping) for row in result]
    return {"ok": True, "rows": rows}

