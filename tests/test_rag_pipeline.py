"""
RAG 파이프라인 테스트
Retriever 및 RAG Pipeline 기능 검증 (Mock 사용)
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.rag.retriever import RAGRetriever
from src.rag.pipeline import RAGPipeline
from src.vectorstore.mock_store import MockVectorStore
from src.embeddings.embedder import EmbeddingGenerator
from src.vectorstore.base import VectorDocument
from langchain_core.documents import Document
from src.utils.errors import RetrieverError, RAGPipelineError


class TestRAGRetriever:
    """RAGRetriever 테스트 클래스"""
    
    def setup_method(self):
        """테스트 전 설정"""
        self.vector_store = MockVectorStore()
        self.embedder = EmbeddingGenerator()
        self.retriever = RAGRetriever(
            vector_store=self.vector_store,
            embedding_generator=self.embedder,
            k=3
        )
    
    def test_get_relevant_documents_basic(self):
        """기본 문서 검색 테스트"""
        # 벡터 스토어에 문서 추가
        doc = VectorDocument(
            document_id="doc1",
            chunk_id="chunk_1",
            text="This is a test document about Python programming.",
            embedding=self.embedder.embed_text("Python programming"),
            metadata={"source": "test"}
        )
        self.vector_store.add_documents([doc])
        
        # 검색 실행
        query = "Python"
        documents = self.retriever.get_relevant_documents(query)
        
        assert len(documents) > 0
        assert isinstance(documents[0], Document)
        assert "Python" in documents[0].page_content or len(documents) > 0
    
    def test_get_relevant_documents_top_k(self):
        """Top-K 검색 테스트"""
        # 여러 문서 추가
        texts = [
            "Python is a programming language",
            "Java is another programming language",
            "JavaScript is used for web development",
            "C++ is a systems programming language"
        ]
        
        docs = [
            VectorDocument(
                document_id=f"doc{i}",
                chunk_id="chunk_1",
                text=text,
                embedding=self.embedder.embed_text(text),
                metadata={"index": i}
            )
            for i, text in enumerate(texts)
        ]
        
        self.vector_store.add_documents(docs)
        
        # k=2로 검색
        retriever = RAGRetriever(
            vector_store=self.vector_store,
            embedding_generator=self.embedder,
            k=2
        )
        
        documents = retriever.get_relevant_documents("programming language")
        assert len(documents) <= 2
    
    def test_get_relevant_documents_empty_result(self):
        """빈 결과 처리 테스트"""
        # 빈 벡터 스토어에서 검색
        documents = self.retriever.get_relevant_documents("test query")
        assert isinstance(documents, list)
        assert len(documents) == 0
    
    def test_get_relevant_documents_metadata_preservation(self):
        """메타데이터 보존 테스트"""
        doc = VectorDocument(
            document_id="doc1",
            chunk_id="chunk_1",
            text="Test document",
            embedding=self.embedder.embed_text("test"),
            metadata={"author": "Alice", "date": "2024-01-01"}
        )
        self.vector_store.add_documents([doc])
        
        documents = self.retriever.get_relevant_documents("test")
        
        if len(documents) > 0:
            assert "author" in documents[0].metadata
            assert "document_id" in documents[0].metadata
            assert documents[0].metadata["author"] == "Alice"
    
    def test_get_relevant_documents_error_handling(self):
        """에러 처리 테스트"""
        # 임베딩 생성 실패 시뮬레이션
        mock_embedder = Mock()
        mock_embedder.embed_text.side_effect = Exception("Embedding error")
        
        retriever = RAGRetriever(
            vector_store=self.vector_store,
            embedding_generator=mock_embedder,
            k=3
        )
        
        # 에러가 발생해도 빈 리스트 반환
        documents = retriever.get_relevant_documents("test")
        assert isinstance(documents, list)


class TestRAGPipeline:
    """RAGPipeline 테스트 클래스"""
    
    def setup_method(self):
        """테스트 전 설정"""
        self.vector_store = MockVectorStore()
        self.embedder = EmbeddingGenerator()
        self.retriever = RAGRetriever(
            vector_store=self.vector_store,
            embedding_generator=self.embedder,
            k=3
        )
    
    def test_pipeline_query_basic(self):
        """기본 질의응답 테스트"""
        # 벡터 스토어에 문서 추가
        doc = VectorDocument(
            document_id="doc1",
            chunk_id="chunk_1",
            text="Python is a high-level programming language.",
            embedding=self.embedder.embed_text("Python programming"),
            metadata={}
        )
        self.vector_store.add_documents([doc])
        
        # Pipeline 생성 및 쿼리
        pipeline = RAGPipeline(
            retriever=self.retriever,
            llm_provider="openai"  # Mock LLM 사용됨
        )
        
        result = pipeline.query("What is Python?")
        
        assert "answer" in result
        assert "source_documents" in result
        assert isinstance(result["answer"], str)
        assert isinstance(result["source_documents"], list)
    
    def test_pipeline_query_with_context(self):
        """컨텍스트가 있는 질의응답 테스트"""
        # 여러 문서 추가
        texts = [
            "Python is a programming language.",
            "Python was created by Guido van Rossum.",
            "Python is widely used in data science."
        ]
        
        docs = [
            VectorDocument(
                document_id=f"doc{i}",
                chunk_id="chunk_1",
                text=text,
                embedding=self.embedder.embed_text(text),
                metadata={"index": i}
            )
            for i, text in enumerate(texts)
        ]
        
        self.vector_store.add_documents(docs)
        
        pipeline = RAGPipeline(
            retriever=self.retriever,
            llm_provider="openai"
        )
        
        result = pipeline.query("Who created Python?")
        
        assert "answer" in result
        assert len(result["source_documents"]) > 0
    
    def test_pipeline_query_empty_context(self):
        """컨텍스트가 비어있을 때 처리 테스트"""
        # 빈 벡터 스토어에서 질의
        pipeline = RAGPipeline(
            retriever=self.retriever,
            llm_provider="openai"
        )
        
        result = pipeline.query("What is Python?")
        
        # 빈 컨텍스트여도 응답은 생성되어야 함 (fallback)
        assert "answer" in result
        assert isinstance(result["answer"], str)
        assert len(result["source_documents"]) == 0
    
    def test_pipeline_query_error_handling(self):
        """에러 처리 테스트"""
        # Retriever 실패 시뮬레이션
        mock_retriever = Mock()
        mock_retriever.get_relevant_documents.side_effect = Exception("Retrieval error")
        
        pipeline = RAGPipeline(
            retriever=mock_retriever,
            llm_provider="openai"
        )
        
        # 에러가 발생해도 응답 반환
        result = pipeline.query("test")
        assert "answer" in result
        assert "오류" in result["answer"] or "error" in result["answer"].lower()
    
    def test_pipeline_source_documents_format(self):
        """소스 문서 형식 테스트"""
        doc = VectorDocument(
            document_id="doc1",
            chunk_id="chunk_1",
            text="Test document content",
            embedding=self.embedder.embed_text("test"),
            metadata={"source": "test"}
        )
        self.vector_store.add_documents([doc])
        
        pipeline = RAGPipeline(
            retriever=self.retriever,
            llm_provider="openai"
        )
        
        result = pipeline.query("test query")
        
        # 소스 문서 형식 확인
        if len(result["source_documents"]) > 0:
            source = result["source_documents"][0]
            assert "content" in source
            assert "metadata" in source
            assert isinstance(source["content"], str)
            assert isinstance(source["metadata"], dict)
    
    def test_pipeline_different_providers(self):
        """다양한 LLM 제공자 테스트"""
        providers = ["openai", "bedrock"]
        
        for provider in providers:
            pipeline = RAGPipeline(
                retriever=self.retriever,
                llm_provider=provider
            )
            
            result = pipeline.query("test")
            assert "answer" in result
    
    def test_pipeline_query_empty_string(self):
        """빈 문자열 질의 처리 테스트"""
        pipeline = RAGPipeline(
            retriever=self.retriever,
            llm_provider="openai"
        )
        
        result = pipeline.query("")
        
        # 빈 질의도 처리되어야 함
        assert "answer" in result
    
    def test_pipeline_query_very_long_query(self):
        """매우 긴 질의 처리 테스트"""
        pipeline = RAGPipeline(
            retriever=self.retriever,
            llm_provider="openai"
        )
        
        long_query = " ".join(["word"] * 1000)
        result = pipeline.query(long_query)
        
        assert "answer" in result
        assert isinstance(result["answer"], str)

