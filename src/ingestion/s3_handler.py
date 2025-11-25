"""
S3 문서 핸들러
S3 이벤트를 받아 문서 다운로드 및 메타데이터 추출
"""

import boto3
import json
from typing import Dict, Optional
from io import BytesIO

from src.utils.logger import get_logger
from src.utils.errors import S3HandlerError

logger = get_logger(__name__)


class S3DocumentHandler:
    """S3에서 문서를 다운로드하고 메타데이터를 추출하는 핸들러"""
    
    def __init__(self, bucket_name: str, region: str = "ap-northeast-2"):
        """
        Args:
            bucket_name: S3 버킷 이름
            region: AWS 리전
        """
        self.bucket_name = bucket_name
        self.s3_client = boto3.client("s3", region_name=region)
        logger.info(f"S3DocumentHandler initialized for bucket: {bucket_name}")
    
    def download_document(self, s3_key: str) -> bytes:
        """
        S3에서 문서 다운로드
        
        Args:
            s3_key: S3 객체 키
            
        Returns:
            문서 바이너리 데이터
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            content = response["Body"].read()
            logger.info(f"Downloaded document: {s3_key} ({len(content)} bytes)")
            return content
        except Exception as e:
            logger.error(f"Failed to download document {s3_key}: {str(e)}")
            raise
    
    def get_metadata(self, s3_key: str) -> Dict:
        """
        S3 객체 메타데이터 추출
        
        Args:
            s3_key: S3 객체 키
            
        Returns:
            메타데이터 딕셔너리
        """
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            metadata = {
                "s3_key": s3_key,
                "content_type": response.get("ContentType", "unknown"),
                "content_length": response.get("ContentLength", 0),
                "last_modified": response.get("LastModified").isoformat() if response.get("LastModified") else None,
                "etag": response.get("ETag", "").strip('"'),
            }
            # 사용자 정의 메타데이터 병합
            if "Metadata" in response:
                metadata.update(response["Metadata"])
            
            logger.info(f"Extracted metadata for {s3_key}")
            return metadata
        except Exception as e:
            logger.error(f"Failed to get metadata for {s3_key}: {str(e)}")
            raise
    
    def parse_s3_event(self, event: Dict) -> Dict:
        """
        Lambda S3 이벤트 파싱
        
        Args:
            event: Lambda S3 이벤트
            
        Returns:
            파싱된 이벤트 정보
        """
        try:
            # S3 이벤트 구조 파싱
            records = event.get("Records", [])
            if not records:
                raise ValueError("No records found in S3 event")
            
            s3_record = records[0].get("s3", {})
            bucket = s3_record.get("bucket", {}).get("name")
            key = s3_record.get("object", {}).get("key")
            
            # URL 디코딩
            import urllib.parse
            key = urllib.parse.unquote_plus(key)
            
            parsed_event = {
                "bucket": bucket,
                "key": key,
                "event_name": records[0].get("eventName", ""),
                "event_time": records[0].get("eventTime", ""),
            }
            
            logger.info(f"Parsed S3 event: {bucket}/{key}")
            return parsed_event
        except Exception as e:
            logger.error(f"Failed to parse S3 event: {str(e)}")
            raise

