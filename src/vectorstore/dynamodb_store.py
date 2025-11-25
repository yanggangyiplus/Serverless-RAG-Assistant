"""
DynamoDB 벡터 스토어 구현
DynamoDB를 벡터 데이터베이스로 사용
"""

import boto3
import json
import logging
import numpy as np
from typing import List, Dict, Optional
from .base import VectorStore, VectorDocument

logger = logging.getLogger(__name__)


class DynamoDBVectorStore(VectorStore):
    """DynamoDB 기반 벡터 스토어"""
    
    def __init__(
        self,
        table_name: str,
        region: str = "ap-northeast-2",
        embedding_dimension: int = 384
    ):
        """
        DynamoDB 벡터 스토어 초기화
        
        Args:
            table_name: DynamoDB 테이블 이름
            region: AWS 리전
            embedding_dimension: 임베딩 차원
        """
        self.table_name = table_name
        self.embedding_dimension = embedding_dimension
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table = self.dynamodb.Table(table_name)
        logger.info(f"DynamoDBVectorStore initialized: table={table_name}")
    
    def add_documents(self, documents: List[VectorDocument]) -> bool:
        """문서 추가"""
        try:
            with self.table.batch_writer() as batch:
                for doc in documents:
                    item = {
                        "document_id": doc.document_id,
                        "chunk_id": doc.chunk_id,
                        "text": doc.text,
                        "embedding": json.dumps(doc.embedding),  # JSON 문자열로 저장
                        "metadata": json.dumps(doc.metadata),
                    }
                    batch.put_item(Item=item)
            
            logger.info(f"Added {len(documents)} documents to DynamoDB")
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
            # DynamoDB는 직접적인 벡터 유사도 검색을 지원하지 않으므로
            # 전체 스캔 후 메모리에서 유사도 계산 (작은 규모용)
            # 프로덕션에서는 OpenSearch, Pinecone 등 전용 벡터 DB 사용 권장
            
            response = self.table.scan()
            items = response.get("Items", [])
            
            # 유사도 계산
            similarities = []
            query_vec = np.array(query_embedding)
            
            for item in items:
                # 메타데이터 필터링
                if filter_metadata:
                    item_metadata = json.loads(item.get("metadata", "{}"))
                    if not self._matches_filter(item_metadata, filter_metadata):
                        continue
                
                # 임베딩 로드
                doc_embedding = json.loads(item.get("embedding", "[]"))
                doc_vec = np.array(doc_embedding)
                
                # 코사인 유사도 계산
                similarity = np.dot(query_vec, doc_vec) / (
                    np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)
                )
                
                similarities.append((similarity, item))
            
            # 유사도 순으로 정렬
            similarities.sort(key=lambda x: x[0], reverse=True)
            
            # 상위 k개 반환
            results = []
            for similarity, item in similarities[:k]:
                doc = VectorDocument(
                    document_id=item["document_id"],
                    chunk_id=item["chunk_id"],
                    text=item["text"],
                    embedding=json.loads(item.get("embedding", "[]")),
                    metadata=json.loads(item.get("metadata", "{}"))
                )
                results.append(doc)
            
            logger.info(f"Found {len(results)} similar documents")
            return results
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
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
            # 해당 document_id의 모든 청크 삭제
            response = self.table.query(
                KeyConditionExpression="document_id = :doc_id",
                ExpressionAttributeValues={":doc_id": document_id}
            )
            
            with self.table.batch_writer() as batch:
                for item in response.get("Items", []):
                    batch.delete_item(
                        Key={
                            "document_id": item["document_id"],
                            "chunk_id": item["chunk_id"]
                        }
                    )
            
            logger.info(f"Deleted document: {document_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document: {e}")
            return False
    
    def get_document(self, document_id: str) -> Optional[VectorDocument]:
        """문서 조회"""
        try:
            # 첫 번째 청크만 반환 (전체 문서는 여러 청크로 구성될 수 있음)
            response = self.table.query(
                KeyConditionExpression="document_id = :doc_id",
                Limit=1,
                ExpressionAttributeValues={":doc_id": document_id}
            )
            
            items = response.get("Items", [])
            if not items:
                return None
            
            item = items[0]
            return VectorDocument(
                document_id=item["document_id"],
                chunk_id=item["chunk_id"],
                text=item["text"],
                embedding=json.loads(item.get("embedding", "[]")),
                metadata=json.loads(item.get("metadata", "{}"))
            )
        except Exception as e:
            logger.error(f"Failed to get document: {e}")
            return None

