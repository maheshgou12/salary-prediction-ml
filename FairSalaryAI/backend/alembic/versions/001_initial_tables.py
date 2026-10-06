"""Create initial tables

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, ENUM


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums
    user_role_enum = ENUM('user', 'admin', name='user_role_enum', create_type=True)
    user_role_enum.create(op.get_bind(), checkfirst=True)

    employment_type_enum = ENUM('Full-time', 'Part-time', 'Contract', 'Internship', 'Freelance', name='employment_type_enum', create_type=True)
    employment_type_enum.create(op.get_bind(), checkfirst=True)

    company_size_enum = ENUM('Startup (1-50)', 'Small (51-200)', 'Medium (201-1000)', 'Large (1000+)', name='company_size_enum', create_type=True)
    company_size_enum.create(op.get_bind(), checkfirst=True)

    education_level_enum = ENUM('High School', 'Associate Degree', "Bachelor's Degree", "Master's Degree", 'PhD', name='education_level_enum', create_type=True)
    education_level_enum.create(op.get_bind(), checkfirst=True)

    gender_enum = ENUM('Male', 'Female', 'Non-binary', 'Prefer not to say', name='gender_enum', create_type=True)
    gender_enum.create(op.get_bind(), checkfirst=True)

    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', user_role_enum, nullable=False, server_default='user'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_id', 'users', ['id'])

    # Predictions table
    op.create_table(
        'predictions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('input_data', JSONB, nullable=False),
        sa.Column('predicted_salary', sa.Integer(), nullable=False),
        sa.Column('min_salary', sa.Integer(), nullable=False),
        sa.Column('max_salary', sa.Integer(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('similar_profiles', JSONB, nullable=True),
        sa.Column('explanation', JSONB, nullable=True),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_predictions_id', 'predictions', ['id'])
    op.create_index('ix_predictions_user_created', 'predictions', ['user_id', 'created_at'])

    # Candidate profiles table
    op.create_table(
        'candidate_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('experience_years', sa.Float(), nullable=False),
        sa.Column('education', education_level_enum, nullable=False),
        sa.Column('job_role', sa.String(100), nullable=False),
        sa.Column('location', sa.String(100), nullable=False),
        sa.Column('skills', JSONB, nullable=False),
        sa.Column('industry', sa.String(100), nullable=False),
        sa.Column('company_size', company_size_enum, nullable=False),
        sa.Column('employment_type', employment_type_enum, nullable=False),
        sa.Column('salary', sa.Integer(), nullable=False),
        sa.Column('gender', gender_enum, nullable=True),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(50), nullable=False, server_default='synthetic'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_candidate_profiles_id', 'candidate_profiles', ['id'])
    op.create_index('ix_candidate_profiles_role_location', 'candidate_profiles', ['job_role', 'location'])
    op.create_index('ix_candidate_profiles_experience_education', 'candidate_profiles', ['experience_years', 'education'])
    op.create_index('ix_candidate_profiles_gender', 'candidate_profiles', ['gender'])
    op.create_index('ix_candidate_profiles_age', 'candidate_profiles', ['age'])

    # Model versions table
    op.create_table(
        'model_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('model_type', sa.String(100), nullable=False),
        sa.Column('metrics', JSONB, nullable=False),
        sa.Column('fairness_metrics', JSONB, nullable=True),
        sa.Column('model_path', sa.String(500), nullable=False),
        sa.Column('preprocessor_path', sa.String(500), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('version'),
    )
    op.create_index('ix_model_versions_version', 'model_versions', ['version'], unique=True)
    op.create_index('ix_model_versions_is_active', 'model_versions', ['is_active'])


def downgrade() -> None:
    op.drop_index('ix_model_versions_is_active', table_name='model_versions')
    op.drop_index('ix_model_versions_version', table_name='model_versions')
    op.drop_table('model_versions')

    op.drop_index('ix_candidate_profiles_age', table_name='candidate_profiles')
    op.drop_index('ix_candidate_profiles_gender', table_name='candidate_profiles')
    op.drop_index('ix_candidate_profiles_experience_education', table_name='candidate_profiles')
    op.drop_index('ix_candidate_profiles_role_location', table_name='candidate_profiles')
    op.drop_index('ix_candidate_profiles_id', table_name='candidate_profiles')
    op.drop_table('candidate_profiles')

    op.drop_index('ix_predictions_user_created', table_name='predictions')
    op.drop_index('ix_predictions_id', table_name='predictions')
    op.drop_table('predictions')

    op.drop_index('ix_users_id', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')

    # Drop enums
    gender_enum = ENUM('Male', 'Female', 'Non-binary', 'Prefer not to say', name='gender_enum')
    gender_enum.drop(op.get_bind(), checkfirst=True)

    education_level_enum = ENUM('High School', 'Associate Degree', "Bachelor's Degree", "Master's Degree", 'PhD', name='education_level_enum')
    education_level_enum.drop(op.get_bind(), checkfirst=True)

    company_size_enum = ENUM('Startup (1-50)', 'Small (51-200)', 'Medium (201-1000)', 'Large (1000+)', name='company_size_enum')
    company_size_enum.drop(op.get_bind(), checkfirst=True)

    employment_type_enum = ENUM('Full-time', 'Part-time', 'Contract', 'Internship', 'Freelance', name='employment_type_enum')
    employment_type_enum.drop(op.get_bind(), checkfirst=True)

    user_role_enum = ENUM('user', 'admin', name='user_role_enum')
    user_role_enum.drop(op.get_bind(), checkfirst=True)