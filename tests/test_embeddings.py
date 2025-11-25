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

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
                 provider: str = "huggingface"):
        self.model_name = model_name
        self.provider = provider
        self.embedder = None
        self._initialize_embedder()
        logger.info(f"EmbeddingGenerator initialized: {provider}/{model_name}")

    # ------------------------------------------------------
    # Embedder initialize
    # ------------------------------------------------------
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
                    model_kwargs={"device": "cpu"}  # CPU 강제
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
                client = boto3.client("bedrock-runtime")
                self.embedder = BedrockEmbeddings(
                    client=client,
                    model_id="amazon.titan-embed-text-v1"
                )

            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            logger.info("Embedder initialized successfully")

        except Exception as e:
            logger.warning(f"Embedder init failed ({e}). Using Mock embedding.")
            self.embedder = None  # Mock fallback

    # ------------------------------------------------------
    # Stable seed (Python hash 제거)
    # ------------------------------------------------------
    def _stable_seed(self, text: str) -> int:
        """텍스트 기반 고정 시드 (Python hash 사용 금지)"""
        md5 = hashlib.md5(text.encode()).hexdigest()
        return int(md5, 16) % (2**32)

    # ------------------------------------------------------
    # Mock embedding (정규화 + 일관성 보장)
    # ------------------------------------------------------
    def _mock_embed(self, text: str, dimension: int = 384) -> List[float]:
        """Mock 임베딩 (단어 기반, 고정 해시, 정규화)"""

        # 공백/개행도 고유 벡터 생성
        if not text or len(text.strip()) < 2:
            np.random.seed(self._stable_seed(text))
            vec = np.random.normal(0, 0.1, dimension)
            vec = vec / np.linalg.norm(vec)
            return vec.tolist()

        words = re.findall(r"\w+", text.lower())

        # 단어 없음 → 고유 랜덤 벡터
        if not words:
            np.random.seed(self._stable_seed(text))
            vec = np.random.normal(0, 0.1, dimension)
            vec = vec / np.linalg.norm(vec)
            return vec.tolist()

        embedding = np.zeros(dimension)

        # 단어별 분산 벡터 생성 (정규화 전)
        for word in words:
            h = hashlib.md5(word.encode()).hexdigest()
            h_int = int(h, 16)

            for i in range(20):
                idx = (h_int + i * 11) % dimension
                value = ((h_int >> (i * 4)) % 2000) / 1000.0 - 1.0
                embedding[idx] += value

        # 정규화
        norm = np.linalg.norm(embedding)
        if norm == 0:
            np.random.seed(self._stable_seed(text))
            embedding = np.random.normal(0, 0.1, dimension)
            norm = np.linalg.norm(embedding)

        embedding = embedding / norm
        return embedding.tolist()

    # ------------------------------------------------------
    # Public APIs
    # ------------------------------------------------------
    def embed_text(self, text: str) -> List[float]:
        """단일 텍스트 임베딩"""
        if self.embedder is None:
            return self._mock_embed(text)

        try:
            return self.embedder.embed_query(text)
        except Exception as e:
            logger.error(f"Embed query failed → Mock fallback: {e}")
            return self._mock_embed(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """여러 문서 임베딩"""
        if self.embedder is None:
            return [self._mock_embed(t) for t in texts]

        try:
            return self.embedder.embed_documents(texts)
        except Exception as e:
            logger.error(f"Embed documents failed → Mock fallback: {e}")
            return [self._mock_embed(t) for t in texts]

    # ------------------------------------------------------
    # Dimension property (Mock or Real)
    # ------------------------------------------------------
    @property
    def dimension(self) -> int:
        if self.embedder is None:
            return 384
        try:
            return len(self.embed_text("dimension_check"))
        except:
            return 384
