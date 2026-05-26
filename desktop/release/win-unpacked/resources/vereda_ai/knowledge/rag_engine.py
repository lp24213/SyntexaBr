from vereda_ai.ai.llm_engine import LLMEngine
from vereda_ai.knowledge.vector_db import VectorDB


class RAGEngine:
    """
    Retrieval Augmented Generation: busca contexto em VectorDB e chama LLM.
    """

    def __init__(self, llm: LLMEngine, db: VectorDB):
        self.llm = llm
        self.db = db

    def answer(self, question: str, namespace: str = "scientific") -> str:
        docs = self.db.similarity_search(namespace=namespace, query=question, top_k=5)
        context = "\n\n".join(d.get("text", "") for d in docs)
        messages = [
            {
                "role": "system",
                "content": "Você é um assistente científico rigoroso.",
            },
            {
                "role": "user",
                "content": f"Contexto:\n{context}\n\nPergunta: {question}",
            },
        ]
        return self.llm.chat(messages)

