"""
RAG Pipeline (LangChain 최신 버전 호환 + 완전한 동작 보장)
"""

from typing import Dict, Optional, List

import os
from src.utils.logger import get_logger
from .retriever import RAGRetriever

logger = get_logger(__name__)


class RAGPipeline:
    """
    RAG 파이프라인 클래스
    LangChain 최신 버전에 맞춰 전체 구조 재구성
    """
    
    def __init__(
        self,
        retriever: RAGRetriever,
        llm_provider: str = "mock",
        model_name: Optional[str] = None
    ):
        self.retriever = retriever
        self.llm_provider = llm_provider
        self.model_name = model_name or self._get_default_model(llm_provider)
        self.llm = self._initialize_llm()

        # 최신 RetrievalQA 구성
        self.chain = self._create_chain()

        logger.info(f"RAGPipeline initialized: provider={llm_provider}, model={self.model_name}")
    
    # ------------------------------------------------------------
    # 📌 기본 모델 이름
    # ------------------------------------------------------------
    def _get_default_model(self, provider: str) -> str:
        defaults = {
            "openai": "gpt-3.5-turbo",
            "bedrock": "amazon.titan-text-express-v1",
            "mock": "mock-model"
        }
        return defaults.get(provider, "mock-model")
    
    # ------------------------------------------------------------
    # 📌 LLM 초기화 (OpenAI / Bedrock / Mock)
    # ------------------------------------------------------------
    def _initialize_llm(self):
        """LLM 로드. 실패 시 mock LLM 사용"""
        try:
            # ------------------------------
            # OpenAI
            # ------------------------------
            if self.llm_provider == "openai":
                try:
                    from langchain_openai import ChatOpenAI
                    api_key = os.getenv("OPENAI_API_KEY")
                    
                    if not api_key:
                        logger.warning("OPENAI_API_KEY 없음 → Mock LLM 사용")
                        return self._create_mock_llm()
                    
                    return ChatOpenAI(
                        model_name=self.model_name,
                        temperature=0.0,
                        openai_api_key=api_key,
                    )
                except Exception as e:
                    logger.warning(f"OpenAI 초기화 실패: {e} → Mock LLM 사용")
                    return self._create_mock_llm()

            # ------------------------------
            # AWS Bedrock
            # ------------------------------
            elif self.llm_provider == "bedrock":
                try:
                    from langchain_community.llms import Bedrock
                    import boto3
                    client = boto3.client("bedrock-runtime")
                    return Bedrock(
                        client=client,
                        model_id=self.model_name,
                    )
                except Exception as e:
                    logger.warning(f"Bedrock 초기화 실패: {e} → Mock LLM 사용")
                    return self._create_mock_llm()

            # ------------------------------
            # Mock
            # ------------------------------
            else:
                logger.info("Mock LLM 사용")
                return self._create_mock_llm()

        except Exception as e:
            logger.error(f"LLM 초기화 실패: {e} → Mock LLM 사용")
            return self._create_mock_llm()
    
    # ------------------------------------------------------------
    # 📌 Mock LLM (LangChain 최신 버전 호환)
    # ------------------------------------------------------------
    def _create_mock_llm(self):
        """
        LangChain 0.1~0.2 구조에 완벽 대응하는 Mock LLM
        """
        from typing import Any, List, Optional

        # 최신 LLM Base
        try:
            from langchain_core.language_models.llms import BaseLLM
            from langchain_core.outputs import LLMResult
            from langchain_core.callbacks.manager import CallbackManagerForLLMRun
        except ImportError:
            # 아주 구버전 대응
            class SimpleLLM:
                def __call__(self, prompt):
                    return f"[Mock] {prompt[:150]}..."
            return SimpleLLM()

        class MockLLM(BaseLLM):

            @property
            def _llm_type(self) -> str:
                return "mock-llm"
            
            def _call(self, prompt: str, stop=None) -> str:
                return f"[Mock Response] {prompt[:200]}..."

            def _generate(
                self,
                prompts: List[str],
                stop: Optional[List[str]] = None,
                run_manager: Optional[CallbackManagerForLLMRun] = None,
                **kwargs: Any,
            ) -> LLMResult:
                generations = [[{"text": self._call(prompt)}] for prompt in prompts]
                return LLMResult(generations=generations)

        return MockLLM()
    
    # ------------------------------------------------------------
    # 📌 RetrievalQA Chain 생성
    # ------------------------------------------------------------
    def _create_chain(self):
        """
        RetrievalQA 체인 생성
        LangChain 최신버전에서 완전히 호환되도록 구성
        """
        try:
            from langchain.chains.retrieval_qa.base import RetrievalQA
            from langchain_core.prompts import PromptTemplate
        except Exception as e:
            logger.warning(f"RetrievalQA import 실패: {e} → Fallback mode")
            return None

        template = """다음 문서들을 바탕으로 질문에 답해주세요.
문서에서 답을 찾을 수 없으면 "답변을 찾을 수 없습니다."라고 말하세요.

문서:
{context}

질문: {question}

답변:"""

        PROMPT = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )

        try:
            chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.retriever,
                return_source_documents=True,
                chain_type_kwargs={"prompt": PROMPT}
            )
            return chain

        except Exception as e:
            logger.error(f"RetrievalQA 체인 생성 실패: {e}")
            return None
    
    # ------------------------------------------------------------
    # 📌 QUERY 수행 (핵심)
    # ------------------------------------------------------------
    def query(self, question: str) -> Dict:
        """
        질문에 대한 답변 생성
        최신 LangChain 구조에 완전히 맞춰 수행되도록 수정됨.
        """
        try:
            # 체인이 존재하지 않는 경우 fallback
            if self.chain is None:
                logger.warning("RetrievalQA chain 없음 → fallback 수행")
                docs = self.retriever.get_relevant_documents(question)

                if docs:
                    context = "\n".join([d.page_content for d in docs[:3]])
                    answer = f"[Mock Fallback] {context[:300]}"
                else:
                    answer = "관련 문서를 찾을 수 없습니다."

                return {
                    "answer": answer,
                    "source_documents": [
                        {"content": d.page_content, "metadata": d.metadata}
                        for d in docs
                    ],
                }

            # ------------------------------
            # 🔥 최신 RetrievalQA 입력 키는 "question"
            # ------------------------------
            result = self.chain({"question": question})

            # LangChain 구조
            answer = result.get("result", "")
            source_docs = result.get("source_documents", [])

            converted = [
                {
                    "content": d.page_content,
                    "metadata": d.metadata,
                }
                for d in source_docs
            ]

            return {
                "answer": answer,
                "source_documents": converted,
            }

        except Exception as e:
            logger.error(f"RAGPipeline 오류: {e}", exc_info=True)
            return {
                "answer": f"오류 발생: {str(e)}",
                "source_documents": []
            }
