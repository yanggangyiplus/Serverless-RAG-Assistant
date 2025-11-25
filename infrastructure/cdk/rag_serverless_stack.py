"""
RAG Serverless 스택 정의
Lambda + API Gateway + S3 + DynamoDB 인프라 구성
"""

from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_dynamodb as dynamodb,
    aws_logs as logs,
    Duration,
    RemovalPolicy,
    CfnOutput,
)
from constructs import Construct
import os


class RagServerlessStack(Stack):
    """Serverless RAG 서비스 인프라 스택"""
    
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # ============================================
        # S3 버킷 (문서 업로드용)
        # ============================================
        documents_bucket = s3.Bucket(
            self,
            "RagDocumentsBucket",
            bucket_name=f"rag-documents-{self.account}-{self.region}",
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY,  # 개발 환경용
            auto_delete_objects=True,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
        )
        
        # ============================================
        # DynamoDB 테이블 (벡터 스토어 및 메타데이터)
        # ============================================
        vector_store_table = dynamodb.Table(
            self,
            "RagVectorStoreTable",
            table_name="rag-documents",
            partition_key=dynamodb.Attribute(
                name="document_id",
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="chunk_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,  # 개발 환경용
            point_in_time_recovery=True,
        )
        
        # GSI: 문서 ID 기반 조회 최적화
        vector_store_table.add_global_secondary_index(
            index_name="document-id-index",
            partition_key=dynamodb.Attribute(
                name="document_id",
                type=dynamodb.AttributeType.STRING
            ),
        )
        
        # ============================================
        # Lambda 함수 공통 설정
        # ============================================
        lambda_timeout = Duration.minutes(15)  # 문서 처리 시간 고려
        lambda_memory_size = 1024  # 임베딩 생성에 충분한 메모리
        
        # Lambda 레이어용 의존성 패키징 (선택사항)
        # 실제 배포 시에는 Lambda Layer 또는 Docker 이미지 사용 권장
        
        # 공통 환경 변수
        common_env = {
            "BUCKET_NAME": documents_bucket.bucket_name,
            "VECTORSTORE_TABLE_NAME": vector_store_table.table_name,
            "VECTORSTORE_BACKEND": "dynamodb",
            "LOG_LEVEL": "INFO",
            "EMBEDDING_MODEL_NAME": "sentence-transformers/all-MiniLM-L6-v2",
            "EMBEDDING_PROVIDER": "huggingface",
            "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "openai"),
            "AWS_REGION": self.region,
        }
        
        # ============================================
        # Lambda 함수 1: upload_handler (S3 이벤트 트리거)
        # ============================================
        upload_handler = _lambda.Function(
            self,
            "UploadHandler",
            function_name="rag-upload-handler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="app.api.upload_handler.lambda_handler",
            code=_lambda.Code.from_asset("../.."),  # 프로젝트 루트 기준
            timeout=lambda_timeout,
            memory_size=lambda_memory_size,
            environment={
                **common_env,
                "HANDLER_TYPE": "upload",
            },
            log_retention=logs.RetentionDays.TWO_WEEKS,
            description="S3 이벤트 기반 문서 업로드 처리 Lambda",
        )
        
        # S3 버킷 읽기 권한
        documents_bucket.grant_read(upload_handler)
        
        # DynamoDB 쓰기 권한
        vector_store_table.grant_write_data(upload_handler)
        
        # S3 이벤트 알림 설정 (PDF, TXT, MD 파일만)
        documents_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(upload_handler),
            s3.NotificationKeyFilter(
                suffix=".pdf"
            )
        )
        documents_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(upload_handler),
            s3.NotificationKeyFilter(
                suffix=".txt"
            )
        )
        documents_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(upload_handler),
            s3.NotificationKeyFilter(
                suffix=".md"
            )
        )
        
        # ============================================
        # Lambda 함수 2: query_handler (API Gateway)
        # ============================================
        query_handler = _lambda.Function(
            self,
            "QueryHandler",
            function_name="rag-query-handler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="app.api.query_handler.lambda_handler",
            code=_lambda.Code.from_asset("../.."),
            timeout=Duration.minutes(5),  # 질의응답은 더 짧은 타임아웃
            memory_size=512,
            environment={
                **common_env,
                "HANDLER_TYPE": "query",
            },
            log_retention=logs.RetentionDays.TWO_WEEKS,
            description="RAG 질의응답 Lambda",
        )
        
        # DynamoDB 읽기 권한
        vector_store_table.grant_read_data(query_handler)
        
        # ============================================
        # Lambda 함수 3: documents_handler (API Gateway)
        # ============================================
        documents_handler = _lambda.Function(
            self,
            "DocumentsHandler",
            function_name="rag-documents-handler",
            runtime=_lambda.Runtime.PYTHON_3_11,
            handler="app.api.documents_handler.lambda_handler",
            code=_lambda.Code.from_asset("../.."),
            timeout=Duration.seconds(30),
            memory_size=256,
            environment={
                **common_env,
                "HANDLER_TYPE": "documents",
            },
            log_retention=logs.RetentionDays.TWO_WEEKS,
            description="문서 목록 조회 Lambda",
        )
        
        # DynamoDB 읽기 권한
        vector_store_table.grant_read_data(documents_handler)
        
        # ============================================
        # API Gateway (REST API)
        # ============================================
        api = apigateway.RestApi(
            self,
            "RagApi",
            rest_api_name="RAG Assistant API",
            description="Serverless RAG Assistant REST API",
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "X-Amz-Date", "Authorization", "X-Api-Key"],
            ),
            deploy_options=apigateway.StageOptions(
                stage_name="prod",
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
            ),
        )
        
        # /rag/query 엔드포인트
        query_resource = api.root.add_resource("rag").add_resource("query")
        query_resource.add_method(
            "POST",
            apigateway.LambdaIntegration(
                query_handler,
                proxy=True,
            )
        )
        
        # /rag/documents 엔드포인트
        documents_resource = api.root.add_resource("rag").add_resource("documents")
        documents_resource.add_method(
            "GET",
            apigateway.LambdaIntegration(
                documents_handler,
                proxy=True,
            )
        )
        
        # ============================================
        # CloudWatch Logs 그룹
        # ============================================
        # Lambda 함수의 로그 그룹은 자동 생성되지만,
        # 추가 설정이 필요한 경우 여기에 정의
        
        # ============================================
        # 출력값 (Outputs)
        # ============================================
        CfnOutput(
            self,
            "ApiEndpoint",
            value=api.url,
            description="API Gateway 엔드포인트 URL",
        )
        
        CfnOutput(
            self,
            "DocumentsBucketName",
            value=documents_bucket.bucket_name,
            description="문서 업로드용 S3 버킷 이름",
        )
        
        CfnOutput(
            self,
            "VectorStoreTableName",
            value=vector_store_table.table_name,
            description="벡터 스토어 DynamoDB 테이블 이름",
        )
        
        CfnOutput(
            self,
            "UploadHandlerFunctionName",
            value=upload_handler.function_name,
            description="문서 업로드 Lambda 함수 이름",
        )
        
        CfnOutput(
            self,
            "QueryHandlerFunctionName",
            value=query_handler.function_name,
            description="질의응답 Lambda 함수 이름",
        )

