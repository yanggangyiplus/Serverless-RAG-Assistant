"""
Streamlit 기반 RAG Assistant 웹 UI
문서 업로드 및 질의응답 인터페이스
(Serverless RAG Lambda API 연동 + Local 모드 병행 지원)
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any

import base64
import requests
import streamlit as st
import json

# 프로젝트 루트를 경로에 추가
# app/web/main.py -> app/web -> app -> 프로젝트 루트
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# LOCAL 모드 서비스 레이어 import
from src.vectorstore.mock_store import MockVectorStore
from src.embeddings.embedder import EmbeddingGenerator
from src.services.ingestion_service import process_document_ingestion
from src.services.rag_service import process_rag_query

# 페이지 설정
st.set_page_config(
    page_title="Serverless RAG Assistant",
    page_icon="🤖",
    layout="wide",
)

# Lambda API Base URL (배포된 API Gateway URL)
API_BASE_URL = "https://pirm3fhtfe.execute-api.ap-southeast-2.amazonaws.com/prod"


def init_session():
    """세션 상태 초기화"""
    if "initialized" not in st.session_state:
        st.session_state["initialized"] = True
        st.session_state["mock_store"] = MockVectorStore()
        st.session_state["embedding_generator"] = EmbeddingGenerator()


init_session()


def render_sidebar() -> Dict[str, Any]:
    """
    사이드바 렌더링
    
    Returns:
        설정 딕셔너리 (mode, top_k, temperature, max_tokens)
    """
    with st.sidebar:
        st.header("⚙️ 실행 설정")

        mode = st.radio("실행 모드", ["LOCAL", "API"], index=1)

        st.markdown("**🔗 현재 API Gateway**")
        st.code(API_BASE_URL, language="bash")

        top_k = st.slider("Top-K", 1, 20, 5)
        temperature = st.slider("Temperature", 0.0, 2.0, 0.0, step=0.1)
        max_tokens = st.number_input("Max Tokens", 100, 3000, 1000, step=100)

    return {
        "mode": mode,
        "top_k": top_k,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


def render_query_tab(settings: Dict[str, Any]):
    """
    RAG Chat 탭 렌더링
    
    Args:
        settings: 사이드바에서 설정한 파라미터 딕셔너리
    """
    st.header("💬 RAG Chat")

    question = st.text_area("질문을 입력하세요", height=140, placeholder="예: RAG가 뭐야? / 이 문서의 핵심만 요약해줘")

    col_submit, col_clear = st.columns([1, 4])
    submit_button = col_submit.button("질문하기", type="primary")
    clear_button = col_clear.button("초기화")

    if clear_button:
        st.rerun()

    def query_via_api(query: str) -> Dict[str, Any]:
        """API 모드에서 질의응답 요청"""
        payload = {
            "question": query,
            "top_k": settings["top_k"],
            "temperature": settings["temperature"],
            "max_tokens": settings["max_tokens"],
        }

        res = requests.post(f"{API_BASE_URL}/query", json=payload, timeout=60)
        res.raise_for_status()
        return res.json()

    if submit_button:
        if not question.strip():
            st.warning("질문을 입력해주세요.")
            return

        with st.spinner("RAG 실행 중…"):
            try:
                if settings["mode"] == "LOCAL":
                    result = process_rag_query(
                        query=question,
                        vector_store=st.session_state["mock_store"],
                        embedding_generator=st.session_state["embedding_generator"],
                        top_k=settings["top_k"],
                    )
                else:
                    result = query_via_api(question)

            except requests.exceptions.RequestException as e:
                st.error(
                    "🚨 API 호출 중 오류가 발생했습니다.\n\n"
                    f"- URL: `{API_BASE_URL}/query`\n"
                    f"- 오류: `{e}`\n\n"
                    "API Gateway / Lambda 상태를 확인해주세요."
                )
                return
            except Exception as e:
                st.error(f"🚨 RAG 처리 중 오류가 발생했습니다: {e}")
                return

        answer = result.get("answer", "")
        sources = result.get("source_documents", []) or []

        st.success(f"✅ 답변 생성 완료 (참조 문서 {len(sources)}개 사용)")

        st.markdown("### 📝 답변")
        st.write(answer)

        if sources:
            st.markdown("### 📚 참조 문서")
            for idx, doc in enumerate(sources, 1):
                with st.expander(f"📄 문서 {idx}"):
                    text = doc.get("text") or doc.get("content") or ""
                    st.write(text)
                    st.json(doc)


def render_documents_tab(settings: Dict[str, Any]):
    """
    문서 업로드/관리 탭 렌더링
    
    Args:
        settings: 사이드바에서 설정한 파라미터 딕셔너리
    """
    st.header("📚 문서 업로드 / 관리")

    uploaded = st.file_uploader("문서 업로드", type=["pdf", "txt", "md"])

    def upload_via_api(uploaded_file):
        """API 모드에서 문서 업로드 요청"""
        file_bytes = uploaded_file.read()
        file_b64 = base64.b64encode(file_bytes).decode()

        payload = {
            "filename": uploaded_file.name,
            "file_b64": file_b64,
        }

        res = requests.post(f"{API_BASE_URL}/upload", json=payload, timeout=60)
        res.raise_for_status()
        return res.json()

    def list_documents_via_api():
        """API 모드에서 문서 목록 조회"""
        try:
            res = requests.get(f"{API_BASE_URL}/documents", timeout=30)
            res.raise_for_status()

            # Lambda Proxy 통합 시 body는 string으로 넘어옴 → 직접 파싱 필요
            data = res.json()

            # body가 dict가 아니라 string 형태라면 json.loads() 수행
            if isinstance(data, dict) and "body" in data and isinstance(data["body"], str):
                data = json.loads(data["body"])

            return data

        except Exception as e:
            st.error(f"문서 목록 조회 실패: {e}")
            return None

    if uploaded and st.button("📥 문서 처리 시작"):
        with st.spinner("문서 분석 중…"):
            try:
                if settings["mode"] == "LOCAL":
                    info = process_document_ingestion(
                        file_bytes=uploaded.read(),
                        filename=uploaded.name,
                        vector_store=st.session_state["mock_store"],
                        embedding_generator=st.session_state["embedding_generator"],
                    )
                else:
                    info = upload_via_api(uploaded)

            except Exception as e:
                st.error(f"오류 발생: {e}")
                return

        num_chunks = info.get("num_chunks", 0)
        st.success(f"✔ 처리 완료: {num_chunks}개 청크 생성됨")
        st.rerun()

    st.markdown("---")

    if settings["mode"] == "LOCAL":
        docs = st.session_state["mock_store"].get_all_documents()
        st.write(f"총 청크 수: {len(docs)}")

        grouped = {}
        for d in docs:
            grouped.setdefault(d.document_id, 0)
            grouped[d.document_id] += 1

        for doc_id, count in grouped.items():
            st.write(f"📄 {doc_id} — {count}개 청크")
    else:
        st.subheader("🌐 API 문서 목록 조회")

        docs = list_documents_via_api()

        if docs:
            st.write(f"총 문서 수: {docs.get('total_documents', 0)}")

            for d in docs.get("documents", []):
                st.write(f"📄 {d['document_id']} — {d['num_chunks']}개 청크")
        else:
            st.info("문서 목록을 가져올 수 없습니다.")


def main():
    """메인 대시보드 함수"""
    st.title("🤖 Serverless RAG Assistant")
    st.caption("AWS Lambda + API Gateway + DynamoDB 기반 Serverless RAG 서비스")
    st.markdown("---")

    settings = render_sidebar()

    tab_chat, tab_docs = st.tabs(["💬 RAG Chat", "📚 문서 관리"])

    with tab_chat:
        render_query_tab(settings)

    with tab_docs:
        render_documents_tab(settings)


if __name__ == "__main__":
    main()

