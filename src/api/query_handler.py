# src/api/query_handler.py

import json
from src.services.rag_service import process_rag_query
from src.vectorstore.mock_store import MockVectorStore
from src.embeddings.embedder import EmbeddingGenerator

vector_store = MockVectorStore()
embedding_generator = EmbeddingGenerator()

def lambda_handler(event, context=None):
    """
    AWS Lambda 스타일 Query 핸들러
    event = {
        "body": "{\"question\": \"Serverless RAG란?\", \"top_k\": 5}"
    }
    """

    try:
        body = json.loads(event["body"])

        question = body["question"]
        top_k = body.get("top_k", 5)

        result = process_rag_query(
            question=question,
            vector_store=vector_store,
            embedding_generator=embedding_generator,
            top_k=top_k
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
