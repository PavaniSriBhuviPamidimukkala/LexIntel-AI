"""Add document ownership and user-scoped chat history.

Revision ID: 20261013_01
Revises:
"""

from alembic import op
import sqlalchemy as sa


revision = "20261013_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "legal_documents",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_legal_documents_user_id_users",
        "legal_documents",
        "users",
        ["user_id"],
        ["id"],
    )
    op.create_index(
        "ix_legal_documents_user_id",
        "legal_documents",
        ["user_id"],
    )
    op.add_column(
        "document_chunks",
        sa.Column("user_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_document_chunks_user_id_users",
        "document_chunks",
        "users",
        ["user_id"],
        ["id"],
    )
    op.create_index(
        "ix_document_chunks_user_id",
        "document_chunks",
        ["user_id"],
    )
    op.execute(
        """
        UPDATE document_chunks
        SET user_id = legal_documents.user_id
        FROM legal_documents
        WHERE document_chunks.document_id = legal_documents.id
        """
    )
    op.create_table(
        "chat_history",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=False),
        sa.Column("retrieval_succeeded", sa.Boolean(), nullable=False),
        sa.Column("average_similarity_score", sa.Float(), nullable=True),
        sa.Column("response_time_seconds", sa.Float(), nullable=False),
        sa.Column("retrieval_time_seconds", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_chat_history_user_id_users",
        ),
    )
    op.create_index("ix_chat_history_id", "chat_history", ["id"])
    op.create_index("ix_chat_history_user_id", "chat_history", ["user_id"])


def downgrade():
    op.drop_index("ix_chat_history_user_id", table_name="chat_history")
    op.drop_index("ix_chat_history_id", table_name="chat_history")
    op.drop_table("chat_history")
    op.drop_index("ix_document_chunks_user_id", table_name="document_chunks")
    op.drop_constraint(
        "fk_document_chunks_user_id_users",
        "document_chunks",
        type_="foreignkey",
    )
    op.drop_column("document_chunks", "user_id")
    op.drop_index("ix_legal_documents_user_id", table_name="legal_documents")
    op.drop_constraint(
        "fk_legal_documents_user_id_users",
        "legal_documents",
        type_="foreignkey",
    )
    op.drop_column("legal_documents", "user_id")
