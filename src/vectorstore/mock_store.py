"""
Mock 벡터 스토어 구현
로컬 개발/테스트용 인메모리 벡터 스토어
"""

import logging
import numpy as np
from typing import List, Dict, Optional
from .base import VectorStore, VectorDocument

logger = logging.getLogger(__name__)


class MockVectorStore(VectorStore):
    """인메모리 Mock 벡터 스토어 (로컬 개발용)"""
    
    def __init__(self):
        """Mock 스토어 초기화"""
        self.documents: Dict[str, VectorDocument] = {}
        logger.info("MockVectorStore initialized (in-memory)")
    
    def add_documents(self, documents: List[VectorDocument]) -> bool:
        """문서 추가"""
        try:
            for doc in documents:
                key = f"{doc.document_id}_{doc.chunk_id}"
                self.documents[key] = doc
            
            logger.info(f"Added {len(documents)} documents to MockVectorStore")
            return True
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            return False
    
    def similarity_search(
        self,
        query_embedding: List[float],
        k: int = 5,
        filter_metadata: Optional[Dict] = None
    ) -> List[VectorDocument]:
        """유사도 검색"""
        try:
            if not self.documents:
                logger.warning("Vector store is empty")
                return []
            
            query_vec = np.array(query_embedding)
            
            # 쿼리 벡터 정규화 확인
            query_norm = np.linalg.norm(query_vec)
            if query_norm == 0:
                logger.warning("Query embedding is zero vector")
                return []
            
            similarities = []
            
            for key, doc in self.documents.items():
                # 메타데이터 필터링
                if filter_metadata:
                    if not self._matches_filter(doc.metadata, filter_metadata):
                        continue
                
                # 코사인 유사도 계산
                doc_vec = np.array(doc.embedding)
                doc_norm = np.linalg.norm(doc_vec)
                
                if doc_norm == 0:
                    logger.warning(f"Document {key} has zero embedding, skipping")
                    continue
                
                similarity = np.dot(query_vec, doc_vec) / (query_norm * doc_norm)
                
                # NaN 체크
                if np.isnan(similarity) or np.isinf(similarity):
                    logger.warning(f"Invalid similarity for document {key}: {similarity}")
                    continue
                
                similarities.append((similarity, doc))
            
            if not similarities:
                logger.warning("No documents matched the search criteria")
                return []
            
            # 유사도 순으로 정렬
            similarities.sort(key=lambda x: x[0], reverse=True)
            
            # 상위 k개 반환
            results = [doc for _, doc in similarities[:k]]
            
            logger.info(f"Found {len(results)} similar documents (from {len(similarities)} candidates)")
            return results
        except Exception as e:
            logger.error(f"Similarity search failed: {e}", exc_info=True)
            return []
    
    def _matches_filter(self, metadata: Dict, filter_metadata: Dict) -> bool:
        """메타데이터 필터 매칭 확인"""
        for key, value in filter_metadata.items():
            if key not in metadata or metadata[key] != value:
                return False
        return True
    
    def delete_document(self, document_id: str) -> bool:
        """문서 삭제"""
        try:
            keys_to_delete = [
                key for key in self.documents.keys()
                if key.startswith(f"{document_id}_")
            ]
            
            for key in keys_to_delete:
                del self.documents[key]
            
            logger.info(f"Deleted document: {document_id} ({len(keys_to_delete)} chunks)")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False
    
    def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """문서 조회"""
        # 첫 번째 청크만 반환
        for key, doc in self.documents.items():
            if doc.document_id == document_id:
                return doc
        return None
    
    def get_all_documents(self) -> List[VectorDocument]:
        """모든 문서 반환"""
        return list(self.documents.values())

