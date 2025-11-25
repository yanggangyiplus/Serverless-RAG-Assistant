"""
전처리 모듈 테스트
텍스트 정제 및 문서 청킹 기능 검증
"""

import pytest
from src.preprocessing.cleaner import TextCleaner
from src.preprocessing.chunker import DocumentChunker
from src.utils.errors import TextCleaningError, ChunkingError


class TestTextCleaner:
    """TextCleaner 테스트 클래스"""
    
    def test_html_tag_removal(self):
        """HTML 태그 제거 테스트"""
        cleaner = TextCleaner()
        
        # 기본 HTML 태그 제거
        text_with_html = "<p>Hello <b>World</b></p>"
        cleaned = cleaner.clean(text_with_html)
        assert "<" not in cleaned
        assert ">" not in cleaned
        assert "Hello World" in cleaned
        
        # 복잡한 HTML 구조
        complex_html = "<div><span>Test</span><br/><hr/></div>"
        cleaned = cleaner.clean(complex_html)
        assert "<" not in cleaned
        assert ">" not in cleaned
    
    def test_whitespace_normalization(self):
        """공백 정규화 테스트"""
        cleaner = TextCleaner()
        
        # 연속된 공백 정규화
        text_with_spaces = "Hello    World\n\n\nTest"
        cleaned = cleaner.clean(text_with_spaces)
        assert "    " not in cleaned
        assert "\n\n\n" not in cleaned
        
        # 탭 문자 처리
        text_with_tabs = "Hello\t\tWorld"
        cleaned = cleaner.clean(text_with_tabs)
        assert cleaned.strip() == "Hello World"
    
    def test_special_characters(self):
        """특수 문자 처리 테스트"""
        cleaner = TextCleaner()
        
        # 제어 문자 제거
        text_with_control = "Hello\x00\x01World"
        cleaned = cleaner.clean(text_with_control)
        assert "\x00" not in cleaned
        assert "\x01" not in cleaned
    
    def test_edge_cases(self):
        """Edge case 테스트"""
        cleaner = TextCleaner()
        
        # 빈 문자열
        assert cleaner.clean("") == ""
        
        # None 처리 (문자열이 아닌 경우)
        with pytest.raises((AttributeError, TypeError)):
            cleaner.clean(None)
        
        # 특수문자만 있는 경우
        special_only = "!@#$%^&*()"
        cleaned = cleaner.clean(special_only)
        assert len(cleaned) > 0
        
        # 공백만 있는 경우
        whitespace_only = "   \n\n\t\t   "
        cleaned = cleaner.clean(whitespace_only)
        assert len(cleaned) == 0 or cleaned.strip() == ""
    
    def test_clean_with_options(self):
        """옵션별 정제 테스트"""
        cleaner = TextCleaner()
        
        text = "<p>Hello    World</p>"
        
        # HTML 제거만
        cleaned = cleaner.clean(text, remove_html=True, normalize_whitespace=False)
        assert "<" not in cleaned
        assert "    " in cleaned
        
        # 공백 정규화만
        cleaned = cleaner.clean(text, remove_html=False, normalize_whitespace=True)
        assert "<" in cleaned
        assert "    " not in cleaned


class TestDocumentChunker:
    """DocumentChunker 테스트 클래스"""
    
    def test_basic_chunking(self):
        """기본 청킹 테스트"""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
        
        # 긴 텍스트 청킹
        long_text = " ".join(["word"] * 200)
        chunks = chunker.chunk(long_text, metadata={"document_id": "test"})
        
        assert len(chunks) > 0
        assert all(len(chunk.text) <= 100 + 50 for chunk in chunks)  # 오버랩 고려
        
        # 청크 ID 확인
        assert all(chunk.chunk_id.startswith("test_chunk_") for chunk in chunks)
    
    def test_chunking_with_separator(self):
        """구분자 기반 청킹 테스트"""
        chunker = DocumentChunker(chunk_size=50, chunk_overlap=10, separator="\n\n")
        
        text = "Paragraph 1\n\nParagraph 2\n\nParagraph 3"
        chunks = chunker.chunk(text, metadata={"document_id": "test"})
        
        assert len(chunks) > 0
        # 구분자로 분할된 경우 각 청크가 적절한 크기를 가지는지 확인
        assert all(len(chunk.text) > 0 for chunk in chunks)
    
    def test_chunking_edge_cases(self):
        """Edge case 테스트"""
        chunker = DocumentChunker(chunk_size=100, chunk_overlap=20)
        
        # 빈 문자열
        chunks = chunker.chunk("", metadata={"document_id": "test"})
        assert len(chunks) == 0
        
        # 매우 짧은 텍스트
        short_text = "Hello World"
        chunks = chunker.chunk(short_text, metadata={"document_id": "test"})
        assert len(chunks) == 1
        assert chunks[0].text == short_text
        
        # 정확히 chunk_size와 같은 길이
        exact_size_text = "a" * 100
        chunks = chunker.chunk(exact_size_text, metadata={"document_id": "test"})
        assert len(chunks) >= 1
    
    def test_chunk_metadata(self):
        """청크 메타데이터 테스트"""
        chunker = DocumentChunker(chunk_size=50, chunk_overlap=10)
        
        text = " ".join(["word"] * 100)
        metadata = {"document_id": "doc123", "author": "test"}
        chunks = chunker.chunk(text, metadata=metadata)
        
        # 모든 청크에 메타데이터가 포함되어 있는지 확인
        for chunk in chunks:
            assert chunk.metadata["document_id"] == "doc123"
            assert chunk.metadata["author"] == "test"
            assert "chunk_index" in chunk.metadata
    
    def test_chunk_overlap(self):
        """청크 오버랩 테스트"""
        chunker = DocumentChunker(chunk_size=50, chunk_overlap=20)
        
        text = "a" * 100
        chunks = chunker.chunk(text, metadata={"document_id": "test"})
        
        # 오버랩이 제대로 적용되는지 확인
        if len(chunks) > 1:
            # 연속된 청크들이 오버랩 구간을 가지는지 확인
            for i in range(len(chunks) - 1):
                current_end = chunks[i].end_index
                next_start = chunks[i + 1].start_index
                # 오버랩이 있어야 함 (다음 시작이 현재 끝보다 앞에 있어야 함)
                assert next_start < current_end
    
    def test_special_characters_in_chunking(self):
        """특수문자가 포함된 텍스트 청킹 테스트"""
        chunker = DocumentChunker(chunk_size=50, chunk_overlap=10)
        
        # 특수문자 포함 텍스트
        special_text = "Hello!@#$%^&*()World\n\nTest\tTab"
        chunks = chunker.chunk(special_text, metadata={"document_id": "test"})
        
        assert len(chunks) > 0
        # 모든 청크가 원본 텍스트의 일부를 포함하는지 확인
        combined = "".join(chunk.text for chunk in chunks)
        assert len(combined) >= len(special_text) - 50  # 오버랩 고려

