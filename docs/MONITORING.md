# 모니터링 가이드

이 문서는 Serverless RAG 서비스의 모니터링 및 로깅 설정 방법을 설명합니다.

## CloudWatch Logs

### 로그 그룹

각 Lambda 함수는 자동으로 CloudWatch Logs 그룹이 생성됩니다:

- `/aws/lambda/rag-upload-handler`
- `/aws/lambda/rag-query-handler`
- `/aws/lambda/rag-documents-handler`

### 로그 형식

Lambda 환경에서는 JSON 포맷 로그가 자동으로 사용됩니다:

```json
{
  "timestamp": "2024-01-01T00:00:00.000Z",
  "level": "INFO",
  "logger": "upload_handler",
  "message": "Processing document upload: test-document.pdf"
}
```

### 로그 조회

#### AWS CLI

```bash
# 실시간 로그 스트리밍
aws logs tail /aws/lambda/rag-upload-handler --follow

# 특정 시간대 로그 조회
aws logs filter-log-events \
  --log-group-name /aws/lambda/rag-upload-handler \
  --start-time $(date -d '1 hour ago' +%s)000 \
  --end-time $(date +%s)000

# 에러 로그만 필터링
aws logs filter-log-events \
  --log-group-name /aws/lambda/rag-query-handler \
  --filter-pattern "ERROR"
```

#### CloudWatch Console

1. CloudWatch Console → Logs → Log groups
2. Lambda 함수 로그 그룹 선택
3. Log stream 선택하여 상세 로그 확인

## CloudWatch Metrics

### Lambda 메트릭

#### 주요 메트릭

- **Invocations**: 함수 실행 횟수
- **Errors**: 에러 발생 횟수
- **Duration**: 실행 시간 (밀리초)
- **Throttles**: 스로틀 발생 횟수
- **ConcurrentExecutions**: 동시 실행 수
- **Memory Utilization**: 메모리 사용률

#### 메트릭 조회

```bash
# 최근 1시간 에러 횟수
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=rag-query-handler \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum

# 평균 실행 시간
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=rag-query-handler \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Average
```

### DynamoDB 메트릭

- **ConsumedReadCapacityUnits**: 읽기 용량 사용량
- **ConsumedWriteCapacityUnits**: 쓰기 용량 사용량
- **ThrottledRequests**: 스로틀된 요청 수
- **UserErrors**: 사용자 오류 수

### API Gateway 메트릭

- **Count**: API 호출 횟수
- **4XXError**: 클라이언트 오류
- **5XXError**: 서버 오류
- **Latency**: 응답 지연 시간

## CloudWatch Insights 쿼리

### 기본 쿼리 예시

#### 에러 로그 조회

```
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 100
```

#### 특정 문서 처리 추적

```
fields @timestamp, @message
| filter @message like /document_id/
| parse @message /document_id: (?<doc_id>[a-f0-9-]+)/
| stats count() by doc_id
```

#### 실행 시간 분석

```
fields @timestamp, @duration
| filter @type = "REPORT"
| stats avg(@duration), max(@duration), min(@duration) by bin(5m)
```

#### 에러 타입별 집계

```
fields @timestamp, @message
| filter @message like /ERROR/
| parse @message /(?<error_type>\w+Error): (?<error_msg>.*)/
| stats count() by error_type
```

#### 처리량 분석

```
fields @timestamp
| filter @type = "REPORT"
| stats count() by bin(1m)
```

## CloudWatch 대시보드

### 권장 대시보드 구성

1. **Lambda 함수별 실행 횟수 및 에러율**
2. **평균 실행 시간 추이**
3. **동시 실행 수**
4. **API Gateway 요청 수 및 지연 시간**
5. **DynamoDB 읽기/쓰기 용량 사용률**

### 대시보드 생성

```bash
# 대시보드 JSON 파일 생성 후
aws cloudwatch put-dashboard \
  --dashboard-name "RAG-Service-Dashboard" \
  --dashboard-body file://dashboard.json
```

## 알람 설정

### 권장 알람

#### Lambda 에러율 알람

```bash
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
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:region:account:alerts-topic
```

#### Lambda 실행 시간 알람

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name rag-upload-handler-long-duration \
  --alarm-description "Upload handler duration exceeds 10 minutes" \
  --metric-name Duration \
  --namespace AWS/Lambda \
  --statistic Average \
  --period 300 \
  --threshold 600000 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=FunctionName,Value=rag-upload-handler \
  --evaluation-periods 2
```

#### API Gateway 5XX 에러 알람

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name rag-api-5xx-errors \
  --alarm-description "API Gateway 5XX errors detected" \
  --metric-name 5XXError \
  --namespace AWS/ApiGateway \
  --statistic Sum \
  --period 60 \
  --threshold 1 \
  --comparison-operator GreaterThanThreshold \
  --dimensions Name=ApiName,Value=RagApi \
  --evaluation-periods 1
```

## X-Ray 트레이싱 (선택사항)

분산 추적을 위해 AWS X-Ray를 활성화할 수 있습니다.

### CDK 코드에 추가

```python
# Lambda 함수에 X-Ray 활성화
upload_handler.add_environment("_X_AMZN_TRACE_ID", "enabled")
upload_handler.role.add_managed_policy(
    iam.ManagedPolicy.from_aws_managed_policy_name("AWSXRayDaemonWriteAccess")
)
```

### X-Ray 서비스 맵

X-Ray를 통해 다음을 확인할 수 있습니다:

- S3 이벤트 → Lambda → DynamoDB 호출까지 전체 추적
- 각 단계별 실행 시간
- 병목 지점 식별
- 에러 발생 지점 추적

## 로그 분석 팁

### 성능 분석

1. **Cold Start 확인**: 첫 실행 시간이 긴 경우 Cold Start 발생
2. **메모리 사용률**: CloudWatch 메트릭에서 메모리 사용률 확인
3. **동시 실행 수**: 트래픽 패턴 파악

### 에러 분석

1. **에러 로그 집계**: CloudWatch Insights로 에러 타입별 집계
2. **재시도 패턴**: Dead Letter Queue에서 실패한 요청 확인
3. **에러 발생 시점**: 시간대별 에러 발생 패턴 분석

### 비용 분석

1. **Lambda 실행 횟수**: Invocations 메트릭 확인
2. **실행 시간**: Duration 메트릭으로 컴퓨팅 시간 계산
3. **DynamoDB 용량**: ConsumedReadCapacityUnits/WCU 확인

