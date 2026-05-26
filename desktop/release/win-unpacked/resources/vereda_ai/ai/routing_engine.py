from typing import Literal

from vereda_ai.ai.agent_system import AgentSystem, AgentResult
from vereda_ai.core.logging import get_logger


RouteType = Literal["chat", "science", "code", "agent"]

logger = get_logger(__name__)


class RoutingEngine:
    """
    Task router simples: decide qual subsistema deve tratar o pedido.
    """

    def __init__(self, agents: AgentSystem):
        self.agents = agents

    def route(self, user_input: str) -> tuple[RouteType, AgentResult]:
        # Por enquanto, sempre delega ao AgentSystem e marca tipo "agent".
        logger.info("RoutingEngine.route chamado")
        result = self.agents.handle_request(user_input)
        return "agent", result

