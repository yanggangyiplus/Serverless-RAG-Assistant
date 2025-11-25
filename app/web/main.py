"""
Streamlit 기반 RAG Assistant 웹 UI
문서 업로드 및 질의응답 인터페이스
(Serverless RAG Lambda API 연동 + Local 모드 병행 지원 — Streamlit에서는 LOCAL 모드 주석)
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any

import base64
import requests
import streamlit as st
import json

# =========================================================
# 🔧 프로젝트 루트 경로 등록
# =========================================================
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

# =========================================================
# 🔧 LOCAL 서비스 import (Streamlit에서는 사용하지 않음 → 주석 처리)
# =========================================================
# from src.vectorstore.mock_store import MockVectorStore
# from src.embeddings.embedder import EmbeddingGenerator
# from src.services.ingestion_service import process_document_ingestion
# from src.services.rag_service import process_rag_query

# =========================================================
# 🔧 페이지 설정
# =========================================================
st.set_page_config(
    page_title="Serverless RAG Assistant",
    page_icon="🤖",
    layout="wide",
)

# =========================================================
# 🔧 Lambda API URL
# =========================================================
API_BASE_URL = "https://pirm3fhtfe.execute-api.ap-southeast-2.amazonaws.com/prod"


# =========================================================
# 세션 초기화 (LOCAL 모드용 — Streamlit에서는 기능 비활성)
# =========================================================
def init_session():
    if "initialized" not in st.session_state:
        st.session_state["initialized"] = True
        # st.session_state["mock_store"] = MockVectorStore()
        # st.session_state["embedding_generator"] = EmbeddingGenerator()


init_session()


# =========================================================
# 🔧 사이드바 UI
# =========================================================
def render_sidebar() -> Dict[str, Any]:
    with st.sidebar:
        st.header("⚙️ 실행 설정")

        # 🔥 원본 코드 유지 (LOCAL, API 선택)
        # mode = st.radio("실행 모드", ["LOCAL", "API"], index=1)

        # 🔥 Streamlit Cloud에서는 LOCAL 모드를 강제로 막기 위해 아래 한 줄 추가
        mode = "API"

        st.markdown("**🔗 현재 API Gateway URL**")
        st.code(API_BASE_URL)

        top_k = st.slider("Top-K", 1, 20, 5)
        temperature = st.slider("Temperature", 0.0, 2.0, 0.0, step=0.1)
        max_tokens = st.number_input("Max Tokens", 100, 3000, 1000, step=100)

    return {
        "mode": mode,
        "top_k": top_k,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


# =========================================================
# 🔥 RAG 질의응답 탭
# =========================================================
def render_query_tab(settings: Dict[str, Any]):
    st.header("💬 RAG Chat")

    question = st.text_area("질문을 입력하세요", height=140)

    col_submit, col_clear = st.columns([1, 4])
    submit_button = col_submit.button("질문하기", type="primary")
    clear_button = col_clear.button("초기화")

    if clear_button:
        st.rerun()

    # -----------------------------------------------------
    # API 호출 함수를 원본 그대로 유지
    # -----------------------------------------------------
    def query_via_api(query: str) -> Dict[str, Any]:
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
                # ================================
                # 🔥 LOCAL 모드는 주석 처리 (삭제 X)
                # ================================
                # if settings["mode"] == "LOCAL":
                #     result = process_rag_query(
                #         query=question,
                #         vector_store=st.session_state["mock_store"],
                #         embedding_generator=st.session_state["embedding_generator"],
                #         top_k=settings["top_k"],
                #     )
                # else:

                # 🔥 Streamlit에서는 항상 API 모드 실행
                result = query_via_api(question)

            except Exception as e:
                st.error(f"🚨 API 호출 중 오류: {e}")
                return

        answer = result.get("answer", "")
        sources = result.get("source_documents", []) or []

        st.success(f"✔️ 답변 생성 완료 ({len(sources)}개 문서 사용)")

        st.markdown("### 📝 답변")
        st.write(answer)

        if sources:
            st.markdown("### 📚 참조 문서")
            for idx, doc in enumerate(sources, 1):
                with st.expander(f"📄 문서 {idx}"):
                    text = doc.get("text") or doc.get("content") or ""
                    st.write(text)
                    st.json(doc)


# =========================================================
# 📚 문서 업로드 탭
# =========================================================
def render_documents_tab(settings: Dict[str, Any]):
    st.header("📚 문서 업로드 / 관리")

    uploaded = st.file_uploader("문서 업로드", type=["pdf", "txt", "md"])

    # API 업로드
    def upload_via_api(uploaded_file):
        file_bytes = uploaded_file.read()
        file_b64 = base64.b64encode(file_bytes).decode()

        payload = {"filename": uploaded_file.name, "file_b64": file_b64}

        res = requests.post(f"{API_BASE_URL}/upload", json=payload, timeout=60)
        res.raise_for_status()
        return res.json()

    # API 문서 목록 조회
    def list_documents_via_api():
        try:
            res = requests.get(f"{API_BASE_URL}/documents", timeout=30)
            res.raise_for_status()

            data = res.json()
            if isinstance(data, dict) and isinstance(data.get("body"), str):
                return json.loads(data["body"])
            return data

        except Exception as e:
            st.error(f"문서 목록 조회 실패: {e}")
            return None

    # 문서 업로드 버튼
    if uploaded and st.button("📥 문서 처리 시작"):
        with st.spinner("문서 분석 중…"):
            try:
                # 🔥 LOCAL 모드 주석 (삭제 X)
                # if settings["mode"] == "LOCAL":
                #     info = process_document_ingestion(
                #         file_bytes=uploaded.read(),
                #         filename=uploaded.name,
                #         vector_store=st.session_state["mock_store"],
                #         embedding_generator=st.session_state["embedding_generator"],
                #     )
                # else:

                info = upload_via_api(uploaded)

            except Exception as e:
                st.error(f"오류 발생: {e}")
                return

        st.success(f"✔ 처리 완료: {info.get('num_chunks', 0)}개 청크 생성됨")
        st.rerun()

    st.markdown("---")

    # LOCAL 모드 리스트 주석 (삭제 X)
    # if settings["mode"] == "LOCAL":
    #     docs = st.session_state["mock_store"].get_all_documents()
    #     ...
    
    st.subheader("🌐 API 문서 목록 조회")
    docs = list_documents_via_api()

    if docs:
        st.write(f"총 문서 수: {docs.get('total_documents', 0)}")
        for d in docs.get("documents", []):
            st.write(f"📄 {d['document_id']} — {d['num_chunks']}개 청크")
    else:
        st.info("문서 목록을 가져올 수 없습니다.")


# =========================================================
# 메인 함수
# =========================================================
def main():
    st.title("🤖 Serverless RAG Assistant")
    st.caption("AWS Lambda + API Gateway + DynamoDB 기반 Serverless RAG 서비스")

    settings = render_sidebar()

    tab_chat, tab_docs = st.tabs(["💬 RAG Chat", "📚 문서 관리"])

    with tab_chat:
        render_query_tab(settings)

    with tab_docs:
        render_documents_tab(settings)


if __name__ == "__main__":
    main()
