from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import Field, computed_field

class Settings(BaseSettings):
    # Database - can be provided as URL or individual components
    database_url: Optional[str] = None
    db_host: Optional[str] = "localhost"
    db_port: Optional[int] = 5432
    db_name: Optional[str] = "ragdb"
    db_user: Optional[str] = "raguser"
    db_password: Optional[str] = "changeme"
    
    # Redis - can be provided as URL or individual components
    redis_url: Optional[str] = None
    redis_host: Optional[str] = "localhost"
    redis_port: Optional[int] = 6379
    redis_password: Optional[str] = ""
    
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
    openai_chat_model: str = "gpt-3.5-turbo"  # Model for answer generation
    openai_reformulation_model: str = "gpt-3.5-turbo"  # Model for query reformulation

    # Firebase (optional - for Firebase authentication)
    firebase_admin_sdk_json: Optional[str] = None  # JSON string of Firebase service account credentials

    # Okta (for SAML integration via Firebase)
    okta_client_id: Optional[str] = None
    okta_client_secret: Optional[str] = None
    okta_domain: Optional[str] = None
    okta_redirect_uri: Optional[str] = None
    okta_api_token: Optional[str] = None
    okta_api_audience: Optional[str] = None

    # SharePoint/OneDrive Provider
    enable_sharepoint_provider: bool = False  # ENV-based feature flag
    sp_client_id: Optional[str] = None  # Microsoft App Registration Client ID
    sp_client_secret: Optional[str] = None  # Microsoft App Registration Client Secret
    sp_redirect_uri: Optional[str] = None  # OAuth callback URL

    # Token Encryption (for provider OAuth tokens)
    encryption_key: Optional[str] = None  # Fernet encryption key (base64)

    # App
    app_name: str = "RAG RBAC System"
    debug: bool = True
    
    @computed_field
    @property
    def effective_database_url(self) -> str:
        """Get the database URL, constructing it from components if not provided directly."""
        if self.database_url:
            return self.database_url
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @computed_field
    @property
    def effective_redis_url(self) -> str:
        """Get the Redis URL, constructing it from components if not provided directly."""
        if self.redis_url:
            return self.redis_url
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields to prevent validation errors

settings = Settings()