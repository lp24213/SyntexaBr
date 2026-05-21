from dataclasses import dataclass
from typing import Iterable


@dataclass
class CrawlDocument:
    url: str
    title: str
    text: str


def crawl_sources(urls: Iterable[str]) -> list[CrawlDocument]:
    """
    PROIBIDO retornar mock/placeholder (V38).
    Crawler autorizado deve executar fetch real.
    """
    raise RuntimeError(
        "[Syntexa V38] Crawler não possui implementação real de fetch. "
        "Nenhum fallback mock é permitido. Configure o runtime de crawling local."
    )
