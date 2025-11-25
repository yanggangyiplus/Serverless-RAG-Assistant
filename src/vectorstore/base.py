"""
벡터 스토어 베이스 클래스
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class VectorDocument:
    """벡터 스토어에 저장되는 문서"""
    document_id: str
    chunk_id: str
    text: str
    embedding: List[float]
    metadata: Dict


class VectorStore(ABC):
    """벡터 스토어 인터페이스"""
    
    @abstractmethod
    def add_documents(self, documents: List[VectorDocument]) -> bool:
        """
        문서 추가
        
        Args:
            documents: 추가할 문서 리스트
            
        Returns:
            성공 여부
        """
        pass
    
    @abstractmethod
    def similarity_search(
        self,
        query_embedding: List[float],
        k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[VectorDocument]:
        """
        유사도 검색
        
        Args:
            query_embedding: 쿼리 임베딩 벡터
            k: 반환할 문서 수
            filter_metadata: 메타데이터 필터
            
        Returns:
            검색된 문서 리스트
        """
        pass
    
    @abstractmethod
    def delete_document(self, document_id: str) -> bool:
        """
        문서 삭제
        
        Args:
            document_id: 삭제할 문서 ID
            
        Returns:
            성공 여부
        """
        pass
    
    @abstractmethod
    def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """
        문서 조회
        
        Args:
            document_id: 문서 ID
            
        Returns:
            문서 또는 None
        """
        pass

