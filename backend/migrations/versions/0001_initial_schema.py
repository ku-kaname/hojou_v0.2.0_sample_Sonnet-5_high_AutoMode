"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-10-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("department", sa.String(length=50), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=10), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("must_change_password", sa.Boolean(), nullable=False),
        sa.Column("token_version", sa.Integer(), nullable=False),
        sa.Column("failed_login_count", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("role IN ('general', 'admin')", name="ck_user_role"),
    )
    op.create_index("ix_user_user_id", "user", ["user_id"], unique=True)

    op.create_table(
        "equipment",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("asset_number", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("location", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_equipment_asset_number", "equipment", ["asset_number"], unique=True)

    op.create_table(
        "loan_request",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("equipment_id", sa.Integer(), nullable=False),
        sa.Column("applicant_user_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("purpose", sa.String(length=200), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("rejection_reason", sa.String(length=200), nullable=True),
        sa.Column("approved_by_user_id", sa.Integer(), nullable=True),
        sa.Column("lent_by_user_id", sa.Integer(), nullable=True),
        sa.Column("returned_by_user_id", sa.Integer(), nullable=True),
        sa.Column("cancelled_by_user_id", sa.Integer(), nullable=True),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("decided_at", sa.DateTime(), nullable=True),
        sa.Column("lent_at", sa.DateTime(), nullable=True),
        sa.Column("returned_at", sa.DateTime(), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(), nullable=True),
        sa.Column("return_note", sa.String(length=200), nullable=True),
        sa.ForeignKeyConstraint(
            ["equipment_id"], ["equipment.id"], name="fk_loan_request_equipment_id", onupdate="CASCADE", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["applicant_user_id"], ["user.id"], name="fk_loan_request_applicant_user_id", onupdate="CASCADE", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["approved_by_user_id"], ["user.id"], name="fk_loan_request_approved_by_user_id", onupdate="CASCADE", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["lent_by_user_id"], ["user.id"], name="fk_loan_request_lent_by_user_id", onupdate="CASCADE", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["returned_by_user_id"], ["user.id"], name="fk_loan_request_returned_by_user_id", onupdate="CASCADE", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["cancelled_by_user_id"], ["user.id"], name="fk_loan_request_cancelled_by_user_id", onupdate="CASCADE", ondelete="RESTRICT"
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'lending', 'returned', 'rejected', 'cancelled')",
            name="ck_loan_request_status",
        ),
    )

    op.create_table(
        "notification",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("recipient_user_id", sa.Integer(), nullable=False),
        sa.Column("notification_type", sa.String(length=20), nullable=False),
        sa.Column("loan_request_id", sa.Integer(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["recipient_user_id"], ["user.id"], name="fk_notification_recipient_user_id", onupdate="CASCADE", ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["loan_request_id"], ["loan_request.id"], name="fk_notification_loan_request_id", onupdate="CASCADE", ondelete="RESTRICT"
        ),
        sa.CheckConstraint(
            "notification_type IN ('approved', 'rejected', 'cancelled', 'new_request', 'due_reminder')",
            name="ck_notification_notification_type",
        ),
    )


def downgrade() -> None:
    op.drop_table("notification")
    op.drop_table("loan_request")
    op.drop_index("ix_equipment_asset_number", table_name="equipment")
    op.drop_table("equipment")
    op.drop_index("ix_user_user_id", table_name="user")
    op.drop_table("user")
