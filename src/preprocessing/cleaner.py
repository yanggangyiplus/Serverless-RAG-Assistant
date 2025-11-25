"""
텍스트 클리너
불필요한 공백/개행/특수문자 정리
"""

import re
from src.utils.logger import get_logger

logger = get_logger(__name__)


class TextCleaner:
    """문서 전처리용 텍스트 클리너"""

    def __init__(self):
        logger.info("TextCleaner initialized")

    # ------------------------------------------------------------
    # 🔥 기존 clean() 메서드 (유지)
    # ------------------------------------------------------------
    def clean(self, text: str) -> str:
        """텍스트 정리"""

        if not text:
            return ""

        cleaned = text

        # 연속 공백 삭제
        cleaned = re.sub(r"\s+", " ", cleaned)

        # 양쪽 공백 제거
        cleaned = cleaned.strip()

        return cleaned

    # ------------------------------------------------------------
    # 🔥 ingestion_service 와 맞는 clean_text() 추가
    # ------------------------------------------------------------
    def clean_text(self, text: str) -> str:
        """
        ingestion 서비스에서 호출하는 텍스트 정제 API
        (clean()을 그대로 사용하지만, 서비스 레이어 요구명세 맞춰 추가)
        """
        return self.clean(text)
