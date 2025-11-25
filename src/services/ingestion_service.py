# src/services/ingestion_service.py

from typing import List, Dict
from src.ingestion.parser import DocumentParser
from src.preprocessing.cleaner import TextCleaner
from src.preprocessing.chunker import DocumentChunker, Chunk
from src.embeddings.embedder import EmbeddingGenerator
from src.vectorstore.base import VectorStore, VectorDocument
from src.utils.logger import get_logger

logger = get_logger(__name__)


def process_document_ingestion(
    file_bytes: bytes,
    filename: str,
    vector_store: VectorStore,
    embedding_generator: EmbeddingGenerator,
    chunk_size: int = 500,
    overlap: int = 50,
) -> Dict:

    logger.info(f"[Ingestion] Start processing: {filename}")

    # 1. 파일 파싱
    parser = DocumentParser()
    parsed_text = parser.parse_file(file_bytes, filename)

    # 2. 전처리
    cleaner = TextCleaner()
    cleaned_text = cleaner.clean_text(parsed_text)

    # 3. 청킹
    chunker = DocumentChunker(chunk_size=chunk_size, chunk_overlap=overlap)
    chunks: List[Chunk] = chunker.chunk(cleaned_text)

    logger.info(f"[Ingestion] Text chunked into {len(chunks)} chunks")

    # 4. Chunk → 문자열 리스트
    chunk_texts = [c.text for c in chunks]

    # 5. 임베딩
    vectors = embedding_generator.embed_documents(chunk_texts)

    # 6. VectorDocument 생성
    docs: List[VectorDocument] = []

    for chunk, emb in zip(chunks, vectors):
        docs.append(
            VectorDocument(
                document_id=filename,
                chunk_id=chunk.chunk_id,
                text=chunk.text,
                embedding=emb,
                metadata=chunk.metadata,        # ← Chunk의 metadata 보존
            )
        )

    # 7. VectorStore 저장
    vector_store.add_documents(docs)

    logger.info(f"[Ingestion] Saved {len(docs)} chunks for file: {filename}")

    return {
        "document_id": filename,
        "num_chunks": len(chunks),
        "chunks": [c.text for c in chunks],   # 문자열만 반환
    }
