"""
임베딩 생성기
LangChain Embeddings를 사용하여 텍스트를 벡터로 변환
"""

from typing import List, Optional
import numpy as np
import hashlib
import re

from src.utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingGenerator:
    """텍스트를 벡터 임베딩으로 변환하는 생성기"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", provider: str = "huggingface"):
        self.model_name = model_name
        self.provider = provider
        self.embedder = None
        self._initialize_embedder()
        logger.info(f"EmbeddingGenerator initialized: {provider}/{model_name}")
    
    def _initialize_embedder(self):
        """임베딩 모델 초기화"""
        try:
            if self.provider == "huggingface":
                try:
                    from langchain_community.embeddings import HuggingFaceEmbeddings
                except ImportError:
                    from langchain.embeddings import HuggingFaceEmbeddings
                self.embedder = HuggingFaceEmbeddings(
                    model_name=self.model_name,
                    model_kwargs={"device": "cpu"}
                )
            elif self.provider == "openai":
                try:
                    from langchain_openai import OpenAIEmbeddings
                except ImportError:
                    from langchain.embeddings import OpenAIEmbeddings
                import os
                self.embedder = OpenAIEmbeddings(
                    openai_api_key=os.getenv("OPENAI_API_KEY")
                )
            elif self.provider == "bedrock":
                try:
                    from langchain_community.embeddings import BedrockEmbeddings
                except ImportError:
                    from langchain.embeddings import BedrockEmbeddings
                import boto3
                bedrock_client = boto3.client("bedrock-runtime")
                self.embedder = BedrockEmbeddings(
                    client=bedrock_client,
                    model_id="amazon.titan-embed-text-v1"
                )
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            logger.info(f"Embedder initialized successfully")

        except Exception as e:
            logger.warning(f"Embedder init failed ({e}), using Mock Embeddings")
            self.embedder = None
    
    # ------------------------------
    # 고정 시드 생성
    # ------------------------------
    def _stable_seed(self, text: str) -> int:
        """텍스트 기반 고정 시드 생성 (Python hash 사용 절대 금지)"""
        md5 = hashlib.md5(text.encode()).hexdigest()
        return int(md5, 16) % (2**32)

    # ------------------------------
    # Mock 임베딩
    # ------------------------------
    def _mock_embed(self, text: str, dimension: int = 384) -> List[float]:
        """Mock 임베딩: 단어 기반 + 고정 해시 기반 벡터"""

        # 공백/개행/짧은 텍스트도 고유 벡터 부여
        if not text or len(text.strip()) < 2:
            np.random.seed(self._stable_seed(text))
            vec = np.random.normal(0, 0.1, dimension)
            vec = vec / np.linalg.norm(vec)
            return vec.tolist()

        # 소문자 단어 추출
        words = re.findall(r"\w+", text.lower())

        # 단어가 없는 경우도 고정 벡터 생성
        if not words:
            np.random.seed(self._stable_seed(text))
            vec = np.random.normal(0, 0.1, dimension)
            vec = vec / np.linalg.norm(vec)
            return vec.tolist()

        embedding = np.zeros(dimension)

        # 단어 기반 분산 임베딩
        for word in words:
            h = hashlib.md5(word.encode()).hexdigest()
            h_int = int(h, 16)

            # 각각의 단어가 여러 차원에 분산 기여
            for i in range(20):
                idx = (h_int + i * 13) % dimension
                val = ((h_int >> (i * 5)) % 2000) / 1000.0 - 1.0
                embedding[idx] += val

        # 정규화
        norm = np.linalg.norm(embedding)

        # 🔥 Zero vector 또는 NaN/Inf 방지
        if norm == 0 or np.isnan(norm) or np.isinf(norm):
            # 새로운 랜덤 벡터 생성 (안전한 fallback)
            np.random.seed(self._stable_seed(text) + 999)
            embedding = np.random.normal(0, 0.5, dimension)
            embedding = embedding / np.linalg.norm(embedding)
        else:
            embedding = embedding / norm

        return embedding.tolist()


    # ------------------------------
    # Public API
    # ------------------------------
    def embed_text(self, text: str) -> List[float]:
        """질문(단일 텍스트) 임베딩"""
        if self.embedder is None:
            return self._mock_embed(text)

        try:
            return self.embedder.embed_query(text)
        except Exception as e:
            logger.error(f"Embed query failed: {e}")
            return self._mock_embed(text)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """여러 문서 임베딩"""
        if self.embedder is None:
            return [self._mock_embed(t) for t in texts]

        try:
            return self.embedder.embed_documents(texts)
        except Exception as e:
            logger.error(f"Embed documents failed: {e}")
            return [self._mock_embed(t) for t in texts]

    @property
    def dimension(self) -> int:
        """임베딩 차원"""
        if self.embedder is None:
            return 384
        try:
            return len(self.embed_text("dimension_test"))
        except:
            return 384
