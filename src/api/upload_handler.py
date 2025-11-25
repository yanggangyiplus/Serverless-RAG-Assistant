# src/api/upload_handler.py

import json
import base64
from src.services.ingestion_service import process_document_ingestion
from src.vectorstore.mock_store import MockVectorStore
from src.embeddings.embedder import EmbeddingGenerator

# Lambda cold start 방지: 전역에서 생성
vector_store = MockVectorStore()
embedding_generator = EmbeddingGenerator()

def lambda_handler(event, context=None):
    """
    AWS Lambda 업로드 핸들러
    event = {
        "body": "{\"filename\": \"file.txt\", \"file\": \"<base64>\"}"
    }
    """

    try:
        # API Gateway는 body를 문자열로 전달함
        body = json.loads(event["body"])

        filename = body["filename"]
        file_base64 = body["file"]  # base64 encoded file
        chunk_size = body.get("chunk_size", 500)
        overlap = body.get("overlap", 50)

        # base64 → bytes
        file_bytes = base64.b64decode(file_base64)

        result = process_document_ingestion(
            file_bytes=file_bytes,
            filename=filename,
            vector_store=vector_store,
            embedding_generator=embedding_generator,
            chunk_size=chunk_size,
            overlap=overlap
        )

        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
