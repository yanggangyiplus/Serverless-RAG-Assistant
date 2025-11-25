"""
문서 수집 모듈
S3 이벤트 기반 문서 업로드 처리
"""

from .parser import DocumentParser

# S3DocumentHandler는 선택적 import (boto3 의존성)
try:
    import boto3
    from .s3_handler import S3DocumentHandler
    __all__ = ["S3DocumentHandler", "DocumentParser"]
except ImportError:
    S3DocumentHandler = None
    __all__ = ["DocumentParser"]

