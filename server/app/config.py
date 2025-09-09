from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    database_url: str
    
    # Redis
    redis_url: str
    
    # MinIO
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str = "documents"
    minio_secure: bool = False
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 30
    
    # OpenAI
    openai_api_key: str
    
    # Confluence Integration
    confluence_oauth_client_id: Optional[str] = None
    confluence_oauth_client_secret: Optional[str] = None
    confluence_oauth_redirect_uri: Optional[str] = None
    confluence_encryption_key: Optional[str] = None
    confluence_max_import_size: int = 100  # MB
    confluence_rate_limit: int = 10  # requests per second
    confluence_sync_interval: int = 3600  # seconds
    
    # Celery
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    
    # App
    app_name: str = "RAG RBAC System"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()