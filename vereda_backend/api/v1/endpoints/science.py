from typing import Any, Dict

from fastapi import APIRouter, Depends

from vereda_backend.core.security import get_current_admin
from vereda_backend.ai_runtime import engineering_engine, math_engine, physics_engine


router = APIRouter(prefix="/science")


@router.post("/math/symbolic")
def math_symbolic(
    expr: str, subs: Dict[str, float] | None = None, _: Any = Depends(get_current_admin)
) -> Dict[str, Any]:
    result = math_engine.symbolic.eval_expression(expr, subs=subs or {})
    return {"ok": True, "expr": expr, "result": result}


@router.post("/physics/newton")
def physics_newton(
    mass: float, acceleration: float, _: Any = Depends(get_current_admin)
) -> Dict[str, Any]:
    force = physics_engine.newton_second_law(mass, acceleration)
    return {"ok": True, "force": force}


@router.post("/engineering/beam")
def engineering_beam(
    length: float,
    load: float,
    e_modulus: float,
    inertia: float,
    _: Any = Depends(get_current_admin),
) -> Dict[str, Any]:
    res = engineering_engine.cantilever_beam_point_load(
        length=length, load=load, e_modulus=e_modulus, inertia=inertia
    )
    return {
        "ok": True,
        "length": length,
        "load": load,
        "max_moment": res.max_moment,
        "max_deflection": res.max_deflection,
    }

