# AWS CDK 인프라 코드

이 디렉토리는 AWS CDK를 사용한 Serverless RAG 서비스 인프라 정의를 포함합니다.

## 구조

- `app.py`: CDK 앱 진입점
- `rag_serverless_stack.py`: RAG 서비스 인프라 스택 정의
- `cdk.json`: CDK 설정 파일
- `requirements.txt`: CDK Python 의존성

## 배포된 리소스

### S3
- 문서 업로드용 버킷
- S3 이벤트 알림 (PDF/TXT/MD 파일 업로드 시 Lambda 트리거)

### Lambda Functions
- `rag-upload-handler`: S3 이벤트 기반 문서 처리
- `rag-query-handler`: RAG 질의응답 API
- `rag-documents-handler`: 문서 목록 조회 API

### API Gateway
- REST API 엔드포인트:
  - `POST /rag/query`: 질의응답
  - `GET /rag/documents`: 문서 목록 조회

### DynamoDB
- 벡터 스토어 테이블 (`rag-documents`)
- GSI: 문서 ID 기반 조회 최적화

### CloudWatch Logs
- Lambda 함수 로그 그룹 (14일 보관)

## 배포 방법

### 사전 요구사항

```bash
# AWS CLI 설치 및 설정
aws configure

# CDK 설치
npm install -g aws-cdk

# CDK 부트스트랩 (최초 1회)
cdk bootstrap
```

### 로컬 배포

```bash
# 의존성 설치
cd infrastructure/cdk
pip install -r requirements.txt

# 인프라 검증
cdk synth

# 배포
cdk deploy
```

### 환경 변수 설정

Lambda 함수에 필요한 환경 변수는 CDK 스택에서 자동 설정됩니다.
추가 환경 변수(예: `OPENAI_API_KEY`)는 AWS Systems Manager Parameter Store 또는 Secrets Manager를 통해 설정하세요.

## 리소스 정리

```bash
cdk destroy
```

