"""
RAG Retriever (LangChain 최신 버전 완전 호환)
"""

from typing import List
from langchain_core.documents import Document

from src.vectorstore.base import VectorStore
from src.embeddings.embedder import EmbeddingGenerator
from src.utils.logger import get_logger

logger = get_logger(__name__)


class RAGRetriever:
    """
    LangChain 최신버전(0.1 ~ 0.2.x ~ 1.0까지)에서 완전히 동작하는 커스텀 Retriever
    BaseRetriever 상속 절대 금지 (Pydantic 필드 충돌 때문)
    """

    def __init__(self, vector_store: VectorStore, embedding_generator: EmbeddingGenerator, k: int = 5):
        self.vector_store = vector_store
        self.embedding_generator = embedding_generator
        self.k = k

    def get_relevant_documents(self, query: str) -> List[Document]:
        """LangChain Retriever에서 호출하는 핵심 메서드"""

        if self.vector_store is None or self.embedding_generator is None:
            logger.error("Retriever not initialized.")
            return []

        # 쿼리 임베딩 생성
        query_embedding = self.embedding_generator.embed_text(query)

        # 유사도 검색
        docs = self.vector_store.similarity_search(query_embedding, k=self.k)

        # LangChain Document 변환
        results = []
        for d in docs:
            results.append(
                Document(
                    page_content=d.text,
                    metadata={
                        **d.metadata,
                        "document_id": d.document_id,
                        "chunk_id": d.chunk_id,
                    }
                )
            )

        return results

    # 비동기 버전 (필수 아님, 있어도 무방)
    async def aget_relevant_documents(self, query: str) -> List[Document]:
        return self.get_relevant_documents(query)
