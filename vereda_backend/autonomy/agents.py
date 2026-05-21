from dataclasses import dataclass


@dataclass
class AgentTask:
    name: str
    payload: dict


def run_agent(task: AgentTask) -> dict:
    """
    PROIBIDO retornar mock/placeholder (V38).
    Executor de agente deve usar runtime real.
    """
    raise RuntimeError(
        f"[Syntexa V38] Agente '{task.name}' não possui executor real implementado. "
        "Nenhum fallback mock é permitido. Configure o runtime de agentes local."
    )
