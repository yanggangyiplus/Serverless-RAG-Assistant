# AWS Serverless 배포 가이드

이 문서는 Serverless RAG Assistant를 AWS 환경에 배포하는 방법을 설명합니다.

## 사전 요구사항

### AWS 계정 및 권한

- AWS 계정 및 적절한 IAM 권한
- 다음 리소스 생성/관리 권한:
  - Lambda 함수
  - API Gateway
  - S3 버킷
  - DynamoDB 테이블
  - CloudWatch Logs
  - IAM 역할 및 정책

### 로컬 환경 설정

```bash
# AWS CLI 설치 및 설정
aws configure

# AWS CDK 설치
npm install -g aws-cdk

# Python 3.11 이상
python --version
```

### GitHub Secrets 설정 (CI/CD 사용 시)

다음 Secrets를 GitHub 저장소에 설정:

- `AWS_ACCESS_KEY_ID`: AWS 액세스 키 ID
- `AWS_SECRET_ACCESS_KEY`: AWS 시크릿 액세스 키
- `AWS_REGION`: AWS 리전 (기본값: `ap-northeast-2`)
- `LLM_PROVIDER`: LLM 제공자 (선택사항, 기본값: `openai`)

## 배포 방법

### 방법 1: CDK를 통한 수동 배포

#### 1단계: CDK 부트스트랩 (최초 1회)

```bash
cd infrastructure/cdk
cdk bootstrap
```

#### 2단계: 인프라 검증

```bash
# CDK 의존성 설치
pip install -r requirements.txt

# 인프라 코드 검증
cdk synth
```

#### 3단계: 배포

```bash
# 인프라 배포
cdk deploy

# 배포 확인
cdk list
```

배포가 완료되면 다음 정보가 출력됩니다:

- `ApiEndpoint`: API Gateway 엔드포인트 URL
- `DocumentsBucketName`: S3 버킷 이름
- `VectorStoreTableName`: DynamoDB 테이블 이름
- Lambda 함수 이름들

### 방법 2: GitHub Actions를 통한 자동 배포

#### 설정

1. GitHub 저장소에 Secrets 설정 (위 참조)

2. `main` 브랜치에 푸시하면 자동 배포:

```bash
git add .
git commit -m "Deploy to AWS"
git push origin main
```

3. GitHub Actions 탭에서 배포 진행 상황 확인

#### 배포 후 확인

배포가 완료되면 GitHub Actions 로그에서 다음을 확인:

- CDK Synth 성공 여부
- CDK Deploy 성공 여부
- 출력된 리소스 정보

## 배포된 인프라 구조

### S3 버킷

- **이름**: `rag-documents-{account}-{region}`
- **용도**: 문서 업로드 저장
- **이벤트**: PDF/TXT/MD 파일 업로드 시 Lambda 자동 트리거

### Lambda 함수

#### rag-upload-handler
- **트리거**: S3 이벤트 (ObjectCreated)
- **타임아웃**: 15분
- **메모리**: 1024 MB
- **역할**: 문서 파싱, 전처리, 임베딩 생성, 벡터 스토어 저장

#### rag-query-handler
- **트리거**: API Gateway (`POST /rag/query`)
- **타임아웃**: 5분
- **메모리**: 512 MB
- **역할**: RAG 질의응답 처리

#### rag-documents-handler
- **트리거**: API Gateway (`GET /rag/documents`)
- **타임아웃**: 30초
- **메모리**: 256 MB
- **역할**: 문서 목록 조회

### API Gateway

- **엔드포인트**: `https://{api-id}.execute-api.{region}.amazonaws.com/prod/rag/`
- **엔드포인트**:
  - `POST /rag/query`: 질의응답
  - `GET /rag/documents`: 문서 목록 조회
- **CORS**: 모든 오리진 허용 (프로덕션에서는 제한 권장)

### DynamoDB

- **테이블명**: `rag-documents`
- **키 구조**:
  - Partition Key: `document_id`
  - Sort Key: `chunk_id`
- **GSI**: `document-id-index`
- **빌링 모드**: Pay-per-Request

## 환경 변수 설정

Lambda 함수는 다음 환경 변수를 자동으로 설정받습니다:

- `BUCKET_NAME`: S3 버킷 이름
- `VECTORSTORE_TABLE_NAME`: DynamoDB 테이블 이름
- `VECTORSTORE_BACKEND`: `dynamodb`
- `LOG_LEVEL`: `INFO`
- `EMBEDDING_MODEL_NAME`: 임베딩 모델 이름
- `AWS_REGION`: AWS 리전

### 추가 환경 변수 설정

