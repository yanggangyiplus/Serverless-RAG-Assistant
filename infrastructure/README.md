# Infrastructure as Code

이 디렉토리는 AWS 인프라스트럭처를 코드로 정의하는 IaC 파일들을 포함합니다.

## 지원 도구

- **AWS CDK**: TypeScript/Python 기반 인프라 정의
- **Terraform**: HCL 기반 인프라 정의

## 배포 구조

### Lambda Functions
- `upload_handler`: S3 이벤트 트리거, 문서 처리 파이프라인 실행
- `query_handler`: API Gateway 연동, 질의응답 처리
- `documents_handler`: API Gateway 연동, 문서 목록 조회

### API Gateway
- `/upload`: 문서 업로드 엔드포인트
- `/query`: 질의응답 엔드포인트
- `/documents`: 문서 목록 조회 엔드포인트

### S3
- 문서 저장 버킷
- S3 이벤트 알림 설정

### DynamoDB
- 벡터 문서 저장 테이블
- GSI 설정 (문서 ID 기반)

## 배포 방법

### CDK 사용
```bash
cd infrastructure/cdk
npm install
cdk deploy
```

### Terraform 사용
```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

