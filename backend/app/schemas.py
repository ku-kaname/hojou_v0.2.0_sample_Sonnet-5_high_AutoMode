"""
API入出力DTO

【概要】
エンドポイント層（main.py）のリクエスト・レスポンスで使用するPydanticスキーマを定義する。
本ファイルには認証・認可（auth）区分、通知区分、ユーザー管理区分、備品管理区分のスキーマを記載する。他機能群のスキーマは各機能群バックログで追加する。
"""

from datetime import date, datetime

from pydantic import BaseModel, Field

# ====================================================================================================
# 認証・認可スキーマ
# - LoginRequest : ログイン要求
# - TokenResponse : トークン応答
# - PasswordChangeRequest : パスワード変更要求
# - UserValidationResponse : 有効ユーザー検証応答
# - UserResponse : ユーザー情報応答

# 設計書：スキーマ（schemas）/認証・認可_v0.2.0.md
# ====================================================================================================


class LoginRequest(BaseModel):
    """
    ログイン要求

    設計書：スキーマ（schemas）/認証・認可_v0.2.0.md
    """

    user_id: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    """
    トークン応答

    設計書：スキーマ（schemas）/認証・認可_v0.2.0.md
    """

    access_token: str
    token_type: str


class PasswordChangeRequest(BaseModel):
    """
    パスワード変更要求

    設計書：スキーマ（schemas）/認証・認可_v0.2.0.md
    """

    current_password: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=8, max_length=255)


class UserValidationResponse(BaseModel):
    """
    有効ユーザー検証応答

    設計書：スキーマ（schemas）/認証・認可_v0.2.0.md
    """

    id: int
    user_id: str = Field(min_length=3, max_length=32)
    name: str = Field(min_length=1, max_length=50)
    department: str | None = Field(default=None, max_length=50)
    hashed_password: str = Field(min_length=1, max_length=255)
    role: str
    is_active: bool
    must_change_password: bool
    token_version: int = Field(ge=0)


class UserResponse(BaseModel):
    """
    ユーザー情報応答

    設計書：スキーマ（schemas）/認証・認可_v0.2.0.md
    """

    user_id: str = Field(min_length=3, max_length=32)
    name: str = Field(min_length=1, max_length=50)
    department: str | None = Field(default=None, max_length=50)
    role: str
    must_change_password: bool


# ====================================================================================================
# 通知スキーマ
# - NotificationResponse : 通知応答

# 設計書：スキーマ（schemas）/通知_v0.1.0.md
# ====================================================================================================


class NotificationResponse(BaseModel):
    """
    通知応答

    設計書：スキーマ（schemas）/通知_v0.1.0.md
    """

    id: int
    notification_type: str
    loan_request_id: int
    is_read: bool
    created_at: datetime


# ====================================================================================================
# ユーザー管理スキーマ
# - UserCreateRequest : ユーザー作成リクエスト
# - UserUpdateRequest : ユーザー編集リクエスト
# - PasswordResetRequest : パスワード初期化リクエスト
# - UserManagementResponse : ユーザー応答

# 設計書：スキーマ（schemas）/ユーザー操作_v0.2.0.md
# ====================================================================================================


class UserCreateRequest(BaseModel):
    """
    ユーザー作成リクエスト

    設計書：スキーマ（schemas）/ユーザー操作_v0.2.0.md
    """

    user_id: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=50)
    department: str | None = Field(default=None, max_length=50)
    password: str = Field(min_length=8, max_length=255)
    role: str


class UserUpdateRequest(BaseModel):
    """
    ユーザー編集リクエスト

    設計書：スキーマ（schemas）/ユーザー操作_v0.2.0.md
    """

    name: str = Field(min_length=1, max_length=50)
    department: str | None = Field(default=None, max_length=50)
    role: str


class PasswordResetRequest(BaseModel):
    """
    パスワード初期化リクエスト

    設計書：スキーマ（schemas）/ユーザー操作_v0.2.0.md
    """

    password: str = Field(min_length=8, max_length=255)


class UserManagementResponse(BaseModel):
    """
    ユーザー応答

    設計書：スキーマ（schemas）/ユーザー操作_v0.2.0.md
    """

    user_id: str
    name: str
    department: str | None
    role: str
    is_active: bool
    must_change_password: bool
    created_at: datetime
    updated_at: datetime


