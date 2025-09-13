"""init

Revision ID: 0001_init
Revises: 
Create Date: 2025-09-13

"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg
from app.models.user import Role
from app.models.note import NoteStatus

# revision identifiers, used by Alembic.
revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum(Role, name='role'), nullable=False, server_default=Role.AGENT.value),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        'notes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('raw_text', sa.Text(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum(NoteStatus, name='notestatus'), nullable=False, server_default=NoteStatus.queued.value),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('notes')
    op.drop_table('users')
    op.execute("DROP TYPE IF EXISTS role")
    op.execute("DROP TYPE IF EXISTS notestatus")
