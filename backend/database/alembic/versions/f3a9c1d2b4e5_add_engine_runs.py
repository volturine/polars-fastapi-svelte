"""add engine runs.

Revision ID: f3a9c1d2b4e5
Revises: cd818acda9c7
Create Date: 2026-02-09 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f3a9c1d2b4e5'
down_revision: str | Sequence[str] | None = 'cd818acda9c7'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'engine_runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('analysis_id', sa.String(), nullable=True),
        sa.Column('datasource_id', sa.String(), nullable=False),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('request_json', sa.JSON(), nullable=False),
        sa.Column('result_json', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('engine_runs')