# ====================================================================================================
# 備品管理スキーマ
# - EquipmentCreateRequest : 備品作成リクエスト
# - EquipmentUpdateRequest : 備品編集リクエスト
# - EquipmentResponse : 備品応答
# - EquipmentListItemResponse : 備品一覧項目応答
# - ReservationPeriodResponse : 予約期間応答
# - EquipmentBulkImportResponse : 備品CSV一括登録応答

# 設計書：スキーマ（schemas）/備品操作_v0.1.0.md
# ====================================================================================================


class EquipmentCreateRequest(BaseModel):
    """
    備品作成リクエスト

    設計書：スキーマ（schemas）/備品操作_v0.1.0.md
    """

    asset_number: str = Field(min_length=1, max_length=32, pattern=r"^[A-Za-z0-9-]+$")
    name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    location: str | None = Field(default=None, max_length=100)


class EquipmentUpdateRequest(BaseModel):
    """
    備品編集リクエスト

    設計書：スキーマ（schemas）/備品操作_v0.1.0.md
    """

    name: str = Field(min_length=1, max_length=100)
    category: str = Field(min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    location: str | None = Field(default=None, max_length=100)


class EquipmentResponse(BaseModel):
    """
    備品応答

    設計書：スキーマ（schemas）/備品操作_v0.1.0.md
    """

    asset_number: str
    name: str
    category: str
    description: str | None
    location: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class EquipmentListItemResponse(BaseModel):
    """
    備品一覧項目応答

    設計書：スキーマ（schemas）/備品操作_v0.1.0.md
    """

    asset_number: str
    name: str
    category: str
    description: str | None
    location: str | None
    is_active: bool
    lending_status: str
    due_date: date | None


class ReservationPeriodResponse(BaseModel):
    """
    予約期間応答

    設計書：スキーマ（schemas）/備品操作_v0.1.0.md
    """

    start_date: date
    due_date: date
    status: str
    borrower_name: str | None


class EquipmentBulkImportResponse(BaseModel):
    """
    備品CSV一括登録応答

    設計書：スキーマ（schemas）/備品操作_v0.1.0.md
    """

    registered_count: int


# ====================================================================================================
# 貸出申請・承認スキーマ
# - LoanRequestCreateRequest : 貸出申請リクエスト
# - LoanRequestRejectRequest : 申請却下リクエスト
# - LoanRequestAdminCancelRequest : 管理者申請取消リクエスト
# - LoanRequestResponse : 貸出申請応答
# - PendingLoanRequestListItemResponse : 承認待ち申請一覧要素応答

# 設計書：スキーマ（schemas）/貸出申請操作_v0.1.0.md
# ====================================================================================================


class LoanRequestCreateRequest(BaseModel):
    """
    貸出申請リクエスト

    設計書：スキーマ（schemas）/貸出申請操作_v0.1.0.md
    """

    asset_number: str = Field(min_length=1, max_length=32)
    start_date: date
    due_date: date
    purpose: str = Field(min_length=1, max_length=200)


class LoanRequestRejectRequest(BaseModel):
    """
    申請却下リクエスト

    設計書：スキーマ（schemas）/貸出申請操作_v0.1.0.md
    """

    rejection_reason: str = Field(min_length=1, max_length=200)


class LoanRequestAdminCancelRequest(BaseModel):
    """
    管理者申請取消リクエスト

    設計書：スキーマ（schemas）/貸出申請操作_v0.1.0.md
    """

    cancellation_reason: str = Field(min_length=1, max_length=200)


class LoanRequestResponse(BaseModel):
    """
    貸出申請応答

    設計書：スキーマ（schemas）/貸出申請操作_v0.1.0.md
    """

    id: int
    asset_number: str
    equipment_name: str
    applicant_name: str
    start_date: date
    due_date: date
    purpose: str
    status: str
    rejection_reason: str | None
    requested_at: datetime
    decided_at: datetime | None
    cancelled_at: datetime | None


class PendingLoanRequestListItemResponse(BaseModel):
    """
    承認待ち申請一覧要素応答

    設計書：スキーマ（schemas）/貸出申請操作_v0.1.0.md
    """

    id: int
    asset_number: str
    equipment_name: str
    applicant_name: str
    start_date: date
    due_date: date
    purpose: str
    requested_at: datetime
