"""
AWS Lambda 핸들러
RAG 질의응답, 문서 업로드, 문서 목록 조회 기능 제공
"""

import os
import json
import base64
import math
from typing import List, Dict, Any

import boto3
import requests

# 환경 변수
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
VECTORSTORE_TABLE_NAME = os.environ.get("VECTORSTORE_TABLE_NAME")
AWS_REGION = "ap-southeast-2"

if not VECTORSTORE_TABLE_NAME:
    raise RuntimeError("환경변수 VECTORSTORE_TABLE_NAME 이(가) 설정되지 않았습니다.")


class DynamoVectorStore:
    """
    DynamoDB 기반 벡터 스토어
    
    DynamoDB 테이블 구조:
    - PK: document_id (STRING)
    - SK: chunk_id (STRING)
    - text: 원본 텍스트
    - embedding: JSON 문자열(list[float])
    """

    def __init__(self, table_name: str, region_name: str | None = None):
        """
        DynamoVectorStore 초기화
        
        Args:
            table_name: DynamoDB 테이블 이름
            region_name: AWS 리전 (기본값: None)
        """
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.table = self.dynamodb.Table(table_name)

    def add_document(self, document_id: str, chunk_id: str, text: str, embedding: List[float]) -> None:
        self.table.put_item(
            Item={
                "document_id": document_id,
                "chunk_id": chunk_id,
                "text": text,
                "embedding": json.dumps(embedding),  # DynamoDB는 float list를 바로 못 넣으므로 문자열로 저장
            }
        )

    def _scan_all_items(self) -> List[Dict[str, Any]]:
        """테이블 전체 스캔 (소규모 데모 전용)"""
        items: List[Dict[str, Any]] = []
        scan_kwargs: Dict[str, Any] = {}
        while True:
            resp = self.table.scan(**scan_kwargs)
            items.extend(resp.get("Items", []))
            last_key = resp.get("LastEvaluatedKey")
            if not last_key:
                break
            scan_kwargs["ExclusiveStartKey"] = last_key
        return items

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def similarity_search(self, query_vec: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """전체 아이템을 스캔해서 코사인 유사도 순으로 정렬 (데모용)"""
        items = self._scan_all_items()
        scored: List[tuple[float, Dict[str, Any]]] = []

        for item in items:
            emb_str = item.get("embedding")
            if not emb_str:
                continue
            try:
                emb = json.loads(emb_str)
                score = self._cosine_similarity(query_vec, emb)
                scored.append((score, item))
            except Exception:
                # 잘못 저장된 레코드는 무시
                continue

        scored.sort(key=lambda x: x[0], reverse=True)
        return [x[1] for x in scored[:top_k]]


vector_store = DynamoVectorStore(VECTORSTORE_TABLE_NAME, AWS_REGION)


def embed_text(text: str) -> List[float]:
    """
    Cohere API를 사용하여 텍스트 임베딩 생성
    
    Args:
        text: 임베딩할 텍스트
        
    Returns:
        임베딩 벡터 리스트
        
    Raises:
        RuntimeError: COHERE_API_KEY가 설정되지 않은 경우
    """
    if not COHERE_API_KEY:
        raise RuntimeError("COHERE_API_KEY 환경변수가 설정되지 않았습니다.")

    url = "https://api.cohere.com/v1/embed"
    headers = {
        "Authorization": f"Bearer {COHERE_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "embed-english-v3.0",
        "input_type": "search_document",
        "texts": [text],
    }

    res = requests.post(url, headers=headers, json=payload, timeout=30)
    data = res.json()

    if "embeddings" not in data:
        raise RuntimeError(f"Cohere embedding error: {data}")

    return data["embeddings"][0]


def generate_answer(context: str, question: str) -> str:
    """
    Groq API를 사용하여 RAG 기반 답변 생성
    
    Args:
        context: 검색된 문서 컨텍스트
        question: 사용자 질문
        
    Returns:
        생성된 답변 문자열
        
    Raises:
        RuntimeError: GROQ_API_KEY가 설정되지 않은 경우
    """
    if not GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY 환경변수가 설정되지 않았습니다.")

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    messages = [
        {"role": "system", "content": "You are a helpful RAG assistant."},
        {
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion: {question}\nAnswer in Korean:",
        },
    ]

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": messages,
        "temperature": 0.0,
    }

    res = requests.post(url, headers=headers, json=payload, timeout=60)
    data = res.json()

    if "choices" not in data:
        raise RuntimeError(f"Groq LLM error: {data}")

    return data["choices"][0]["message"]["content"]


