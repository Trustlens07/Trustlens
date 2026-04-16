"""Initial schema merged from all migrations (idempotent raw SQL)

Revision ID: initial_schema_merged
Revises: 
Create Date: 2026-04-16 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'initial_schema_merged'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Create ENUM type if it doesn't exist using raw SQL
    op.execute("""
        DO $$ 
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'candidatestatus') THEN
                CREATE TYPE candidatestatus AS ENUM ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED');
            END IF;
        END $$;
    """)

    # Create tables using raw SQL to avoid SQLAlchemy's automatic ENUM creation
    op.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            name VARCHAR(255),
            email VARCHAR(255),
            phone VARCHAR(50),
            file_name VARCHAR(255) NOT NULL,
            file_url VARCHAR(500) NOT NULL,
            file_size INTEGER NOT NULL,
            file_type VARCHAR(50) NOT NULL,
            status candidatestatus NOT NULL,
            parsed_data JSON,
            error_message VARCHAR(500),
            id VARCHAR(36) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE,
            required_skills JSON,
            screening_session_id VARCHAR(255),
            application_id VARCHAR(50),
            job_role VARCHAR(255),
            PRIMARY KEY (id)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS bias_metrics (
            metric_name VARCHAR(100) NOT NULL,
            group_type VARCHAR(50) NOT NULL,
            group_name VARCHAR(100) NOT NULL,
            metric_value DOUBLE PRECISION NOT NULL,
            threshold DOUBLE PRECISION,
            is_biased VARCHAR(10) NOT NULL,
            details JSON,
            calculated_at TIMESTAMP WITH TIME ZONE NOT NULL,
            candidate_id VARCHAR(36),
            is_enhanced VARCHAR(10) NOT NULL,
            enhanced_bias_metrics JSONB,
            bias_enhanced_at TIMESTAMP WITH TIME ZONE,
            original_metric_id VARCHAR(36),
            id VARCHAR(36) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE,
            PRIMARY KEY (id),
            FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            candidate_id VARCHAR(36) NOT NULL,
            feedback_text TEXT NOT NULL,
            strengths TEXT,
            improvements TEXT,
            is_regenerated BOOLEAN,
            id VARCHAR(36) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE,
            PRIMARY KEY (id),
            FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            candidate_id VARCHAR(36) NOT NULL,
            overall_score DOUBLE PRECISION NOT NULL,
            skill_score DOUBLE PRECISION NOT NULL,
            experience_score DOUBLE PRECISION NOT NULL,
            education_score DOUBLE PRECISION NOT NULL,
            breakdown JSON NOT NULL,
            ranking_percentile DOUBLE PRECISION,
            version INTEGER NOT NULL,
            enhanced_score DOUBLE PRECISION,
            enhanced_breakdown JSONB,
            enhanced_at TIMESTAMP WITH TIME ZONE,
            enhanced_by_model VARCHAR(100),
            enhancement_explanation TEXT,
            bias_correction_applied TEXT,
            id VARCHAR(36) NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE,
            PRIMARY KEY (id),
            FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS screening_sessions (
            id VARCHAR(255) NOT NULL,
            job_role VARCHAR(255) NOT NULL,
            job_description VARCHAR(5000),
            fairness_mode VARCHAR(50) DEFAULT 'balanced' NOT NULL,
            total_candidates INTEGER DEFAULT 0 NOT NULL,
            shortlisted_count INTEGER DEFAULT 0 NOT NULL,
            rejected_count INTEGER DEFAULT 0 NOT NULL,
            status VARCHAR(50) DEFAULT 'pending' NOT NULL,
            error_message VARCHAR(500),
            fairness_score DOUBLE PRECISION,
            bias_metrics JSON,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE,
            PRIMARY KEY (id)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id VARCHAR(255) NOT NULL,
            application_id VARCHAR(255) NOT NULL,
            candidate_id VARCHAR(255) NOT NULL,
            session_id VARCHAR(255) NOT NULL,
            decision VARCHAR(50) DEFAULT 'pending' NOT NULL,
            notes VARCHAR(500),
            decided_by VARCHAR(255),
            created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE,
            PRIMARY KEY (id),
            FOREIGN KEY (candidate_id) REFERENCES candidates(id),
            FOREIGN KEY (session_id) REFERENCES screening_sessions(id),
            UNIQUE (application_id)
        )
    """)

    # Add foreign key from candidates to screening_sessions
    op.execute("""
        ALTER TABLE candidates 
        ADD CONSTRAINT fk_candidates_screening_session 
        FOREIGN KEY (screening_session_id) 
        REFERENCES screening_sessions(id)
    """)

    # Add unique constraint on candidates.application_id
    op.execute("""
        ALTER TABLE candidates 
        ADD CONSTRAINT uq_candidates_application_id 
        UNIQUE (application_id)
    """)

def downgrade() -> None:
    # Drop constraints
    op.execute("ALTER TABLE candidates DROP CONSTRAINT IF EXISTS uq_candidates_application_id")
    op.execute("ALTER TABLE candidates DROP CONSTRAINT IF EXISTS fk_candidates_screening_session")
    
    # Drop tables in reverse order
    op.execute("DROP TABLE IF EXISTS decisions")
    op.execute("DROP TABLE IF EXISTS screening_sessions")
    op.execute("DROP TABLE IF EXISTS scores")
    op.execute("DROP TABLE IF EXISTS feedback")
    op.execute("DROP TABLE IF EXISTS bias_metrics")
    op.execute("DROP TABLE IF EXISTS candidates")
    
    # Drop ENUM type
    op.execute("DROP TYPE IF EXISTS candidatestatus")