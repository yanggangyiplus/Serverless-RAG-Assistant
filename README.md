# Serverless RAG Assistant

AWS Serverless 기반 RAG(Retrieval-Augmented Generation) 서비스

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange.svg)](https://aws.amazon.com/lambda/)
[![LangChain](https://img.shields.io/badge/LangChain-0.1+-green.svg)](https://www.langchain.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 프로젝트 미리보기

*Streamlit 웹 UI 화면 - 문서 업로드 및 RAG 질의응답 인터페이스*

## 핵심 성과 요약

| 항목 | 성과 |
|:---:|:---:|
| **문서 처리** | PDF/TXT/MD 파일 자동 파싱 및 텍스트 추출 |
| **전처리** | 텍스트 정제, 청킹 (크기/오버랩 설정 가능) |
| **임베딩** | LangChain Embeddings (HuggingFace/OpenAI/Bedrock 지원) |
| **벡터 스토어** | DynamoDB 또는 Mock VectorStore (로컬 개발용) |
| **RAG 파이프라인** | LangChain RetrievalQA Chain 기반 질의응답 |
| **API** | Lambda + API Gateway 기반 RESTful API |
| **구현 범위** | 업로드부터 답변 생성까지 End-to-End 파이프라인 |

## 문제 정의 & 해결 목적

문서 기반 질의응답 시스템을 구축하기 위해서는 문서 업로드, 전처리, 임베딩 생성, 벡터 검색, LLM 기반 답변 생성까지의 전체 파이프라인이 필요했습니다. 기존 솔루션들은 각 단계가 분리되어 있거나 서버 관리가 필요한 구조였습니다.

이 프로젝트는 AWS Serverless 아키텍처를 활용하여 완전 자동화된 RAG 서비스를 제공합니다. S3에 문서를 업로드하면 Lambda가 자동으로 트리거되어 전체 파이프라인이 실행되며, API Gateway를 통해 질의응답 API를 제공합니다.

## 프로젝트 개요

### 목적
문서 업로드부터 임베딩 생성, 벡터 검색, LLM 기반 질의응답까지 전체 파이프라인을 구현한 프로덕션 수준의 Serverless RAG 시스템을 구축합니다.

### 주요 특징
- **Serverless 아키텍처**: Lambda + API Gateway + S3 + DynamoDB 기반 완전 Serverless 구조
- **자동화된 파이프라인**: S3 이벤트 기반 자동 문서 처리 및 임베딩 생성
- **다양한 임베딩 지원**: HuggingFace Transformers, OpenAI, AWS Bedrock
- **로컬 개발 지원**: Mock VectorStore를 통한 DynamoDB 없이도 개발 가능
- **RAG 파이프라인**: LangChain 기반 RetrievalQA Chain 구현
- **웹 UI**: Streamlit 기반 문서 업로드 및 질의응답 인터페이스

## 시스템 아키텍처

### 전체 시스템 구조

```
┌─────────────────────────────────────────────────────────────┐
│                    사용자 (User)                             │
└────────────────────────────┬────────────────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │     Streamlit UI (Optional)            │
        │   문서 업로드·질의응답 인터페이스         │
        └────────────────────┬─────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │         API Gateway                     │
        │   /upload /query /documents             │
        └────────────────────┬─────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │         Lambda Functions                │
        │  upload_handler / query_handler /       │
        │  documents_handler                      │
        └────────────────────┬─────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │         S3 Event Trigger                │
        │  문서 업로드 → Lambda 자동 트리거        │
        └────────────────────┬─────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │      Document Processing Pipeline        │
        │  파싱 → 정제 → 청킹 → 임베딩            │
        └────────────────────┬─────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │      Vector Store                       │
        │  DynamoDB / Mock VectorStore            │
        └────────────────────┬─────────────────────┘
                             │
        ┌────────────────────┴────────────────────┐
        │      RAG Pipeline                       │
        │  Retriever → LLM → Answer Generation    │
        └─────────────────────────────────────────┘
```

### 데이터 파이프라인

```
S3 문서 업로드
    │
    ▼
S3 Event → Lambda Trigger
    │
    ▼
┌──────────────────────────┐
│   Document Parsing       │
│  PDF/TXT/MD → Text       │
└───────────┬──────────────┘
            │
            ▼
┌─────────────────────────┐
│   Text Preprocessing    │
│  Cleanup → Chunking     │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Embedding Generation  │
│  LangChain Embeddings   │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Vector Store          │
│  DynamoDB / Mock        │
└───────────┬─────────────┘
            │
            ▼
┌─────────────────────────┐
│   Query Processing      │
│  Embedding → Search →   │
│  RAG → LLM → Answer     │
└─────────────────────────┘
```

## 모델/기술 스택

| 영역 | 기술 | 선택 이유 |
|------|------|----------|
| **Serverless** | AWS Lambda, API Gateway | 서버 관리 없이 자동 스케일링 |
| **Storage** | S3, DynamoDB | 문서 저장 및 벡터 데이터 저장 |
| **RAG Framework** | LangChain | 표준화된 RAG 파이프라인 구축 |
| **Embeddings** | HuggingFace Transformers, OpenAI, Bedrock | 다양한 임베딩 모델 지원 |
| **LLM** | OpenAI GPT, AWS Bedrock | 질의응답 생성 |
| **Document Parsing** | PyPDF2, pdfplumber | PDF/TXT/MD 파일 파싱 |
| **Web UI** | Streamlit | 빠른 프로토타이핑 및 테스트 UI |
| **Infrastructure** | AWS CDK | IaC 기반 인프라 관리 |

## 핵심 기술 설명

### 문서 처리 파이프라인

**S3 이벤트 기반 자동 처리**:
- S3에 문서 업로드 시 Lambda 자동 트리거
- PDF/TXT/MD 파일 자동 인식 및 파싱
- 텍스트 정제 (HTML 제거, 공백 정규화)
- 문서 청킹 (크기/오버랩 설정 가능)

**임베딩 생성**:
- LangChain Embeddings 인터페이스 사용
- HuggingFace Transformers (기본), OpenAI, AWS Bedrock 지원
- 배치 임베딩 생성으로 효율성 향상

### 벡터 스토어

**DynamoDB 벡터 스토어**:
- DynamoDB를 벡터 데이터베이스로 활용
- 문서 ID + 청크 ID 복합 키 구조
- 유사도 검색 (코사인 유사도 기반)

**Mock VectorStore**:
- 로컬 개발/테스트용 인메모리 벡터 스토어
- DynamoDB 없이도 개발 가능

### RAG 파이프라인

**LangChain 기반 구현**:
- RetrievalQA Chain 사용
- 커스텀 프롬프트 템플릿
- 소스 문서 반환 기능

**LLM 지원**:
- OpenAI GPT 모델 (기본)
- AWS Bedrock 모델 지원
- Mock LLM (개발/테스트용)

## 실행 방법

### Quick Start

```bash
# 저장소 클론
git clone https://github.com/yanggangyiplus/Serverless-RAG-Assistant.git
cd Serverless-RAG-Assistant

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install --upgrade pip
pip install -r requirements.txt

# 테스트 실행 (선택사항)
pytest  # 또는 ./scripts/run_tests.sh

# Streamlit UI 실행
streamlit run app/web/main.py --server.port 8501
```

**실행 시간**: 약 10초 내 완료 가능

### 상세 설치 가이드

1. **저장소 클론**
```bash
git clone https://github.com/yanggangyiplus/Serverless-RAG-Assistant.git
cd Serverless-RAG-Assistant
```

2. **가상환경 생성 및 활성화**
```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
```

3. **의존성 설치**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

4. **설정 파일 구성**
   - `configs/config_rag.yaml`: 전체 서비스 설정
     - S3 버킷 설정
     - 전처리 설정 (청크 크기, 오버랩)
     - 임베딩 모델 설정
     - 벡터 스토어 설정
     - LLM 설정

### 로컬 개발

로컬 개발 환경에서는 Mock VectorStore를 사용하여 DynamoDB 없이도 개발할 수 있습니다.

```bash
# Streamlit UI 실행 (로컬 모드)
streamlit run app/web/main.py --server.port 8501
```

### Streamlit Cloud 배포

Streamlit Cloud를 통한 배포:

1. GitHub 저장소에 코드 푸시
2. [Streamlit Cloud](https://streamlit.io/cloud)에서 저장소 연결
3. Main file path: `app/web/main.py` 지정
4. 배포 완료 후 자동으로 웹 URL 생성

**주의사항**:
- Streamlit Cloud는 무료 플랜에서 1GB 메모리 제한
- Lambda API 연동 시 CORS 설정 필요
- 로컬 모드 사용 시 Mock VectorStore 자동 활성화

## 사용 시나리오 (Use Cases)

### 1. 문서 기반 질의응답 시스템
**시나리오**: 회사 내부 문서, 매뉴얼, 지식 베이스를 업로드하고 직원들이 자연어로 질문하여 답변을 받고 싶을 때  
**해결책**: 문서 업로드 → 자동 임베딩 생성 → 벡터 스토어 저장 → RAG 기반 질의응답  
**효과**: 문서 검색 시간 단축, 정확한 답변 제공

### 2. 고객 지원 자동화
**시나리오**: FAQ 문서, 제품 매뉴얼을 업로드하여 고객 문의에 자동으로 답변하고 싶을 때  
**해결책**: FAQ 문서 업로드 → RAG 파이프라인을 통한 자동 답변 생성  
**효과**: 고객 지원 부담 감소, 24/7 자동 응답 가능

### 3. 연구 논문 분석
**시나리오**: 연구 논문 PDF를 업로드하고 특정 주제에 대한 질문에 답변을 받고 싶을 때  
**해결책**: 논문 업로드 → 청킹 및 임베딩 생성 → 유사도 검색 기반 답변 생성  
**효과**: 논문 내용 빠른 파악, 관련 내용 자동 추출

### 4. 법률 문서 검색
**시나리오**: 법률 문서, 판례를 업로드하고 특정 법률 조항이나 판례를 검색하고 싶을 때  
**해결책**: 법률 문서 업로드 → 벡터 검색 기반 관련 조항/판례 자동 추출  
**효과**: 법률 문서 검색 시간 단축, 관련 내용 정확한 추출

## 한계 & 개선 방향

### 현재 한계

- **DynamoDB 벡터 검색**: DynamoDB는 벡터 검색에 최적화되지 않음 (전체 스캔 필요)
- **대용량 문서 처리**: 대용량 문서 처리 시 Lambda 타임아웃 가능성
- **실시간 스트리밍**: 실시간 스트리밍 미지원 (배치 처리 기반)
- **멀티모달 지원**: 이미지, 표 등 멀티모달 데이터 미지원

### 개선 방향

- **v1**: Amazon OpenSearch 또는 Pinecone 등 전용 벡터 DB 통합
- **v2**: Step Functions를 활용한 대용량 문서 처리 파이프라인
- **v3**: 실시간 스트리밍 파이프라인 (Kinesis + Lambda)
- **v4**: 멀티모달 지원 (이미지, 표 등)
- **v5**: Fine-tuning된 임베딩 모델 적용으로 성능 향상

## 개인 기여도

이 프로젝트는 **개인 프로젝트**로, 모든 작업을 직접 수행했습니다.

### 엔드투엔드 파이프라인 설계
- S3 업로드 → Lambda 트리거 → 문서 파싱 → 전처리 → 임베딩 → 벡터 스토어 저장 → 검색 → RAG → 답변 생성까지 풀 사이클 개발
- Collector / Preprocessing / Embeddings / VectorStore / RAG 계층 완전 분리 구성
- 재사용성과 유지보수성 높은 구조 설계

### Serverless 아키텍처 설계
- Lambda + API Gateway + S3 + DynamoDB 기반 완전 Serverless 구조 설계
- S3 이벤트 기반 자동 트리거 파이프라인 구현
- API Gateway 통합 및 CORS 설정

### IaC 구현
- AWS CDK를 통한 인프라 코드화 및 자동 배포 파이프라인 구축
- Lambda 함수, API Gateway, S3 버킷, DynamoDB 테이블 자동 생성
- 환경 변수 및 IAM 권한 자동 설정

### CI/CD 파이프라인
- GitHub Actions를 통한 자동화된 테스트 및 배포 시스템 구현
- 코드 품질 검사 (black, isort, flake8)
- 자동 배포 워크플로우 구성

### 문서 처리 파이프라인
- PDF/TXT/MD 파일 파싱 로직 직접 구현
- 텍스트 정제, 청킹 로직 구현
- 다양한 파일 형식 지원 확장 가능한 구조 설계

### RAG 파이프라인 구현
- LangChain 기반 Retriever, RetrievalQA Chain 구현
- 커스텀 프롬프트 템플릿 설계
- 소스 문서 반환 기능 구현

### 벡터 스토어 추상화
- DynamoDB 및 Mock VectorStore 인터페이스 설계 및 구현
- 벡터 스토어 추상화로 다른 벡터 DB 통합 가능한 구조
- 유사도 검색 알고리즘 구현

### Lambda 핸들러 구현
- upload_handler, query_handler, documents_handler 직접 구현
- API Gateway 통합 및 에러 처리
- 통일된 응답 형식 설계

### 웹 UI 구현
- Streamlit 기반 문서 업로드 및 질의응답 인터페이스 구현
- 로컬 모드 및 API 모드 병행 지원
- 사용자 친화적인 UI/UX 설계

### 문서화
- 아키텍처 문서 작성
- 설치·실행 가이드 작성
- API 문서 작성
- 배포 가이드 작성

## 프로젝트 구조

```
Serverless-RAG-Assistant/
├── app/                    # 웹 애플리케이션
│   └── web/               # Streamlit UI
│       └── main.py        # Streamlit 웹 데모
├── aws_lambda/             # Lambda 배포용 코드
│   └── rag_lambda/
│       └── app.py         # Lambda 핸들러 통합
├── configs/               # 설정 파일
│   └── config_rag.yaml    # 전체 서비스 설정
├── infrastructure/        # IaC (AWS CDK)
│   └── cdk/              # CDK 인프라 코드
│       ├── app.py
│       └── rag_serverless_stack.py
├── src/                  # 소스 코드
│   ├── api/              # Lambda 핸들러
│   │   ├── upload_handler.py
│   │   └── query_handler.py
│   ├── embeddings/       # 임베딩
│   │   └── embedder.py
│   ├── ingestion/        # 문서 수집
│   │   ├── parser.py
│   │   └── s3_handler.py
│   ├── preprocessing/    # 전처리
│   │   ├── cleaner.py
│   │   └── chunker.py
│   ├── rag/              # RAG 파이프라인
│   │   ├── pipeline.py
│   │   └── retriever.py
│   ├── services/         # 서비스 레이어
│   │   ├── ingestion_service.py
│   │   └── rag_service.py
│   ├── vectorstore/      # 벡터 스토어
│   │   ├── base.py
│   │   ├── dynamodb_store.py
│   │   └── mock_store.py
│   └── utils/            # 유틸리티
│       ├── config.py
│       ├── errors.py
│       ├── logger.py
│       └── response.py
├── tests/                 # 테스트 코드
│   ├── test_embeddings.py
│   ├── test_preprocessing.py
│   ├── test_rag_pipeline.py
│   └── test_vectorstore.py
├── scripts/               # 실행 스크립트
│   └── run_tests.sh
├── docs/                  # 문서
│   ├── DEPLOYMENT_AWS.md
│   ├── LOCAL_TESTING.md
│   ├── MONITORING.md
│   └── TESTING.md
├── README.md              # 프로젝트 설명
├── QUICK_START.md         # 빠른 시작 가이드
├── requirements.txt       # 의존성 목록
└── pytest.ini             # pytest 설정
```

## 테스트

### 빠른 시작

```bash
# 테스트 실행 스크립트 사용 (권장)
./scripts/run_tests.sh

# 또는 수동 실행
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pytest
```

### 테스트 실행

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함
pytest --cov=src --cov-report=html

# 특정 모듈 테스트
pytest tests/test_preprocessing.py
pytest tests/test_embeddings.py
pytest tests/test_vectorstore.py
pytest tests/test_rag_pipeline.py

# 상세 출력
pytest -v

# 실패한 테스트만 재실행
pytest --lf
```

## ☁️ Level 3 — AWS Serverless 배포

이 프로젝트는 Local RAG 시스템에서 한 단계 더 나아가, **AWS Serverless 환경에 올릴 수 있도록 설계**되었습니다. Lambda + API Gateway + S3 + DynamoDB + GitHub Actions CI/CD를 통한 완전 자동화된 배포 파이프라인을 제공합니다.

### 인프라 구성

**AWS CDK 기반 IaC**로 다음 리소스를 자동 생성:

- **S3 버킷**: 문서 업로드 저장 및 이벤트 트리거
- **Lambda 함수 3개**: upload_handler, query_handler, documents_handler
- **API Gateway**: RESTful API 엔드포인트 (`/rag/query`, `/rag/documents`)
- **DynamoDB**: 벡터 스토어 및 문서 메타데이터 저장
- **CloudWatch Logs**: Lambda 함수 로그 자동 수집

### 배포 방법

#### 방법 1: CDK 수동 배포

```bash
# CDK 부트스트랩 (최초 1회)
cd infrastructure/cdk
pip install -r requirements.txt
cdk bootstrap

# 인프라 배포
cdk deploy
```

#### 방법 2: GitHub Actions 자동 배포

`main` 브랜치에 푸시하면 자동으로 배포됩니다:

```bash
git push origin main
```

GitHub Secrets 설정 필요:
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_REGION`

### 배포 후 확인

배포 완료 후 출력되는 정보:

- **API 엔드포인트**: `https://{api-id}.execute-api.{region}.amazonaws.com/prod/rag/`
- **S3 버킷 이름**: 문서 업로드용
- **DynamoDB 테이블**: 벡터 스토어

### 상세 배포 가이드

전체 배포 과정 및 운영 가이드는 [배포 문서](docs/DEPLOYMENT_AWS.md)를 참조하세요.

**주요 내용**:
- CDK 기반 인프라 배포 방법
- GitHub Actions 자동 배포 설정
- 비용 모델 및 최적화 전략
- Serverless Best Practices
- CloudWatch 모니터링 및 알람 설정

## 라이선스 & 작성자

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

**작성자**: yanggangyi

- GitHub: [@yanggangyiplus](https://github.com/yanggangyiplus)

## 상세 문서

### 핵심 문서
- [빠른 시작 가이드](QUICK_START.md) - 빠른 설치 및 실행 방법
- [AWS 배포 가이드](docs/DEPLOYMENT_AWS.md) - AWS Serverless 환경 배포 방법

### 추가 문서
- [테스트 가이드](docs/TESTING.md) - 테스트 실행 방법 및 테스트 구조 설명
- [로컬 테스트 가이드](docs/LOCAL_TESTING.md) - Lambda 함수 로컬 테스트 방법
- [모니터링 가이드](docs/MONITORING.md) - CloudWatch 로그 및 메트릭 모니터링 방법
