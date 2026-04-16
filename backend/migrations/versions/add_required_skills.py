"""Add required_skills column to candidates

Revision ID: add_required_skills_001
Revises: 090a8a57f7ca
Create Date: 2026-04-15 11:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_required_skills_001"
down_revision: Union[str, None] = "090a8a57f7ca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add required_skills column to candidates table
    op.add_column('candidates', sa.Column('required_skills', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove required_skills column from candidates table
    op.drop_column('candidates', 'required_skills')
