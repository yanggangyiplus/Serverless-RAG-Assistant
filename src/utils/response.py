"""
API 응답 유틸리티
Lambda 핸들러에서 사용하는 통일된 응답 형식
"""

import json
from typing import Dict, Any, Optional
from .errors import RAGBaseError


def success_response(data: Dict[str, Any], status_code: int = 200) -> Dict[str, Any]:
    """
    성공 응답 생성
    
    Args:
        data: 응답 데이터
        status_code: HTTP 상태 코드
        
    Returns:
        API Gateway Proxy 형식 응답
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "success": True,
            "data": data
        }, ensure_ascii=False)
    }


def error_response(
    error: Exception,
    status_code: int = 500,
    error_code: Optional[str] = None
) -> Dict[str, Any]:
    """
    에러 응답 생성
    
    Args:
        error: 예외 객체
        status_code: HTTP 상태 코드
        error_code: 커스텀 에러 코드
        
    Returns:
        API Gateway Proxy 형식 응답
    """
    # RAGBaseError인 경우 상세 정보 추출
    if isinstance(error, RAGBaseError):
        error_type = error.__class__.__name__
        error_message = error.message
        error_code = error_code or error.error_code or error_type.upper()
    else:
        error_type = error.__class__.__name__
        error_message = str(error)
        error_code = error_code or "INTERNAL_ERROR"
    
    # 상태 코드 결정
    if status_code == 500 and isinstance(error, RAGBaseError):
        # 특정 에러 타입에 따라 상태 코드 조정 가능
        if "Configuration" in error_type or "Validation" in error_type:
            status_code = 400
        elif "NotFound" in error_type:
            status_code = 404
    
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({
            "success": False,
            "error": {
                "type": error_type,
                "message": error_message,
                "code": error_code
            }
        }, ensure_ascii=False)
    }

