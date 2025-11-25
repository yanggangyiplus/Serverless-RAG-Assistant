"""
벡터 스토어 모듈
DynamoDB 또는 로컬 벡터 스토어 래퍼
"""

from .base import VectorStore, VectorDocument
from .mock_store import MockVectorStore

# DynamoDB VectorStore는 선택적 import (boto3 의존성)
try:
    import boto3
    from .dynamodb_store import DynamoDBVectorStore
    __all__ = ["VectorStore", "VectorDocument", "DynamoDBVectorStore", "MockVectorStore"]
except ImportError:
    DynamoDBVectorStore = None
    __all__ = ["VectorStore", "VectorDocument", "MockVectorStore"]

