#!/usr/bin/env python3
"""
AWS CDK 앱 진입점
Serverless RAG 서비스 인프라 정의
"""

import aws_cdk as cdk
from rag_serverless_stack import RagServerlessStack

app = cdk.App()

# 환경 설정
env = cdk.Environment(
    account=app.node.try_get_context("account") or None,
    region=app.node.try_get_context("region") or "ap-northeast-2"
)

# RAG Serverless 스택 생성
RagServerlessStack(
    app,
    "RagServerlessStack",
    env=env,
    description="Serverless RAG Assistant - Lambda + API Gateway + S3 + DynamoDB"
)

app.synth()