OpenAI API 키 등 민감한 정보는 AWS Systems Manager Parameter Store 또는 Secrets Manager를 사용하세요:

```bash
# Parameter Store에 저장
aws ssm put-parameter \
  --name "/rag/openai-api-key" \
  --value "your-api-key" \
  --type "SecureString"

# Lambda 함수에서 읽기 (코드 수정 필요)
```

## 테스트

### API 엔드포인트 테스트

```bash
# API 엔드포인트 확인
API_URL=$(aws cloudformation describe-stacks \
  --stack-name RagServerlessStack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiEndpoint`].OutputValue' \
  --output text)

# 질의응답 테스트
curl -X POST "${API_URL}rag/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Python?"}'

# 문서 목록 조회 테스트
curl "${API_URL}rag/documents?limit=10"
```

### S3 업로드 테스트

```bash
# 버킷 이름 확인
BUCKET_NAME=$(aws cloudformation describe-stacks \
  --stack-name RagServerlessStack \
  --query 'Stacks[0].Outputs[?OutputKey==`DocumentsBucketName`].OutputValue' \
  --output text)

# 문서 업로드
aws s3 cp test-document.pdf "s3://${BUCKET_NAME}/"

# Lambda 함수 로그 확인
aws logs tail /aws/lambda/rag-upload-handler --follow
```

## 모니터링 및 로깅

### CloudWatch Logs

각 Lambda 함수의 로그는 CloudWatch Logs에 자동 저장됩니다:

- `/aws/lambda/rag-upload-handler`
- `/aws/lambda/rag-query-handler`
- `/aws/lambda/rag-documents-handler`

**로그 보관 기간**: 14일 (CDK에서 설정)

**로그 조회 예시**:

```bash
# 최근 로그 확인
aws logs tail /aws/lambda/rag-upload-handler --follow

# 특정 시간대 로그 조회
aws logs filter-log-events \
  --log-group-name /aws/lambda/rag-upload-handler \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --filter-pattern "ERROR"

# JSON 형식 로그 파싱
aws logs tail /aws/lambda/rag-query-handler | jq '.message'
```

**로그 형식**:
- Lambda 환경에서는 JSON 포맷 로그 사용 (자동 감지)
- 구조화된 로그로 CloudWatch Insights에서 효율적 쿼리 가능

### CloudWatch Metrics

다음 메트릭을 모니터링할 수 있습니다:

#### Lambda 메트릭

- **Invocations**: 함수 실행 횟수
- **Errors**: 에러 발생 횟수
- **Duration**: 실행 시간 (평균, 최대, 최소)
- **Throttles**: 스로틀 발생 횟수
- **ConcurrentExecutions**: 동시 실행 수
- **Memory Utilization**: 메모리 사용률

**메트릭 조회 예시**:

```bash
# 최근 1시간 에러율 확인
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=rag-query-handler \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

#### DynamoDB 메트릭

- **ConsumedReadCapacityUnits**: 읽기 용량 사용량
- **ConsumedWriteCapacityUnits**: 쓰기 용량 사용량
- **ThrottledRequests**: 스로틀된 요청 수
- **UserErrors**: 사용자 오류 수

#### API Gateway 메트릭

- **Count**: API 호출 횟수
- **4XXError**: 클라이언트 오류
- **5XXError**: 서버 오류
- **Latency**: 응답 지연 시간

### CloudWatch Insights 쿼리 예시

**에러 로그 조회**:
```
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```

**특정 문서 처리 시간 분석**:
```
fields @timestamp, @message
| filter @message like /document_id/
| parse @message /document_id: (?<doc_id>[a-f0-9-]+)/
| stats avg(@duration) by doc_id
```

**에러 타입별 집계**:
```
fields @timestamp, @message
| filter @message like /ERROR/
| parse @message /(?<error_type>\w+Error): (?<error_msg>.*)/
| stats count() by error_type
```

### CloudWatch 대시보드 생성

**권장 대시보드 메트릭**:

1. **Lambda 함수별 실행 횟수 및 에러율**
2. **평균 실행 시간 추이**
3. **동시 실행 수**
4. **API Gateway 요청 수 및 지연 시간**
5. **DynamoDB 읽기/쓰기 용량 사용률**

**대시보드 생성 예시**:

```bash
# CloudWatch 대시보드 JSON 생성 (수동 또는 CDK로 자동화 가능)
aws cloudwatch put-dashboard \
  --dashboard-name "RAG-Service-Dashboard" \
  --dashboard-body file://dashboard.json
```

### 알람 설정

**권장 알람**:

