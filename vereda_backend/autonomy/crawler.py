from dataclasses import dataclass
from typing import Iterable


@dataclass
class CrawlDocument:
    url: str
    title: str
    text: str


def crawl_sources(urls: Iterable[str]) -> list[CrawlDocument]:
    """
    Placeholder de crawler autorizado (robots/compliance).
    """
    out: list[CrawlDocument] = []
    for u in urls:
        out.append(CrawlDocument(url=u, title="pending", text=""))
    return out
