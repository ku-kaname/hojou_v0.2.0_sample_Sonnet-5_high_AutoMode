"""
エンドポイント（共通）

【概要】
ヘルスチェック・認証・認可（auth）・通知・ユーザー管理の各エンドポイント、およびアプリケーション起動時処理
（初期管理者アカウント自動作成・日次バッチ起動定義）を定義する。他機能群のエンドポイントは各機能群バックログで追加する。
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Path
from pwdlib import PasswordHash
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import auth, crud, scheduler, services
from app.database import SessionLocal, get_db
from app.schemas import (
    NotificationResponse,
    PasswordResetRequest,
    UserCreateRequest,
    UserManagementResponse,
    UserUpdateRequest,
    UserValidationResponse,
)

_password_hash = PasswordHash.recommended()


def create_initial_admin_on_startup(db: Session) -> None:
    """
    初期管理者アカウント自動作成

    設計書：起動時処理（startup）/初期管理者アカウント自動作成_v0.2.0.md

    【処理概要】
    - 環境変数で指定されたユーザーIDが未登録の場合のみ、管理者ロールのユーザーを新規作成する。
    - 既に同一ユーザーIDが登録済みの場合は何も行わない（再起動時の冪等性を保つ）。

    【パラメータ】
    - db (Session) : データベース (必須)

    【戻り値】
    - なし

    【例外処理】
    - RuntimeError : 環境変数（ADMIN_USER_ID／ADMIN_NAME／ADMIN_PASSWORD）のいずれかが未設定の場合

    【処理フロー】
    1. 環境変数読み込み
    2. 既存ユーザー確認
    3. パスワードハッシュ化
    4. 管理者ユーザーレコード新規作成
    5. 戻り値を返却
    """

    # 1. 環境変数読み込み
    admin_user_id = os.environ.get("ADMIN_USER_ID")
    admin_name = os.environ.get("ADMIN_NAME")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    if not admin_user_id or not admin_name or not admin_password:
        raise RuntimeError("ADMIN_USER_ID・ADMIN_NAME・ADMIN_PASSWORDを環境変数に設定してください")

    # 2. 既存ユーザー確認
    existing_user = crud.get_user_by_user_id(db, admin_user_id)
    if existing_user is not None:
        return

    # 3. パスワードハッシュ化
    hashed_password = _password_hash.hash(admin_password)

    # 4. 管理者ユーザーレコード新規作成
    crud.create_user(db, admin_user_id, admin_name, None, hashed_password, "admin")

    # 5. 戻り値を返却
    return None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    db = SessionLocal()
    try:
        create_initial_admin_on_startup(db)
    finally:
        db.close()

    scheduler.start_daily_batch_scheduler()

    yield


app = FastAPI(lifespan=lifespan)


# ====================================================================================================
# ヘルスチェック
# - health_check : ヘルスチェック

# アーキテクチャ方針で定める例外（DB等への疎通確認のみを行う処理）に基づき、オーケストレーション層を経由しない。
# ====================================================================================================


@app.get("/health-check")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    """
    ヘルスチェック

    【処理概要】
    - データベースへの疎通確認を行う。

    【パラメータ】
    - db (Session) : データベース (必須)

    【戻り値】
    - status (dict[str, str]) : 疎通結果

    【例外処理】
    - なし

    【処理フロー】
    1. データベースへの疎通確認
    2. 戻り値を返却
    """

    # 1. データベースへの疎通確認
    db.execute(text("SELECT 1"))

    # 2. 戻り値を返却
    return {"status": "ok"}


# ====================================================================================================
# 認証・認可エンドポイント
# - issue_token : ログイン（トークン発行）
# - logout : ログアウト
# - get_my_info : 自分情報取得
# - change_password : パスワード変更

# 設計書：認証・認可（auth）/
# アーキテクチャ方針で定める例外（認証・認可処理）に基づき、オーケストレーション層を経由せず、
# auth.pyの各関数自体をルートハンドラとして直接登録する（main.py側に別名の中継関数を設けない）。
# docコメント・処理フロー等はauth.py側の各関数に記載済み。
# ====================================================================================================

app.post("/token")(auth.issue_token)
app.post("/logout", status_code=204)(auth.logout)
app.get("/me")(auth.get_my_info)
app.put("/me/password")(auth.change_password)


# ====================================================================================================
# 通知エンドポイント
# - get_notifications_endpoint : 通知一覧取得
# - mark_notification_read_endpoint : 通知既読化

# 設計書：サーバー処理（main）/共通/
# オーケストレーション層（services.py）を経由し、データアクセス層（crud.py）を直接呼び出さない。
# ====================================================================================================


@app.get("/notifications")
def get_notifications_endpoint(
    current_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> list[NotificationResponse]:
    """
    通知一覧取得

    設計書：サーバー処理（main）/共通/通知一覧取得_v0.1.0.md

    【処理概要】
    - ログインユーザーの内部IDに一致する通知情報を、作成日時の降順（新しい順）で取得する。
    - 取得した通知情報をレスポンスとして返却する。

    【パラメータ】
    - current_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - notification_response_list (list[NotificationResponse]) : 通知応答リスト。該当がない場合は空リスト

    【例外処理】
    - なし

    【処理フロー】
    1. 通知一覧取得
    2. 戻り値を返却
    """

    # 1. 通知一覧取得
    notifications = services.get_notifications(db, current_user.id)

    # 2. 戻り値を返却
    return [NotificationResponse.model_validate(notification, from_attributes=True) for notification in notifications]


@app.put("/notifications/{notification_id}/read")
def mark_notification_read_endpoint(
    notification_id: int,
    current_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> NotificationResponse:
    """
    通知既読化

    設計書：サーバー処理（main）/共通/通知既読化_v0.1.0.md

    【処理概要】
    - 対象の通知情報を取得し、ログインユーザー自身の宛先であることを確認する。
    - 既読フラグを更新し、更新後の通知情報をレスポンスとして返却する。

    【パラメータ】
    - notification_id (int) : 通知ID (必須)
    - current_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - notification_response (NotificationResponse) : 通知応答

    【例外処理】
    - HTTPException(404) : 通知情報が取得できない場合
    - HTTPException(404) : 宛先ユーザーIDがログインユーザーの内部IDと一致しない場合

    【処理フロー】
    1. 通知取得
    2. 宛先検証
    3. 通知既読化
    4. 戻り値を返却
    """

    # 1〜4. 通知取得・宛先検証・通知既読化・戻り値を返却
    updated_notification = services.mark_notification_read(db, notification_id, current_user.id)
    return NotificationResponse.model_validate(updated_notification, from_attributes=True)


# ====================================================================================================
# ユーザー管理エンドポイント
# - create_user_endpoint : ユーザー登録
# - get_users_endpoint : ユーザー一覧取得
# - get_user_endpoint : ユーザー詳細取得
# - update_user_endpoint : ユーザー編集
# - disable_user_endpoint : ユーザー無効化
# - enable_user_endpoint : ユーザー再有効化
# - reset_user_password_endpoint : パスワード初期化

# 設計書：サーバー処理（main）/ユーザー管理/
# オーケストレーション層（services.py）を経由し、データアクセス層（crud.py）を直接呼び出さない。
# ====================================================================================================


@app.post("/users")
def create_user_endpoint(
    user_create_request: UserCreateRequest,
    admin_user: UserValidationResponse = Depends(auth.require_admin),
    password_changed_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> UserManagementResponse:
    """
    ユーザー登録

    設計書：サーバー処理（main）/ユーザー管理/ユーザー登録_v0.2.0.md

    【処理概要】
    - ユーザーIDの重複を確認したうえで、初期パスワードをハッシュ化してユーザーを新規登録する。

    【パラメータ】
    - user_create_request (UserCreateRequest) : ユーザー作成リクエスト (必須)
    - admin_user (UserValidationResponse) : ロール検証結果 (必須)
    - password_changed_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - user_response (UserManagementResponse) : ユーザー応答

    【例外処理】
    - HTTPException(400) : ユーザーIDが既に使用されている場合

    【処理フロー】
    1. ユーザーID重複を確認する
    2. 初期パスワードをハッシュ化する
    3. ユーザーを登録する
    4. 戻り値を返却
    """

    # 1〜4. ユーザーID重複確認・初期パスワードハッシュ化・ユーザー登録・戻り値を返却
    user = services.create_user(db, user_create_request)
    return UserManagementResponse.model_validate(user, from_attributes=True)


@app.get("/users")
def get_users_endpoint(
    admin_user: UserValidationResponse = Depends(auth.require_admin),
    password_changed_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> list[UserManagementResponse]:
    """
    ユーザー一覧取得

    設計書：サーバー処理（main）/ユーザー管理/ユーザー一覧取得_v0.2.0.md

    【処理概要】
    - 全ユーザー情報をユーザーID昇順で取得する。

    【パラメータ】
    - admin_user (UserValidationResponse) : ロール検証結果 (必須)
    - password_changed_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - user_response_list (list[UserManagementResponse]) : ユーザー応答リスト。該当がない場合は空リスト

    【例外処理】
    - なし

    【処理フロー】
    1. ユーザー一覧を取得する
    2. 戻り値を返却
    """

    # 1. ユーザー一覧を取得する
    users = services.get_users(db)

    # 2. 戻り値を返却
    return [UserManagementResponse.model_validate(user, from_attributes=True) for user in users]


@app.get("/users/{user_id}")
def get_user_endpoint(
    user_id: str = Path(min_length=3, max_length=32),
    admin_user: UserValidationResponse = Depends(auth.require_admin),
    password_changed_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> UserManagementResponse:
    """
    ユーザー詳細取得

    設計書：サーバー処理（main）/ユーザー管理/ユーザー詳細取得_v0.2.0.md

    【処理概要】
    - パスパラメータのユーザーIDに一致するユーザー情報を取得し、レスポンスとして返却する。

    【パラメータ】
    - user_id (str) : ユーザーID (必須)
    - admin_user (UserValidationResponse) : ロール検証結果 (必須)
    - password_changed_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - user_response (UserManagementResponse) : ユーザー応答

    【例外処理】
    - HTTPException(404) : ユーザーが取得できない場合

    【処理フロー】
    1. ユーザーを取得する
    2. 戻り値を返却
    """

    # 1〜2. ユーザー取得・戻り値を返却
    user = services.get_user(db, user_id)
    return UserManagementResponse.model_validate(user, from_attributes=True)


@app.put("/users/{user_id}")
def update_user_endpoint(
    user_update_request: UserUpdateRequest,
    user_id: str = Path(min_length=3, max_length=32),
    admin_user: UserValidationResponse = Depends(auth.require_admin),
    password_changed_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> UserManagementResponse:
    """
    ユーザー編集

    設計書：サーバー処理（main）/ユーザー管理/ユーザー編集_v0.2.0.md

    【処理概要】
    - 最後の有効な管理者を一般ユーザーに変更しようとしていないかを確認したうえで、ユーザー情報を更新する。
    - ロールを変更した場合、既発行のトークンを失効させる。

    【パラメータ】
    - user_update_request (UserUpdateRequest) : ユーザー編集リクエスト (必須)
    - user_id (str) : ユーザーID (必須)
    - admin_user (UserValidationResponse) : ロール検証結果 (必須)
    - password_changed_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - user_response (UserManagementResponse) : ユーザー応答

    【例外処理】
    - HTTPException(404) : ユーザーが取得できない場合
    - HTTPException(400) : 最後の有効な管理者を一般ユーザーに変更しようとしている場合

    【処理フロー】
    1. 対象ユーザーを取得する
    2. 最後の管理者の変更でないことを確認する
    3. トークン世代を算定する
    4. ユーザーを更新する
    5. 戻り値を返却
    """

    # 1〜5. 対象ユーザー取得・最後の管理者チェック・トークン世代算定・ユーザー更新・戻り値を返却
    updated_user = services.update_user(db, user_id, user_update_request)
    return UserManagementResponse.model_validate(updated_user, from_attributes=True)


@app.put("/users/{user_id}/disable")
def disable_user_endpoint(
    user_id: str = Path(min_length=3, max_length=32),
    admin_user: UserValidationResponse = Depends(auth.require_admin),
    password_changed_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> UserManagementResponse:
    """
    ユーザー無効化

    設計書：サーバー処理（main）/ユーザー管理/ユーザー無効化_v0.2.0.md

    【処理概要】
    - 最後の有効な管理者でないこと、貸出中の申請がないことを確認したうえで無効化する。
    - 無効化に伴い、申請中・承認済みの申請を自動的に取消する。

    【パラメータ】
    - user_id (str) : ユーザーID (必須)
    - admin_user (UserValidationResponse) : ロール検証結果 (必須)
    - password_changed_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - user_response (UserManagementResponse) : ユーザー応答

    【例外処理】
    - HTTPException(404) : ユーザーが取得できない場合
    - HTTPException(400) : 既に無効化済みの場合
    - HTTPException(400) : 最後の有効な管理者を無効化しようとしている場合
    - HTTPException(400) : 貸出中の申請が存在する場合

    【処理フロー】
    1. 対象ユーザーを取得する
    2. 最後の管理者の無効化でないことを確認する
    3. 貸出中の申請がないことを確認する
    4. 申請中・承認済みの申請を自動取消する
    5. ユーザーを無効化する
    6. 戻り値を返却
    """

    # 1〜6. 対象ユーザー取得・最後の管理者チェック・貸出中申請確認・申請自動取消・ユーザー無効化・戻り値を返却
    disabled_user = services.disable_user(db, user_id)
    return UserManagementResponse.model_validate(disabled_user, from_attributes=True)


@app.put("/users/{user_id}/enable")
def enable_user_endpoint(
    user_id: str = Path(min_length=3, max_length=32),
    admin_user: UserValidationResponse = Depends(auth.require_admin),
    password_changed_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> UserManagementResponse:
    """
    ユーザー再有効化

    設計書：サーバー処理（main）/ユーザー管理/ユーザー再有効化_v0.2.0.md

    【処理概要】
    - 対象ユーザーが無効化済みであることを確認したうえで再有効化する。

    【パラメータ】
    - user_id (str) : ユーザーID (必須)
    - admin_user (UserValidationResponse) : ロール検証結果 (必須)
    - password_changed_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - user_response (UserManagementResponse) : ユーザー応答

    【例外処理】
    - HTTPException(404) : ユーザーが取得できない場合
    - HTTPException(400) : 既に有効化済みの場合

    【処理フロー】
    1. 対象ユーザーを取得する
    2. ユーザーを再有効化する
    3. 戻り値を返却
    """

    # 1〜3. 対象ユーザー取得・ユーザー再有効化・戻り値を返却
    enabled_user = services.enable_user(db, user_id)
    return UserManagementResponse.model_validate(enabled_user, from_attributes=True)


@app.put("/users/{user_id}/reset-password")
def reset_user_password_endpoint(
    password_reset_request: PasswordResetRequest,
    user_id: str = Path(min_length=3, max_length=32),
    admin_user: UserValidationResponse = Depends(auth.require_admin),
    password_changed_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> UserManagementResponse:
    """
    パスワード初期化

    設計書：サーバー処理（main）/ユーザー管理/パスワード初期化_v0.2.0.md

    【処理概要】
    - 初期パスワードをハッシュ化し、次回ログイン時の変更を必須としたうえで更新する。
    - 既発行のトークンを失効させる。

    【パラメータ】
    - password_reset_request (PasswordResetRequest) : パスワード初期化リクエスト (必須)
    - user_id (str) : ユーザーID (必須)
    - admin_user (UserValidationResponse) : ロール検証結果 (必須)
    - password_changed_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - user_response (UserManagementResponse) : ユーザー応答

    【例外処理】
    - HTTPException(404) : ユーザーが取得できない場合

    【処理フロー】
    1. 対象ユーザーを取得する
    2. 初期パスワードをハッシュ化する
    3. パスワードを初期化する
    4. 戻り値を返却
    """

    # 1〜4. 対象ユーザー取得・初期パスワードハッシュ化・パスワード初期化・戻り値を返却
    updated_user = services.reset_user_password(db, user_id, password_reset_request)
    return UserManagementResponse.model_validate(updated_user, from_attributes=True)
