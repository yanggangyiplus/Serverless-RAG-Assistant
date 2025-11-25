"""
로거 설정 유틸리티
Lambda 환경에서도 동작하도록 설계된 로깅 유틸리티
"""

import logging
import sys
import json
import os
from typing import Optional
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON 형태의 로그 포맷터"""
    
    def format(self, record: logging.LogRecord) -> str:
        """
        로그 레코드를 JSON 형식으로 변환
        
        Args:
            record: 로그 레코드
            
        Returns:
            JSON 문자열
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # 예외 정보 추가
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 추가 필드 추가
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logger(
    name: str,
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    use_json: bool = False
) -> logging.Logger:
    """
    로거 설정
    
    Args:
        name: 로거 이름
        level: 로그 레벨
        format_string: 로그 포맷 문자열 (use_json=False일 때만 사용)
        use_json: JSON 포맷 사용 여부 (Lambda 환경에서 유용)
        
    Returns:
        설정된 로거 인스턴스
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 핸들러가 이미 있으면 추가하지 않음
    if logger.handlers:
        return logger
    
    # 콘솔 핸들러 생성
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    
    # 포맷 설정
    if use_json:
        formatter = JSONFormatter()
    else:
        if format_string is None:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(format_string)
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Lambda 환경에서는 JSON 포맷 권장
    if os.getenv("AWS_LAMBDA_FUNCTION_NAME") and not use_json:
        logger.info("Running in Lambda environment. Consider using JSON format for better CloudWatch integration.")
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    모듈별 로거 생성 (간편 함수)
    
    Args:
        name: 로거 이름 (보통 __name__ 사용)
        
    Returns:
        로거 인스턴스
    """
    # Lambda 환경에서는 JSON 포맷 사용
    use_json = os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None
    return setup_logger(name, use_json=use_json)

