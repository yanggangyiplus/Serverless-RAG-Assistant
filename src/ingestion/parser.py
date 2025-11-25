"""
Document Parser
PDF / TXT / MD 파일에서 텍스트 추출
"""

import os
from typing import Dict, Any
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DocumentParser:
    """문서 파서"""

    def __init__(self):
        logger.info("DocumentParser initialized")

    # ------------------------------------------------------------
    # 🔥 기존 parse() 메서드 (유지)
    # ------------------------------------------------------------
    def parse(self, file_bytes: bytes, content_type: str, filename: str) -> Dict[str, Any]:
        """파일 타입을 기준으로 텍스트 추출"""

        ext = filename.lower().split(".")[-1]

        if ext == "pdf":
            return self._parse_pdf(file_bytes, filename)

        elif ext in ["txt", "md"]:
            return self._parse_text(file_bytes, filename)

        else:
            raise ValueError(f"지원하지 않는 파일 형식: {ext}")

    # ------------------------------------------------------------
    # 🔥 신규 추가됨: 서비스 레이어에서 사용하는 parse_file()
    # ------------------------------------------------------------
    def parse_file(self, file_bytes: bytes, filename: str) -> str:
        """
        ingestion_service.py 에서 호출하는 API
        → 파일에서 텍스트만 바로 반환
        """
        ext = filename.lower().split(".")[-1]

        parsed = self.parse(
            file_bytes=file_bytes,
            content_type=self._guess_content_type(ext),
            filename=filename
        )

        return parsed.get("text", "")

    # ------------------------------------------------------------
    # 파일 타입 자동 추정
    # ------------------------------------------------------------
    def _guess_content_type(self, ext: str) -> str:
        return {
            "pdf": "application/pdf",
            "txt": "text/plain",
            "md": "text/markdown"
        }.get(ext, "application/octet-stream")

    # ------------------------------------------------------------
    # TXT / MD 파싱
    # ------------------------------------------------------------
    def _parse_text(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        text = file_bytes.decode("utf-8", errors="ignore")
        logger.info(f"Parsed TXT {filename}: {len(text)} chars")
        return {"text": text}

    # ------------------------------------------------------------
    # PDF 파싱
    # ------------------------------------------------------------
    def _parse_pdf(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        from pypdf import PdfReader
        import io

        pdf = PdfReader(io.BytesIO(file_bytes))
        text = ""

        for page in pdf.pages:
            text += page.extract_text() or ""

        logger.info(f"Parsed PDF {filename}: {len(text)} chars")
        return {"text": text}
