from vereda_ai.ai.llm_engine import LLMEngine
from vereda_ai.core.logging import get_logger


logger = get_logger(__name__)


class ReasoningEngine:
    """
    Camada de raciocínio: usa LLM + ferramentas para resolver problemas complexos.
    """

    def __init__(self, llm: LLMEngine):
        self.llm = llm

    def solve(self, prompt: str) -> str:
        messages = [
            {
                "role": "system",
                "content": (
                    "Você é um engenheiro e cientista especialista em matemática, "
                    "física, engenharia mecânica e elétrica."
                ),
            },
            {"role": "user", "content": prompt},
        ]
        logger.info("ReasoningEngine.solve chamado")
        return self.llm.chat(messages)

