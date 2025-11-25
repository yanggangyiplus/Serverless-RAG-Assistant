# src/services/rag_service.py

"""
RAG Query Service
Streamlit, API, Lambda 어디서든 호출 가능하도록
RAG Retrieval + LLM 호출을 담당하는 Service Layer
"""

from typing import Dict

from src.rag.retriever import RAGRetriever
from src.rag.pipeline import RAGPipeline
from src.vectorstore.base import VectorStore
from src.embeddings.embedder import EmbeddingGenerator

from src.utils.logger import get_logger

logger = get_logger(__name__)


def process_rag_query(
    query: str,
    vector_store: VectorStore,
    embedding_generator: EmbeddingGenerator,
    top_k: int = 5
) -> Dict:
    """
    RAG 질의응답 서비스.
    
    Args:
        query: 사용자의 질문
        vector_store: 검색용 벡터 스토어
        embedding_generator: 임베딩 생성기
        top_k: 검색할 문서 수
    
    Returns:
        {
            "answer": str,
            "source_documents": List[Dict]
        }
    """

    logger.info(f"[RAG] Start query: {query}")

    # Retriever 생성
    retriever = RAGRetriever(
        vector_store=vector_store,
        embedding_generator=embedding_generator,
        k=top_k
    )

    # 파이프라인 생성
    pipeline = RAGPipeline(
        retriever=retriever,
        llm_provider="mock"  # 추후 'openai' 또는 'bedrock'으로 변경 가능
    )

    # 질의 수행
    return pipeline.query(query)
