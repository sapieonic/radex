"""add_sharepoint_provider_tables

Creates tables for Microsoft SharePoint/OneDrive integration:
- provider_configs: Non-secret provider configuration (OAuth URLs, scopes, etc.)
- provider_connections: User OAuth connections with encrypted tokens
- provider_item_refs: References to synced files for idempotency

Revision ID: a1b2c3d4e5f6
Revises: 2523fa8f0b7b
Create Date: 2025-10-26 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '2523fa8f0b7b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create provider tables and seed SharePoint configuration."""

    # Create enum type manually (will be used by multiple tables)
    op.execute("CREATE TYPE providertype AS ENUM ('sharepoint')")

    # Create provider_configs table
    op.create_table(
        'provider_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('auth_url', sa.String(length=500), nullable=False),
        sa.Column('token_url', sa.String(length=500), nullable=False),
        sa.Column('graph_base_url', sa.String(length=500), nullable=False),
        sa.Column('default_scopes', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_provider_configs_provider', 'provider_configs', ['provider'], unique=True)

    # Create provider_connections table
    op.create_table(
        'provider_connections',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', postgresql.ENUM('sharepoint', name='providertype', create_type=False), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=False),
        sa.Column('encrypted_tokens', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_provider_connections_user_id', 'provider_connections', ['user_id'])
    op.create_index('ix_provider_connections_provider_user', 'provider_connections', ['provider', 'user_id'])
    op.create_index('uix_provider_user_tenant', 'provider_connections', ['provider', 'user_id', 'tenant_id'], unique=True)

    # Create provider_item_refs table
    op.create_table(
        'provider_item_refs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('provider', postgresql.ENUM('sharepoint', name='providertype', create_type=False), nullable=False),
        sa.Column('connection_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('drive_id', sa.String(length=255), nullable=False),
        sa.Column('item_id', sa.String(length=255), nullable=False),
        sa.Column('etag', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=500), nullable=True),
        sa.Column('size', sa.BigInteger(), nullable=True),
        sa.Column('last_modified', sa.DateTime(timezone=True), nullable=True),
        sa.Column('content_hash', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['connection_id'], ['provider_connections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('uix_provider_drive_item', 'provider_item_refs', ['provider', 'drive_id', 'item_id'], unique=True)
    op.create_index('ix_provider_item_refs_connection_id', 'provider_item_refs', ['connection_id'])
    op.create_index('ix_provider_item_refs_document_id', 'provider_item_refs', ['document_id'])

    # Seed SharePoint provider configuration
    op.execute("""
        INSERT INTO provider_configs (
            id,
            provider,
            display_name,
            auth_url,
            token_url,
            graph_base_url,
            default_scopes,
            is_enabled
        ) VALUES (
            gen_random_uuid(),
            'sharepoint',
            'Microsoft 365 (OneDrive & SharePoint)',
            'https://login.microsoftonline.com/common/oauth2/v2.0/authorize',
            'https://login.microsoftonline.com/common/oauth2/v2.0/token',
            'https://graph.microsoft.com/v1.0',
            ARRAY['Files.Read', 'Files.Read.All', 'Sites.Read.All', 'offline_access'],
            false
        )
        ON CONFLICT (provider) DO NOTHING
    """)


def downgrade() -> None:
    """Drop provider tables and enum types."""
    # Drop tables in reverse order
    op.drop_index('ix_provider_item_refs_document_id', table_name='provider_item_refs')
    op.drop_index('ix_provider_item_refs_connection_id', table_name='provider_item_refs')
    op.drop_index('uix_provider_drive_item', table_name='provider_item_refs')
    op.drop_table('provider_item_refs')

    op.drop_index('uix_provider_user_tenant', table_name='provider_connections')
    op.drop_index('ix_provider_connections_provider_user', table_name='provider_connections')
    op.drop_index('ix_provider_connections_user_id', table_name='provider_connections')
    op.drop_table('provider_connections')

    # Drop enum type
    op.execute('DROP TYPE IF EXISTS providertype')

    op.drop_index('ix_provider_configs_provider', table_name='provider_configs')
    op.drop_table('provider_configs')
