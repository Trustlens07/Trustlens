"""Add screening session and decision models

Revision ID: 05_screening_and_decisions
Revises: 04abb6e98158_initial_schema
Create Date: 2026-04-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '05_screening_and_decisions'
down_revision = '04abb6e98158_initial_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create screening sessions table
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
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_screening_sessions_id', 'screening_sessions', ['id'], unique=False)
    
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
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ),
        sa.ForeignKeyConstraint(['session_id'], ['screening_sessions.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('application_id', name='uq_application_id')
    )
    op.create_index('ix_decisions_id', 'decisions', ['id'], unique=False)
    op.create_index('ix_decisions_application_id', 'decisions', ['application_id'], unique=False)
    
    # Add screening_session_id to candidates table
    op.add_column('candidates', sa.Column('screening_session_id', sa.String(255), nullable=True))
    op.create_foreign_key('fk_candidates_screening_session', 'candidates', 'screening_sessions', ['screening_session_id'], ['id'])


def downgrade() -> None:
    # Remove foreign key and column from candidates
    op.drop_constraint('fk_candidates_screening_session', 'candidates', type_='foreignkey')
    op.drop_column('candidates', 'screening_session_id')
    
    # Drop decisions table
    op.drop_index('ix_decisions_application_id', 'decisions')
    op.drop_index('ix_decisions_id', 'decisions')
    op.drop_table('decisions')
    
    # Drop screening sessions table
    op.drop_index('ix_screening_sessions_id', 'screening_sessions')
    op.drop_table('screening_sessions')
