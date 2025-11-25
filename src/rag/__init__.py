"""
RAG 모듈
Retriever, RAG Pipeline 구현
"""

# LangChain 의존성이 있는 모듈은 선택적 import
try:
    from .retriever import RAGRetriever
    from .pipeline import RAGPipeline
    __all__ = ["RAGRetriever", "RAGPipeline"]
except ImportError as e:
    # LangChain이 없는 경우 None으로 설정
    RAGRetriever = None
    RAGPipeline = None
    __all__ = []

