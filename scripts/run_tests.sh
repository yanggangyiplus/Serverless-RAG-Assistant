#!/bin/bash
# 테스트 실행 스크립트

set -e

echo "🧪 Running Serverless RAG Assistant Tests"
echo "=========================================="

# 가상환경 확인 및 생성
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# 가상환경 활성화
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# 의존성 설치
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 테스트 실행
echo ""
echo "🚀 Running tests..."
pytest tests/ -v

echo ""
echo "✅ Tests completed!"

