"""
業務コンテンツモデル

【概要】
備品貸出管理システムが扱う4テーブル（ユーザー情報・備品情報・貸出申請情報・通知情報）のORMモデルを定義する。

設計書：テーブル定義（models）/テーブル定義（models）_v0.1.0.md
"""

from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

# ====================================================================================================
# テーブルモデル
# - User : ユーザー情報
# - Equipment : 備品情報
# - LoanRequest : 貸出申請情報
# - Notification : 通知情報

# 設計書：テーブル定義（models）/テーブル定義（models）_v0.1.0.md
# ====================================================================================================


class User(Base):
    """
    ユーザー情報

    【概要】
    社員アカウント情報（テーブル定義（models）_v0.1.0.md「USER」参照）

    【属性】
    - id (int): 内部ID
    - user_id (str): ユーザーID
    - name (str): 氏名
    - department (str | None): 所属
    - hashed_password (str): パスワードハッシュ
    - role (str): ロール（`general`／`admin`）
    - is_active (bool): 有効フラグ
    - must_change_password (bool): 初回パスワード変更要否フラグ
    - token_version (int): トークン世代
    - failed_login_count (int): 連続認証失敗回数
    - locked_until (datetime | None): ロック解除日時
    - created_at (datetime): 作成日時
    - updated_at (datetime): 更新日時
    """

    __tablename__ = "user"
    __table_args__ = (
        CheckConstraint("role IN ('general', 'admin')", name="ck_user_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    department: Mapped[str | None] = mapped_column(String(50), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(10), nullable=False, default="general")
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    must_change_password: Mapped[bool] = mapped_column(nullable=False, default=True)
    token_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_login_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class Equipment(Base):
    """
    備品情報

    【概要】
    貸出対象となる備品情報（テーブル定義（models）_v0.1.0.md「EQUIPMENT」参照）

    【属性】
    - id (int): 内部ID
    - asset_number (str): 資産番号
    - name (str): 備品名
    - category (str): 分類
    - description (str | None): 説明
    - location (str | None): 保管場所
    - is_active (bool): 有効フラグ
    - created_at (datetime): 作成日時
    - updated_at (datetime): 更新日時
    """

    __tablename__ = "equipment"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_number: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class LoanRequest(Base):
    """
    貸出申請情報

    【概要】
    備品の貸出申請・貸出履歴情報（テーブル定義（models）_v0.1.0.md「LOAN_REQUEST」参照）

    【属性】
    - id (int): 内部ID
    - equipment_id (int): 備品ID
    - applicant_user_id (int): 申請者ユーザーID
    - start_date (date): 開始日
    - due_date (date): 返却予定日
    - purpose (str): 用途
    - status (str): 状態（`pending`／`approved`／`lending`／`returned`／`rejected`／`cancelled`）
    - rejection_reason (str | None): 却下・取消理由
    - approved_by_user_id (int | None): 承認・却下した管理者ユーザーID
    - lent_by_user_id (int | None): 貸出処理した管理者ユーザーID
    - returned_by_user_id (int | None): 返却処理した管理者ユーザーID
    - cancelled_by_user_id (int | None): 取消した者ユーザーID
    - requested_at (datetime): 申請日時
    - decided_at (datetime | None): 承認・却下日時
    - lent_at (datetime | None): 貸出日時
    - returned_at (datetime | None): 返却日時
    - cancelled_at (datetime | None): 取消日時
    - return_note (str | None): 返却時状態メモ
    """

    __tablename__ = "loan_request"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'lending', 'returned', 'rejected', 'cancelled')",
            name="ck_loan_request_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    equipment_id: Mapped[int] = mapped_column(
        ForeignKey("equipment.id", name="fk_loan_request_equipment_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    applicant_user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", name="fk_loan_request_applicant_user_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    purpose: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="pending")
    rejection_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    approved_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", name="fk_loan_request_approved_by_user_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=True,
    )
    lent_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", name="fk_loan_request_lent_by_user_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=True,
    )
    returned_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", name="fk_loan_request_returned_by_user_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=True,
    )
    cancelled_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("user.id", name="fk_loan_request_cancelled_by_user_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=True,
    )
    requested_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    lent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    returned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    return_note: Mapped[str | None] = mapped_column(String(200), nullable=True)


class Notification(Base):
    """
    通知情報

    【概要】
    アプリ内通知情報（テーブル定義（models）_v0.1.0.md「NOTIFICATION」参照）

    【属性】
    - id (int): 内部ID
    - recipient_user_id (int): 宛先ユーザーID
    - notification_type (str): 種別（`approved`／`rejected`／`cancelled`／`new_request`／`due_reminder`）
    - loan_request_id (int): 関連申請ID
    - is_read (bool): 既読フラグ
    - created_at (datetime): 作成日時
    """

    __tablename__ = "notification"
    __table_args__ = (
        CheckConstraint(
            "notification_type IN ('approved', 'rejected', 'cancelled', 'new_request', 'due_reminder')",
            name="ck_notification_notification_type",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recipient_user_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", name="fk_notification_recipient_user_id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
    )
    notification_type: Mapped[str] = mapped_column(String(20), nullable=False)
    loan_request_id: Mapped[int] = mapped_column(
        ForeignKey(
            "loan_request.id", name="fk_notification_loan_request_id", onupdate="CASCADE", ondelete="RESTRICT"
        ),
        nullable=False,
    )
    is_read: Mapped[bool] = mapped_column(nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
