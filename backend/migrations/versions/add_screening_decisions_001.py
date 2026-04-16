"""Add screening sessions and decisions tables

Revision ID: add_screening_decisions_001
Revises: add_required_skills_001
Create Date: 2026-04-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_screening_decisions_001"
down_revision: Union[str, None] = "add_required_skills_001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create screening_sessions table
    op.create_table(
        'screening_sessions',
        sa.Column('id', sa.String(255), nullable=False),
        sa.Column('job_role', sa.String(255), nullable=False),
        sa.Column('job_description', sa.String(5000), nullable=True),
        sa.Column('fairness_mode', sa.String(50), nullable=False, server_default='balanced'),
        sa.Column('total_candidates', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('shortlisted_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rejected_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.Column('fairness_score', sa.Float(), nullable=True),
        sa.Column('bias_metrics', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create decisions table
    op.create_table(
        'decisions',
        sa.Column('id', sa.String(255), nullable=False),
        sa.Column('application_id', sa.String(255), nullable=False),
        sa.Column('candidate_id', sa.String(255), nullable=False),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('decision', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('decided_by', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['screening_sessions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('application_id', name='uq_application_id')
    )
    
    # Add screening_session_id to candidates table
    op.add_column('candidates', sa.Column('screening_session_id', sa.String(255), nullable=True))
    op.create_foreign_key('fk_candidates_screening_session', 'candidates', 'screening_sessions', ['screening_session_id'], ['id'])


def downgrade() -> None:
    # Remove foreign key and column from candidates
    op.drop_constraint('fk_candidates_screening_session', 'candidates', type_='foreignkey')
    op.drop_column('candidates', 'screening_session_id')
    
    # Drop decisions table
    op.drop_table('decisions')
    
    # Drop screening sessions table
    op.drop_table('screening_sessions')
