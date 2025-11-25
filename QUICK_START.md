# 빠른 시작 가이드

로컬에서 프로젝트를 빠르게 시작하는 방법입니다.

## 사전 요구사항

- Python 3.11 이상
- pip (Python 패키지 관리자)

## 1. 저장소 클론

```bash
git clone https://github.com/yanggangyiplus/Serverless-RAG-Assistant.git
cd Serverless-RAG-Assistant
```

## 2. 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화
# macOS/Linux:
source venv/bin/activate
# Windows:
# venv\Scripts\activate
```

## 3. 의존성 설치

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**참고**: 일부 의존성(예: torch, sentence-transformers)은 설치에 시간이 걸릴 수 있습니다.

## 4. 테스트 실행

```bash
# 전체 테스트 실행
pytest

# 또는 테스트 스크립트 사용
./scripts/run_tests.sh

# 특정 테스트만 실행
pytest tests/test_preprocessing.py -v
```

## 5. Streamlit UI 실행 (선택사항)

```bash
streamlit run app/web/main.py --server.port 8501
```

브라우저에서 `http://localhost:8501` 접속

## 6. Lambda 함수 로컬 테스트

```bash
# Python으로 직접 테스트
python3 -c "
from src.api.query_handler import lambda_handler
import json

event = {'body': json.dumps({'question': 'What is Python?'})}
result = lambda_handler(event, None)
print(json.dumps(result, indent=2))
"
```

## 문제 해결

### 의존성 설치 오류

```bash
# 시스템 패키지 관리자 사용 (macOS)
brew install python@3.11

# 또는 pyenv 사용
pyenv install 3.11.0
pyenv local 3.11.0
```

### 테스트 실패

- Python 버전 확인: `python3 --version` (3.11 이상 필요)
- 가상환경 활성화 확인: `which python` (venv 경로여야 함)
- 의존성 재설치: `pip install -r requirements.txt --force-reinstall`

### Mock 의존성 사용

실제 LLM이나 AWS 서비스 없이 테스트하려면 Mock을 사용합니다:

- 임베딩: Mock 임베딩 생성기 (기본값)
- 벡터 스토어: MockVectorStore (기본값)
- LLM: Mock LLM (기본값)

## 다음 단계

- [테스트 가이드](docs/TESTING.md): 상세한 테스트 실행 방법
- [로컬 테스트 가이드](docs/LOCAL_TESTING.md): Lambda 함수 로컬 테스트
- [AWS 배포 가이드](docs/DEPLOYMENT_AWS.md): AWS 환경 배포

