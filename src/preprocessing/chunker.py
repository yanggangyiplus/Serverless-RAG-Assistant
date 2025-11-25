"""
문서 청킹 모듈
긴 문서를 작은 청크로 분할
"""

from typing import List, Dict, Optional
from dataclasses import dataclass

from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Chunk:
    """문서 청크 데이터 클래스"""
    text: str
    chunk_id: str
    start_index: int
    end_index: int
    metadata: Dict


class DocumentChunker:
    """문서를 청크로 분할하는 클래스"""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separator: str = "\n\n"
    ):
        """
        청커 초기화
        
        Args:
            chunk_size: 청크 크기 (문자 수)
            chunk_overlap: 청크 간 겹치는 문자 수
            separator: 청크 분할 구분자
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator
        logger.info(f"DocumentChunker initialized: chunk_size={chunk_size}, overlap={chunk_overlap}")
    
    def chunk(self, text: str, metadata: Optional[Dict] = None) -> List[Chunk]:
        """
        텍스트를 청크로 분할
        
        Args:
            text: 원본 텍스트
            metadata: 문서 메타데이터
            
        Returns:
            청크 리스트
        """
        if not text:
            return []
        
        metadata = metadata or {}
        chunks = []
        
        # 구분자로 먼저 분할 시도
        if self.separator in text:
            chunks = self._chunk_by_separator(text, metadata)
        else:
            # 구분자가 없으면 고정 크기로 분할
            chunks = self._chunk_by_size(text, metadata)
        
        logger.info(f"Chunked text into {len(chunks)} chunks")
        return chunks
    
    def _chunk_by_separator(self, text: str, metadata: Dict) -> List[Chunk]:
        """구분자 기반 청킹"""
        chunks = []
        parts = text.split(self.separator)
        
        current_chunk = ""
        current_start = 0
        
        for part in parts:
            # 현재 청크에 추가했을 때 크기 확인
            potential_chunk = current_chunk + (self.separator if current_chunk else "") + part
            
            if len(potential_chunk) <= self.chunk_size:
                current_chunk = potential_chunk
            else:
                # 현재 청크 저장
                if current_chunk:
                    chunk = Chunk(
                        text=current_chunk,
                        chunk_id=f"{metadata.get('document_id', 'doc')}_chunk_{len(chunks)}",
                        start_index=current_start,
                        end_index=current_start + len(current_chunk),
                        metadata={**metadata, "chunk_index": len(chunks)}
                    )
                    chunks.append(chunk)
                    current_start += len(current_chunk) - self.chunk_overlap
                
                # 새 청크 시작
                current_chunk = part
        
        # 마지막 청크 추가
        if current_chunk:
            chunk = Chunk(
                text=current_chunk,
                chunk_id=f"{metadata.get('document_id', 'doc')}_chunk_{len(chunks)}",
                start_index=current_start,
                end_index=current_start + len(current_chunk),
                metadata={**metadata, "chunk_index": len(chunks)}
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_by_size(self, text: str, metadata: Dict) -> List[Chunk]:
        """고정 크기 기반 청킹"""
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk_text = text[start:end]
            
            # 문장 경계에서 자르기 시도
            if end < len(text):
                # 마지막 문장 끝 찾기
                last_period = chunk_text.rfind(".")
                last_newline = chunk_text.rfind("\n")
                last_break = max(last_period, last_newline)
                
                if last_break > self.chunk_size * 0.5:  # 최소 50% 이상은 유지
                    end = start + last_break + 1
                    chunk_text = text[start:end]
            
            chunk = Chunk(
                text=chunk_text,
                chunk_id=f"{metadata.get('document_id', 'doc')}_chunk_{chunk_index}",
                start_index=start,
                end_index=end,
                metadata={**metadata, "chunk_index": chunk_index}
            )
            chunks.append(chunk)
            
            # 다음 청크 시작 위치 (오버랩 고려)
            start = end - self.chunk_overlap
            chunk_index += 1
        
        return chunks

