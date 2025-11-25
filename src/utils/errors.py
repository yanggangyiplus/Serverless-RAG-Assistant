"""
공통 예외 클래스 정의
RAG 서비스 전반에서 사용하는 커스텀 예외
"""


class RAGBaseError(Exception):
    """기본 예외 클래스"""
    
    def __init__(self, message: str, error_code: str = None):
        """
        예외 초기화
        
        Args:
            message: 에러 메시지
            error_code: 에러 코드 (선택사항)
        """
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class IngestionError(RAGBaseError):
    """문서 수집 관련 예외"""
    pass


class S3HandlerError(IngestionError):
    """S3 핸들러 오류"""
    pass


class DocumentParsingError(IngestionError):
    """문서 파싱 오류"""
    pass


class PreprocessingError(RAGBaseError):
    """전처리 관련 예외"""
    pass


class TextCleaningError(PreprocessingError):
    """텍스트 정제 오류"""
    pass


class ChunkingError(PreprocessingError):
    """문서 청킹 오류"""
    pass


class EmbeddingError(RAGBaseError):
    """임베딩 생성 관련 예외"""
    pass


class EmbeddingModelError(EmbeddingError):
    """임베딩 모델 오류"""
    pass


class VectorStoreError(RAGBaseError):
    """벡터 스토어 관련 예외"""
    pass


class VectorStoreConnectionError(VectorStoreError):
    """벡터 스토어 연결 오류"""
    pass


class VectorStoreQueryError(VectorStoreError):
    """벡터 스토어 쿼리 오류"""
    pass


class RAGPipelineError(RAGBaseError):
    """RAG 파이프라인 관련 예외"""
    pass


class RetrieverError(RAGPipelineError):
    """Retriever 오류"""
    pass


class LLMError(RAGPipelineError):
    """LLM 관련 오류"""
    pass


class ConfigurationError(RAGBaseError):
    """설정 관련 예외"""
    pass

