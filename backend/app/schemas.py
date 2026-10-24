"""
API入出力DTO

【概要】
エンドポイント層（main.py）のリクエスト・レスポンスで使用するPydanticスキーマを定義する。
本ファイルには認証・認可（auth）区分、通知区分のスキーマを記載する。他機能群のスキーマは各機能群バックログで追加する。
"""

from datetime import datetime

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