# =========================================================
# /upload 핸들러
# =========================================================
def handle_upload(event: Dict[str, Any]) -> Dict[str, Any]:
    body_raw = event.get("body") or "{}"

    if event.get("isBase64Encoded"):
        body_raw = base64.b64decode(body_raw).decode("utf-8")

    body = json.loads(body_raw)

    # document_id 생성
    raw_id = body.get("document_id") or body.get("filename") or "doc"
    document_id = os.path.splitext(raw_id)[0]

    import uuid
    chunk_id = f"chunk-{uuid.uuid4().hex[:8]}"

    # 파일 또는 텍스트 입력 처리
    if "text" in body:
        text = body["text"]

    elif "file_b64" in body:
        file_b64 = body["file_b64"]
        filename = body.get("filename", "")

        # txt/md 파일만 처리 (PDF는 현재 미지원)
        lower = filename.lower()
        if lower.endswith(".pdf"):
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "현재 /upload API는 PDF를 직접 처리하지 않습니다. txt / md 파일만 업로드 해주세요."
                })
            }

        try:
            file_bytes = base64.b64decode(file_b64)
            text = file_bytes.decode("utf-8")
        except Exception as e:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": f"파일을 UTF-8로 변환할 수 없습니다: {str(e)}"
                })
            }

    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "text 또는 file_b64가 없습니다."                })
            }

    # 임베딩 생성
    try:
        embedding = embed_text(text)
        embedding = embedding.tolist() if hasattr(embedding, "tolist") else embedding
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"임베딩 생성 실패: {str(e)}"})
        }

    # DynamoDB 저장
    try:
        vector_store.add_document(document_id, chunk_id, text, embedding)
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"DynamoDB 저장 실패: {str(e)}"})
        }

    return {
        "statusCode": 200,
        "body": json.dumps({
            "document_id": document_id,
            "chunk_id": chunk_id,
            "num_chunks": 1
        }),
    }

def handle_query(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    RAG 질의응답 핸들러
    
    Args:
        event: Lambda 이벤트 (body에 question, top_k 포함)
        
    Returns:
        API Gateway 형식의 응답 딕셔너리 (answer, source_documents 포함)
    """
    body_raw = event.get("body") or "{}"

    if event.get("isBase64Encoded"):
        body_raw = base64.b64decode(body_raw).decode("utf-8")

    body = json.loads(body_raw)

    question = body.get("question")
    if not question:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing 'question' in request body"}),
        }

    top_k = int(body.get("top_k", 5))

    # 쿼리 임베딩 생성
    q_vec = embed_text(question)

    # 벡터 검색
    docs = vector_store.similarity_search(q_vec, top_k=top_k)

    # 컨텍스트 생성
    context = "\n\n---\n\n".join(item.get("text", "") for item in docs)

    # LLM 답변 생성
    answer = generate_answer(context, question)

    # 소스 문서 정리
    source_docs = [
        {
            "document_id": item.get("document_id"),
            "chunk_id": item.get("chunk_id"),
            "text": item.get("text", ""),
        }
        for item in docs
    ]

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "answer": answer,
                "source_documents": source_docs,
            }
        ),
    }


def lambda_handler(event, context):
    """
    Lambda 메인 핸들러
    API Gateway 이벤트를 받아 적절한 핸들러로 라우팅
    
    Args:
        event: Lambda 이벤트 (API Gateway 형식)
        context: Lambda 컨텍스트
        
    Returns:
        API Gateway 형식의 응답 딕셔너리
    """
    # 이벤트 로깅
    print("=== INCOMING EVENT ===")
    print(json.dumps(event, indent=2, ensure_ascii=False))
    print("======================")

    # REST / HTTP API 모두 처리 가능한 방식
    path = event.get("path") or event.get("rawPath", "")
    method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method", "")

    # path 끝에 / 제거
    path = path.rstrip("/")

    print(f"[ROUTING] method={method}, path={path}")

    # 라우팅
    if method == "GET" and path == "/documents":
        return handle_list_documents()

    elif method == "POST" and path == "/upload":
        return handle_upload(event)

    elif method == "POST" and path == "/query":
        return handle_query(event)

    # 404 처리
    return {
        "statusCode": 404,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "error": "Not Found",
            "path": path,
            "method": method,
            "available_routes": [
                "GET /documents",
                "POST /upload",
                "POST /query"
            ]
        })
    }

def handle_list_documents():
    """
    문서 목록 조회 핸들러
    
    Returns:
        API Gateway 형식의 응답 딕셔너리 (total_documents, documents 포함)
    """
    import boto3
    from boto3.dynamodb.conditions import Key

    table_name = VECTORSTORE_TABLE_NAME
    dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
    table = dynamodb.Table(table_name)

    # 문서 목록 가져오기
    response = table.scan(ProjectionExpression="document_id")

    items = response.get("Items", [])

    # 문서별 청크 수 집계
    docs = {}
    for item in items:
        doc_id = item["document_id"]
        docs.setdefault(doc_id, 0)
        docs[doc_id] += 1

    # 응답 형태로 변환
    formatted = [
        {"document_id": doc_id, "num_chunks": count}
        for doc_id, count in docs.items()
    ]

    return {
        "statusCode": 200,
        "body": json.dumps({
            "total_documents": len(formatted),
            "documents": formatted
        })
    }
