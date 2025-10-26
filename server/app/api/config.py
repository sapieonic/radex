"""
Configuration API Endpoints

Exposes application configuration to the frontend, including feature flags
and provider availability. No secrets are exposed.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.models.provider_config import ProviderConfig
from app.schemas.sharepoint import ProvidersConfigResponse, ProviderInfo
from app.config import settings

router = APIRouter(
    prefix="/config",
    tags=["Configuration"],
)


@router.get("/providers", response_model=ProvidersConfigResponse)
async def get_providers_config(db: Session = Depends(get_db)):
    """
    Get available file providers configuration.

    Returns feature-gated provider information including:
    - Which providers are enabled (ENV + DB flags)
    - Which providers are properly configured (have required credentials)
    - Display names for UI rendering

    **No secrets are exposed** - only boolean flags and display names.

    **Feature Gating:**
    - ENV flag (ENABLE_SHAREPOINT_PROVIDER) must be true
    - DB flag (ProviderConfig.is_enabled) must be true
    - Required credentials must be configured

    Returns:
        List of available providers with their enabled/configured status
    """
    providers = []

    # SharePoint/OneDrive Provider
    # Check ENV flag
    env_enabled = settings.enable_sharepoint_provider

    # Check if credentials are configured
    credentials_configured = all([
        settings.sp_client_id,
        settings.sp_client_secret,
        settings.sp_redirect_uri,
        settings.encryption_key,
    ])

    # Check DB configuration
    db_config = (
        db.query(ProviderConfig)
        .filter(ProviderConfig.provider == "sharepoint")
        .first()
    )
    db_enabled = db_config.is_enabled if db_config else False

    # Provider is available if ENV enabled AND DB enabled AND credentials configured
    is_enabled = env_enabled and db_enabled and credentials_configured

    providers.append(
        ProviderInfo(
            provider="sharepoint",
            display_name="Microsoft 365 (OneDrive & SharePoint)",
            is_enabled=is_enabled,
            is_configured=credentials_configured,
        )
    )

    # Future providers can be added here
    # Example:
    # providers.append(ProviderInfo(
    #     provider="google_drive",
    #     display_name="Google Drive",
    #     is_enabled=settings.enable_google_drive_provider,
    #     is_configured=bool(settings.google_drive_credentials),
    # ))

    return ProvidersConfigResponse(providers=providers)