1. **Lambda 에러율 알람**: 에러율이 5% 초과 시 알림
2. **Lambda 실행 시간 알람**: 평균 실행 시간이 타임아웃의 80% 초과 시
3. **API Gateway 5XX 에러 알람**: 서버 오류 발생 시
4. **DynamoDB 스로틀 알람**: 스로틀 발생 시

**알람 생성 예시**:

```bash
# Lambda 에러율 알람
aws cloudwatch put-metric-alarm \
  --alarm-name rag-query-handler-high-error-rate \
  --alarm-description "Query handler error rate exceeds 5%" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=rag-query-handler \
  --evaluation-periods 1
```

### X-Ray 트레이싱 (선택사항)

분산 추적을 위해 AWS X-Ray 활성화:

```python
# CDK 코드에 추가
upload_handler.add_environment("_X_AMZN_TRACE_ID", "enabled")
upload_handler.role.add_managed_policy(
    iam.ManagedPolicy.from_aws_managed_policy_name("AWSXRayDaemonWriteAccess")
)
```

X-Ray를 통해 전체 요청 플로우 추적 가능:
- S3 이벤트 → Lambda → DynamoDB 호출까지 전체 추적
- 병목 지점 식별 및 성능 최적화

## 롤백 및 수정

### 롤백

```bash
cd infrastructure/cdk
cdk destroy
```

**주의**: 이 명령은 모든 리소스를 삭제합니다. 프로덕션 환경에서는 신중하게 사용하세요.

### 수정 사항 배포

인프라 코드를 수정한 후:

```bash
cd infrastructure/cdk
cdk diff  # 변경 사항 확인
cdk deploy  # 배포
```

## 비용 모델 및 최적화

### 예상 비용 (소규모 사용 기준)

#### Lambda

- **무료 티어**: 매월 1M 요청, 400,000 GB-초 컴퓨팅 시간
- **과금**: 
  - 요청: 1M 요청당 $0.20
  - 실행 시간: 128MB 기준 GB-초당 $0.0000166667
  - 예시: 1M 요청, 평균 1초 실행, 512MB 메모리 = 약 $0.20 + $0.08 = $0.28/월

#### DynamoDB

- **무료 티어**: 
  - 25GB 스토리지
  - 25 RCU (Read Capacity Units)
  - 25 WCU (Write Capacity Units)
- **On-Demand 모드**: 
  - 읽기: 1M 요청당 $0.25
  - 쓰기: 1M 요청당 $1.25
  - 스토리지: GB당 $0.25/월

#### S3

- **무료 티어**: 5GB 스토리지, 20,000 GET 요청, 2,000 PUT 요청
- **과금**: 
  - 스토리지: GB당 $0.023/월 (표준 스토리지)
  - 요청: 1,000 GET 요청당 $0.0004, 1,000 PUT 요청당 $0.005

#### API Gateway

- **무료 티어**: 1M API 호출/월
- **과금**: 1M 호출당 $3.50

**소규모 사용 예상 비용 (월 10만 문서 처리, 1만 질의응답)**: 약 $5-10/월

### 비용 최적화 전략

#### Lambda

- **메모리 크기 조정**: 실제 사용량에 맞게 조정 (CloudWatch 메트릭 확인)
- **예약 동시성**: 트래픽 예측 가능 시 예약 동시성으로 비용 절감
- **프로비저닝된 동시성**: Cold start 최소화 및 성능 향상
- **Lambda Layer**: 공통 의존성을 Layer로 분리하여 배포 패키지 크기 감소

#### DynamoDB

- **On-Demand → 프로비저닝 전환**: 트래픽 패턴이 예측 가능한 경우
- **GSI 최소화**: 필요한 인덱스만 생성
- **TTL 설정**: 오래된 데이터 자동 삭제로 스토리지 비용 절감

#### S3

- **수명 주기 정책**: 
  - 30일 후 IA (Infrequent Access)로 전환
  - 90일 후 Glacier로 아카이빙
  - 365일 후 삭제
- **스토리지 클래스 최적화**: 접근 빈도에 따라 적절한 클래스 선택

#### API Gateway

- **캐싱**: 자주 조회되는 엔드포인트에 캐싱 적용
- **Throttling**: 무분별한 요청 방지

## Serverless Best Practices

### Cold Start 최적화

**문제**: Lambda 함수가 처음 실행되거나 일정 시간 비활성 후 재실행 시 초기화 시간 발생

**해결책**:
1. **프로비저닝된 동시성**: 항상 실행 중인 인스턴스 유지
2. **Lambda Layer 활용**: 공통 의존성을 Layer로 분리하여 초기화 시간 단축
3. **메모리 크기 최적화**: 충분한 메모리 할당 (CPU 성능도 함께 증가)
4. **최소 패키지 크기**: 불필요한 파일 제외, 의존성 최소화

