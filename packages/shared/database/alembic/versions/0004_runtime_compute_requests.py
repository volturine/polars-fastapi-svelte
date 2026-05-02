"""runtime tenant compute request queue.

Revision ID: 0004_runtime_compute_requests
Revises: 0003_runtime_tenant_initial
Create Date: 2026-05-02

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0004_runtime_compute_requests'
down_revision: str | Sequence[str] | None = '0003_runtime_tenant_initial'
branch_labels: str | Sequence[str] | None = ('tenant',)
depends_on: str | Sequence[str] | None = None

__all__ = ('revision', 'down_revision', 'branch_labels', 'depends_on', 'upgrade', 'downgrade')


COMPUTE_REQUEST_KIND = sa.Enum(
    'preview',
    'schema',
    'row_count',
    'download',
    'export',
    'create_file_datasource',
    'create_database_datasource',
    'create_iceberg_datasource',
    'refresh_datasource',
    'spawn_engine',
    'keepalive_engine',
    'configure_engine',
    'shutdown_engine',
    name='computerequestkind',
    native_enum=False,
)

COMPUTE_REQUEST_STATUS = sa.Enum(
    'queued',
    'running',
    'completed',
    'failed',
    name='computerequeststatus',
    native_enum=False,
)


def _scope() -> str:
    config = op.get_context().config
    if config is None:
        return 'public'
    return str(config.attributes.get('runtime_scope', 'public'))


def upgrade() -> None:
    if _scope() != 'tenant':
        return
    op.create_table(
        'compute_requests',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('namespace', sa.String(), nullable=False),
        sa.Column('kind', COMPUTE_REQUEST_KIND, nullable=False),
        sa.Column('status', COMPUTE_REQUEST_STATUS, nullable=False),
        sa.Column('request_json', sa.JSON(), nullable=False),
        sa.Column('response_json', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('artifact_path', sa.String(), nullable=True),
        sa.Column('artifact_name', sa.String(), nullable=True),
        sa.Column('artifact_content_type', sa.String(), nullable=True),
        sa.Column('lease_owner', sa.String(), nullable=True),
        sa.Column('lease_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_compute_requests_namespace', 'compute_requests', ['namespace'])
    op.create_index('ix_compute_requests_kind', 'compute_requests', ['kind'])
    op.create_index('ix_compute_requests_status', 'compute_requests', ['status'])
    op.create_index('ix_compute_requests_lease_owner', 'compute_requests', ['lease_owner'])


def downgrade() -> None:
    if _scope() != 'tenant':
        return
    op.drop_index('ix_compute_requests_lease_owner', table_name='compute_requests')
    op.drop_index('ix_compute_requests_status', table_name='compute_requests')
    op.drop_index('ix_compute_requests_kind', table_name='compute_requests')
    op.drop_index('ix_compute_requests_namespace', table_name='compute_requests')
    op.drop_table('compute_requests')
