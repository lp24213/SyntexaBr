from vereda_ai.core.logging import get_logger


logger = get_logger(__name__)


def on_startup() -> None:
    """
    Eventos globais de startup da plataforma de IA (inicialização de caches,
    conexão com VectorDB, aquecimento de modelos, etc).
    Por enquanto apenas registra a inicialização.
    """
    logger.info("Syntexa Ultra AI inicializando (eventos globais).")


def on_shutdown() -> None:
    """
    Eventos globais de shutdown (fechamento de conexões, flush de métricas, etc).
    """
    logger.info("Syntexa Ultra AI finalizando.")