**현재 구현**:
- 임베딩 모델은 Lambda Layer 또는 EFS로 분리 권장
- 공통 유틸리티는 Layer로 분리 가능

### Lambda Layer 활용

```python
# 공통 의존성을 Layer로 분리 예시
# infrastructure/cdk/rag_serverless_stack.py에 추가 가능

common_layer = _lambda.LayerVersion(
    self,
    "CommonLayer",
    code=_lambda.Code.from_asset("layers/common"),
    compatible_runtimes=[_lambda.Runtime.PYTHON_3_11],
    description="공통 유틸리티 및 의존성"
)

# Lambda 함수에 Layer 추가
upload_handler.add_layers(common_layer)
```

### DynamoDB 파티션 키 설계

**현재 설계**:
- Partition Key: `document_id`
- Sort Key: `chunk_id`

**설계 기준**:
1. **균등한 분산**: 문서 ID가 고르게 분산되도록 UUID 사용
2. **핫 파티션 방지**: 특정 문서에 대한 집중 조회 시 파티션 분산 고려
3. **쿼리 패턴 고려**: 
   - 문서별 조회: `document_id`로 효율적
   - 전체 스캔: GSI 활용 또는 다른 접근 방식 고려

**개선 가능성**:
- 시간 기반 파티션 키 추가 (날짜별 문서 분리)
- 사용자별 파티션 키 (멀티테넌트 지원)

### API Gateway 설정 최적화

#### CORS 설정

**현재**: 모든 오리진 허용 (개발 환경)

**프로덕션 권장**:
```python
# CDK 코드에서 수정
default_cors_preflight_options=apigateway.CorsOptions(
    allow_origins=["https://yourdomain.com"],  # 특정 도메인만
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=Duration.days(1)
)
```

#### Throttling 설정

```python
# API Gateway에 Throttle 설정 추가
api.add_usage_plan(
    "RagUsagePlan",
    throttle=apigateway.ThrottleSettings(
        rate_limit=100,  # 초당 요청 수
        burst_limit=200  # 버스트 요청 수
    )
)
```

#### 캐싱

자주 조회되는 엔드포인트에 캐싱 적용:

```python
# documents_handler에 캐싱 추가
documents_resource.add_method(
    "GET",
    apigateway.LambdaIntegration(documents_handler),
    method_options=apigateway.MethodOptions(
        caching=apigateway.CachingConfig(
            ttl=Duration.minutes(5),  # 5분 캐시
            cache_key_parameters=["method.request.querystring.limit"]
        )
    )
)
```

### 에러 처리 및 재시도

**Lambda 함수 재시도 설정**:
- S3 이벤트: 기본적으로 3회 재시도
- API Gateway: Lambda 함수 실패 시 재시도 정책 설정 가능

**Dead Letter Queue (DLQ)**:
```python
# 실패한 요청을 DLQ로 전송
upload_handler.add_dead_letter_queue(
    queue=dynamodb.Queue.from_queue_arn(
        self, "DLQ", queue_arn="arn:aws:sqs:..."
    ),
    max_receive_count=3
)
```

## 보안 고려사항

### 프로덕션 환경 권장 사항

1. **CORS 제한**: API Gateway에서 특정 도메인만 허용
2. **API 키 인증**: API Gateway에 API 키 추가
3. **VPC 설정**: Lambda 함수를 VPC 내부에 배치 (필요 시)
4. **Secrets Manager**: 민감한 정보는 Secrets Manager 사용
5. **IAM 최소 권한**: Lambda 역할에 최소한의 권한만 부여
6. **WAF (Web Application Firewall)**: API Gateway 앞단에 WAF 배치
7. **암호화**: S3 버킷 및 DynamoDB 테이블 암호화 활성화

## 문제 해결

### 일반적인 문제

1. **CDK 부트스트랩 실패**
   - AWS 자격 증명 확인
   - 리전 설정 확인

2. **Lambda 함수 타임아웃**
   - 타임아웃 시간 증가 (CDK 코드 수정)
   - 메모리 크기 증가

3. **S3 이벤트 트리거 안 됨**
   - 버킷 이벤트 알림 설정 확인
   - Lambda 함수 권한 확인

4. **API Gateway CORS 오류**
   - CORS 설정 확인
   - 응답 헤더 확인

## 추가 리소스

- [AWS CDK 문서](https://docs.aws.amazon.com/cdk/)
- [Lambda 문서](https://docs.aws.amazon.com/lambda/)
- [API Gateway 문서](https://docs.aws.amazon.com/apigateway/)

