# 로컬 테스트 가이드

Lambda 함수를 로컬에서 테스트하는 방법을 설명합니다.

## Lambda 함수 로컬 테스트

### upload_handler 테스트

S3 이벤트를 시뮬레이션하여 문서 업로드 핸들러를 테스트합니다.

**테스트 스크립트:**

```python
# test_upload_handler.py
import json
from src.api.upload_handler import lambda_handler

# S3 이벤트 시뮬레이션
event = {
    "Records": [
        {
            "s3": {
                "bucket": {"name": "rag-documents-bucket"},
                "object": {"key": "test-document.pdf"}
            },
            "eventName": "ObjectCreated:Put",
            "eventTime": "2024-01-01T00:00:00.000Z"
        }
    ]
}

result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
```

**실행:**

```bash
python test_upload_handler.py
```

### query_handler 테스트

API Gateway 요청을 시뮬레이션하여 질의응답 핸들러를 테스트합니다.

**테스트 스크립트:**

```python
# test_query_handler.py
import json
from src.api.query_handler import lambda_handler

# API Gateway 이벤트 시뮬레이션
event = {
    "body": json.dumps({
        "question": "What is Python?",
        "top_k": 5
    })
}

result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
```

**실행:**

```bash
python test_query_handler.py
```

### documents_handler 테스트

문서 목록 조회 핸들러를 테스트합니다.

**테스트 스크립트:**

```python
# test_documents_handler.py
import json
from src.api.documents_handler import lambda_handler

# API Gateway 이벤트 시뮬레이션
event = {
    "queryStringParameters": {
        "limit": "10",
        "offset": "0"
    }
}

result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
```

**실행:**

```bash
python test_documents_handler.py
```

## 환경 설정

로컬 테스트를 위해서는 다음 환경변수를 설정해야 할 수 있습니다:

```bash
export S3_BUCKET_NAME=rag-documents-bucket
export AWS_REGION=ap-northeast-2
export OPENAI_API_KEY=your-api-key  # 선택사항
```

## Mock VectorStore 사용

로컬 테스트에서는 기본적으로 Mock VectorStore가 사용됩니다. 
`configs/config_rag.yaml`에서 `vectorstore.type`을 `mock`으로 설정하세요.

