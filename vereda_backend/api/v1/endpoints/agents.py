from typing import Any, Dict

from fastapi import APIRouter, Depends

from vereda_backend.ai_runtime import agent_system
from vereda_backend.core.security import get_current_admin


router = APIRouter(prefix="/agents")


@router.post("/plan_and_execute")
def plan_and_execute(
    prompt: str, _: Any = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Usa o AgentSystem para decompor a tarefa, executar etapas e retornar o plano completo.
    """
    result = agent_system.handle_request(prompt)
    return {
        "plan": result.plan,
        "steps": result.steps,
        "outputs": result.outputs,
    }

