# 테스트 가이드

이 문서는 Serverless RAG Assistant 프로젝트의 테스트 실행 방법을 설명합니다.

## 테스트 구조

```
tests/
├── test_preprocessing.py    # 전처리 모듈 테스트
├── test_embeddings.py       # 임베딩 모듈 테스트
├── test_vectorstore.py      # 벡터 스토어 테스트
└── test_rag_pipeline.py    # RAG 파이프라인 테스트
```

## 테스트 실행

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

### 전체 테스트 실행

```bash
# 기본 실행
pytest

# 상세 출력
pytest -v

# 특정 모듈 테스트
pytest tests/test_preprocessing.py
pytest tests/test_embeddings.py
pytest tests/test_vectorstore.py
pytest tests/test_rag_pipeline.py
```

### 커버리지 포함

```bash
pytest --cov=src --cov-report=html
```

HTML 리포트는 `htmlcov/index.html`에서 확인할 수 있습니다.

### 테스트 실행 확인

로컬에서 테스트가 정상적으로 실행되는지 확인:

```bash
# Python 버전 확인 (3.11 이상 필요)
python3 --version

# pytest 설치 확인
pytest --version

# 간단한 테스트 실행
pytest tests/test_preprocessing.py::TestTextCleaner::test_html_tag_removal -v
```

## 테스트 내용

### 전처리 테스트 (`test_preprocessing.py`)

- HTML 태그 제거
- 공백 정규화
- 특수 문자 처리
- Edge case (빈 문자열, None 등)
- 문서 청킹 (크기, 오버랩)
- 메타데이터 보존

### 임베딩 테스트 (`test_embeddings.py`)

- 단일 텍스트 임베딩
- 배치 임베딩 생성
- 일관성 검증
- 차원 검증
- Mock 임베딩 정규화

### 벡터 스토어 테스트 (`test_vectorstore.py`)

- 문서 추가/조회/삭제
- 유사도 검색 (Top-K)
- 메타데이터 필터링
- 빈 스토어 처리

### RAG 파이프라인 테스트 (`test_rag_pipeline.py`)

- Retriever 동작 검증
- Pipeline 질의응답
- 컨텍스트 처리
- 에러 처리

## Mock 사용

테스트에서는 실제 LLM이나 벡터 스토어를 호출하지 않고 Mock을 사용합니다:

- **임베딩**: Mock 임베딩 생성기 사용
- **벡터 스토어**: MockVectorStore 사용
- **LLM**: Mock LLM 사용

이를 통해 빠르고 안정적인 테스트가 가능합니다.

