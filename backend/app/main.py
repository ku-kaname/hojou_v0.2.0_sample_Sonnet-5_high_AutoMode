"""
エンドポイント（共通）

【概要】
ヘルスチェック・認証・認可（auth）・通知・ユーザー管理・備品管理（参照系・登録管理系）・貸出申請・承認・貸出・返却の各エンドポイント、
およびアプリケーション起動時処理（初期管理者アカウント自動作成・日次バッチ起動定義）を定義する。他機能群のエンドポイントは各機能群バックログで追加する。
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, Path, Query, UploadFile
from pwdlib import PasswordHash
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import auth, crud, scheduler, services
from app.database import SessionLocal, get_db
from app.schemas import (
    EquipmentBulkImportResponse,
    EquipmentCreateRequest,
    EquipmentListItemResponse,
    EquipmentResponse,
    EquipmentUpdateRequest,
    LoanLendReturnResponse,
    LoanRequestAdminCancelRequest,
    LoanRequestCreateRequest,
    LoanRequestRejectRequest,
    LoanRequestResponse,
    LoanRequestReturnRequest,
    NotificationResponse,
    PasswordResetRequest,
    PendingLoanRequestListItemResponse,
    ReservationPeriodResponse,
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


# ====================================================================================================
# 備品管理エンドポイント
# - search_equipment_endpoint : 備品検索・一覧取得
# - get_equipment_endpoint : 備品詳細取得
# - get_equipment_reservations_endpoint : 備品予約状況取得
# - create_equipment_endpoint : 備品登録
# - update_equipment_endpoint : 備品編集
# - disable_equipment_endpoint : 備品無効化
# - enable_equipment_endpoint : 備品再有効化
# - bulk_import_equipment_endpoint : 備品CSV一括登録

# 設計書：サーバー処理（main）/備品管理/
# オーケストレーション層（services.py）を経由し、データアクセス層（crud.py）を直接呼び出さない。
# ====================================================================================================


@app.get("/equipment")
def search_equipment_endpoint(
    category: str | None = Query(default=None, min_length=0, max_length=50),
    keyword: str | None = Query(default=None, min_length=0, max_length=100),
    is_active: bool | None = Query(default=None),
    current_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> list[EquipmentListItemResponse]:
    """
    備品検索・一覧取得

    設計書：サーバー処理（main）/備品管理/備品検索・一覧取得_v0.1.0.md

    【処理概要】
    - 要求元が一般ユーザーの場合は有効な備品のみに絞り込み、管理者の場合は有効フラグの指定に応じて絞り込みを行い、一覧取得する。

    【パラメータ】
    - category (str | None) : 分類
    - keyword (str | None) : キーワード
    - is_active (bool | None) : 有効フラグ（管理者のみ有効。一般ユーザーが指定した場合は無視する）
    - current_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - equipment_list_response (list[EquipmentListItemResponse]) : 備品一覧要素応答リスト。該当がない場合は空リスト

    【例外処理】
    - なし

    【処理フロー】
    1. 有効フラグ検索条件を算定する
    2. 備品一覧を取得する
    3. 戻り値を返却
    """

    # 1〜2. 有効フラグ検索条件算定・備品一覧取得
    equipment_list = services.search_equipment(db, current_user.role, category, keyword, is_active)

    # 3. 戻り値を返却
    return [EquipmentListItemResponse.model_validate(equipment, from_attributes=True) for equipment in equipment_list]


@app.get("/equipment/{equipment_id}")
def get_equipment_endpoint(
    equipment_id: str = Path(min_length=1, max_length=32),
    current_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> EquipmentListItemResponse:
    """
    備品詳細取得

    設計書：サーバー処理（main）/備品管理/備品詳細取得_v0.1.0.md

    【処理概要】
    - 指定した資産番号の備品情報と現在の貸出状況を取得し、レスポンスとして返却する。
    - 要求元が一般ユーザーの場合、無効化済みの備品は取得できない。

    【パラメータ】
    - equipment_id (str) : 資産番号 (必須。URLパスの変数名は`equipment_id`とするが、値は資産番号を指定する)
    - current_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - equipment_response (EquipmentListItemResponse) : 備品一覧要素応答

    【例外処理】
    - HTTPException(404) : 備品が取得できない場合
    - HTTPException(404) : 一般ユーザーが無効化済み備品を取得しようとしている場合

    【処理フロー】
    1. 対象備品を取得する
    2. 現在の貸出状況を取得する
    3. 戻り値を返却
    """

    # 1〜3. 対象備品取得・貸出状況取得・戻り値を返却
    equipment = services.get_equipment(db, current_user.role, equipment_id)
    return EquipmentListItemResponse.model_validate(equipment, from_attributes=True)


@app.get("/equipment/{equipment_id}/reservations")
def get_equipment_reservations_endpoint(
    equipment_id: str = Path(min_length=1, max_length=32),
    current_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> list[ReservationPeriodResponse]:
    """
    備品予約状況取得

    設計書：サーバー処理（main）/備品管理/備品予約状況取得_v0.1.0.md

    【処理概要】
    - 対象備品の、状態が「承認済み」「貸出中」の申請を開始日昇順で取得し、レスポンスとして返却する。
    - 借用者氏名は、要求元が管理者の場合のみ設定する。

    【パラメータ】
    - equipment_id (str) : 資産番号 (必須。URLパスの変数名は`equipment_id`とするが、値は資産番号を指定する)
    - current_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - reservation_response_list (list[ReservationPeriodResponse]) : 予約期間応答リスト。該当がない場合は空リスト

    【例外処理】
    - HTTPException(404) : 備品が取得できない場合
    - HTTPException(404) : 一般ユーザーが無効化済み備品の予約状況を取得しようとしている場合

    【処理フロー】
    1. 対象備品を取得する
    2. 予約期間一覧を取得する
    3. 借用者氏名を設定する
    4. 戻り値を返却
    """

    # 1〜4. 対象備品取得・予約期間一覧取得・借用者氏名設定・戻り値を返却
    reservation_list = services.get_equipment_reservations(db, current_user.role, equipment_id)
    return [
        ReservationPeriodResponse.model_validate(reservation, from_attributes=True) for reservation in reservation_list
    ]


@app.post("/equipment")
def create_equipment_endpoint(
    equipment_create_request: EquipmentCreateRequest,
    admin_user: UserValidationResponse = Depends(auth.require_admin),
    password_changed_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> EquipmentResponse:
    """
    備品登録

    設計書：サーバー処理（main）/備品管理/備品登録_v0.1.0.md

    【処理概要】
    - 管理者が新規備品を登録する。
    - 資産番号の重複を確認したうえで、備品を新規登録する。

    【パラメータ】
    - equipment_create_request (EquipmentCreateRequest) : 備品作成リクエスト (必須)
    - admin_user (UserValidationResponse) : ロール検証結果 (必須)
    - password_changed_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - equipment_response (EquipmentResponse) : 備品応答

    【例外処理】
    - HTTPException(400) : 資産番号が既に使用されている場合

    【処理フロー】
    1. 資産番号重複を確認する
    2. 備品を登録する
    3. 戻り値を返却
    """

    # 1〜2. 資産番号重複確認・備品登録
    equipment = services.create_equipment(db, equipment_create_request)

    # 3. 戻り値を返却
    return EquipmentResponse.model_validate(equipment, from_attributes=True)


@app.put("/equipment/{equipment_id}")
def update_equipment_endpoint(
    equipment_update_request: EquipmentUpdateRequest,
    equipment_id: str = Path(min_length=1, max_length=32),
    admin_user: UserValidationResponse = Depends(auth.require_admin),
    password_changed_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> EquipmentResponse:
    """
    備品編集

    設計書：サーバー処理（main）/備品管理/備品編集_v0.1.0.md

    【処理概要】
    - 管理者が対象備品の備品名・分類・説明・保管場所を編集する。

    【パラメータ】
    - equipment_update_request (EquipmentUpdateRequest) : 備品編集リクエスト (必須)
    - equipment_id (str) : 資産番号 (必須。URLパスの変数名は`equipment_id`とするが、値は資産番号を指定する)
    - admin_user (UserValidationResponse) : ロール検証結果 (必須)
    - password_changed_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - equipment_response (EquipmentResponse) : 備品応答

    【例外処理】
    - HTTPException(404) : 備品が取得できない場合

    【処理フロー】
    1. 対象備品を取得する
    2. 備品を更新する
    3. 戻り値を返却
    """

    # 1〜2. 対象備品取得・備品更新
    equipment = services.update_equipment(db, equipment_id, equipment_update_request)

    # 3. 戻り値を返却
    return EquipmentResponse.model_validate(equipment, from_attributes=True)


@app.put("/equipment/{equipment_id}/disable")
def disable_equipment_endpoint(
    equipment_id: str = Path(min_length=1, max_length=32),
    admin_user: UserValidationResponse = Depends(auth.require_admin),
    password_changed_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> EquipmentResponse:
    """
    備品無効化

    設計書：サーバー処理（main）/備品管理/備品無効化_v0.1.0.md

    【処理概要】
    - 指定した備品を無効化する。
    - その備品に「申請中」「承認済み」「貸出中」の申請がないことを確認したうえで無効化する。該当する申請がある場合は無効化できない（ユーザー無効化と異なり、自動取消は行わない）。

    【パラメータ】
    - equipment_id (str) : 資産番号 (必須。URLパスの変数名は`equipment_id`とするが、値は資産番号を指定する)
    - admin_user (UserValidationResponse) : ロール検証結果 (必須)
    - password_changed_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - equipment_response (EquipmentResponse) : 備品応答

    【例外処理】
    - HTTPException(404) : 備品が取得できない場合
    - HTTPException(400) : 備品が既に無効化されている場合
    - HTTPException(400) : 申請中・承認済み・貸出中の申請が存在する場合

    【処理フロー】
    1. 対象備品を取得する
    2. 無効化可能なことを確認する
    3. 備品を無効化する
    4. 戻り値を返却
    """

    # 1〜3. 対象備品取得・無効化可否確認・備品無効化
    equipment = services.disable_equipment(db, equipment_id)

    # 4. 戻り値を返却
    return EquipmentResponse.model_validate(equipment, from_attributes=True)


@app.put("/equipment/{equipment_id}/enable")
def enable_equipment_endpoint(
    equipment_id: str = Path(min_length=1, max_length=32),
    admin_user: UserValidationResponse = Depends(auth.require_admin),
    password_changed_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> EquipmentResponse:
    """
    備品再有効化

    設計書：サーバー処理（main）/備品管理/備品再有効化_v0.1.0.md

    【処理概要】
    - 指定した備品を再有効化する。

    【パラメータ】
    - equipment_id (str) : 資産番号 (必須。URLパスの変数名は`equipment_id`とするが、値は資産番号を指定する)
    - admin_user (UserValidationResponse) : ロール検証結果 (必須)
    - password_changed_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - equipment_response (EquipmentResponse) : 備品応答

    【例外処理】
    - HTTPException(404) : 備品が取得できない場合
    - HTTPException(400) : 備品が既に有効化されている場合

    【処理フロー】
    1. 対象備品を取得する
    2. 備品を再有効化する
    3. 戻り値を返却
    """

    # 1〜2. 対象備品取得・備品再有効化
    equipment = services.enable_equipment(db, equipment_id)

    # 3. 戻り値を返却
    return EquipmentResponse.model_validate(equipment, from_attributes=True)


@app.post("/equipment/bulk-import")
def bulk_import_equipment_endpoint(
    file: UploadFile = File(),
    admin_user: UserValidationResponse = Depends(auth.require_admin),
    password_changed_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> EquipmentBulkImportResponse:
    """
    備品CSV一括登録

    設計書：サーバー処理（main）/備品管理/備品CSV一括登録_v0.1.0.md

    【処理概要】
    - CSVファイルから備品を一括登録する。
    - CSVファイルのサイズ・ヘッダー列・データ行数を検証する。
    - 全データ行について、項目の形式と資産番号の重複（ファイル内・DB内の双方）を検証する。
    - 1行でもエラーがある場合は全件登録せず、行番号付きのエラー一覧を返す。
    - 全行が検証OKの場合のみ、一括登録する。

    【パラメータ】
    - file (UploadFile) : CSVファイル (必須。multipart/form-data。ヘッダー行あり、列は「資産番号・備品名・分類・説明・保管場所」の順)
    - admin_user (UserValidationResponse) : ロール検証結果 (必須)
    - password_changed_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - bulk_import_response (EquipmentBulkImportResponse) : 備品CSV一括登録応答

    【例外処理】
    - HTTPException(400) : ファイルサイズが5MBを超える場合
    - HTTPException(400) : CSVのヘッダー列が不正な場合
    - HTTPException(400) : データ行数が1,000行を超える場合
    - HTTPException(400) : 検証エラーが存在する場合（行番号・エラー内容のリストを返す）

    【処理フロー】
    1. ファイルサイズを検証する
    2. CSVファイルを解析する
    3. 各データ行を検証する
    4. エラーがある場合、登録を中止する
    5. 備品を一括登録する
    6. 戻り値を返却
    """

    # 1〜5. ファイルサイズ検証・CSV解析・各データ行検証・登録中止判定・備品一括登録
    file_content = file.file.read()
    registered_count = services.bulk_import_equipment(db, file_content)

    # 6. 戻り値を返却
    return EquipmentBulkImportResponse(registered_count=registered_count)


@app.post("/loan-requests")
def create_loan_request_endpoint(
    loan_request_create_request: LoanRequestCreateRequest,
    current_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> LoanRequestResponse:
    """
    貸出申請

    設計書：サーバー処理（main）/貸出申請・承認/貸出申請_v0.1.0.md

    【処理概要】
    - 入力値の資産番号に一致する有効な備品を取得する。
    - 指定した期間について、同一備品の承認済み・貸出中の申請と重複がないことを確認する。
    - 貸出申請を新規登録し、有効な管理者全員に通知を送信する。

    【パラメータ】
    - loan_request_create_request (LoanRequestCreateRequest) : 貸出申請リクエスト (必須)
    - current_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - loan_request_response (LoanRequestResponse) : 貸出申請応答

    【例外処理】
    - HTTPException(400) : 返却予定日が開始日より前の場合
    - HTTPException(404) : 備品が取得できない、または無効化済みの場合
    - HTTPException(400) : 指定期間が既存の承認済み・貸出中の申請と重複する場合

    【処理フロー】
    1. リクエストの日付整合性を確認する
    2. 対象備品を取得する
    3. 期間の重複を確認する
    4. 貸出申請を登録する
    5. 有効な管理者全員に通知する
    6. 戻り値を返却
    """

    # 1〜5. 日付整合性確認・対象備品取得・期間重複確認・貸出申請登録・管理者通知
    loan_request_detail = services.create_loan_request(db, loan_request_create_request, current_user.id, current_user.name)

    # 6. 戻り値を返却
    return LoanRequestResponse.model_validate(loan_request_detail, from_attributes=True)


@app.put("/loan-requests/{loan_request_id}/cancel")
def cancel_loan_request_endpoint(
    loan_request_id: int,
    current_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> LoanRequestResponse:
    """
    申請取消

    設計書：サーバー処理（main）/貸出申請・承認/申請取消_v0.1.0.md

    【処理概要】
    - 申請者本人が、自身の貸出申請を取消する。
    - 対象の貸出申請を取得し、申請者が自分自身であること、状態が「申請中」または「承認済み」であることを確認する。
    - 申請を取消状態に更新する。

    【パラメータ】
    - loan_request_id (int) : 内部ID (必須)
    - current_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - loan_request_response (LoanRequestResponse) : 貸出申請応答

    【例外処理】
    - HTTPException(404) : 貸出申請が取得できない場合
    - HTTPException(404) : 自分以外の申請を取消しようとしている場合（存在有無を判別できないよう、取得できない場合と同様に扱う）
    - HTTPException(400) : 取消可能な状態ではない場合

    【処理フロー】
    1. 対象の貸出申請を取得する
    2. 貸出申請を取消する
    3. 貸出申請の詳細を取得する
    4. 戻り値を返却
    """

    # 1〜3. 対象の貸出申請取得・貸出申請取消・貸出申請詳細取得
    loan_request_detail = services.cancel_loan_request(db, loan_request_id, current_user.id)

    # 4. 戻り値を返却
    return LoanRequestResponse.model_validate(loan_request_detail, from_attributes=True)


@app.get("/loan-requests/pending")
def get_pending_loan_requests_endpoint(
    admin_user: UserValidationResponse = Depends(auth.require_admin),
    password_changed_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> list[PendingLoanRequestListItemResponse]:
    """
    承認待ち申請一覧取得

    設計書：サーバー処理（main）/貸出申請・承認/承認待ち申請一覧取得_v0.1.0.md

    【処理概要】
    - 状態が「申請中」の貸出申請を、申請日時の昇順で一覧取得する。

    【パラメータ】
    - admin_user (UserValidationResponse) : ロール検証結果 (必須)
    - password_changed_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - pending_loan_request_response_list (list[PendingLoanRequestListItemResponse]) : 承認待ち申請一覧要素応答リスト。該当がない場合は空リスト

    【例外処理】
    - なし

    【処理フロー】
    1. 承認待ち申請一覧を取得する
    2. 戻り値を返却
    """

    # 1. 承認待ち申請一覧を取得する
    pending_loan_request_list = services.get_pending_loan_requests(db)

    # 2. 戻り値を返却
    return [
        PendingLoanRequestListItemResponse.model_validate(pending_loan_request, from_attributes=True)
        for pending_loan_request in pending_loan_request_list
    ]


@app.put("/loan-requests/{loan_request_id}/approve")
def approve_loan_request_endpoint(
    loan_request_id: int,
    admin_user: UserValidationResponse = Depends(auth.require_admin),
    current_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> LoanRequestResponse:
    """
    申請承認

    設計書：サーバー処理（main）/貸出申請・承認/申請承認_v0.1.0.md

    【処理概要】
    - 管理者が、申請中の貸出申請を承認する。
    - 対象の貸出申請を取得し、状態が「申請中」であること、開始日が今日以降であることを確認する。
    - 指定期間について、同一備品の承認済み・貸出中の申請と重複がないことを確認する。
    - 申請を承認済み状態に更新し、申請者へ通知を送信する。

    【パラメータ】
    - loan_request_id (int) : 内部ID (必須)
    - admin_user (UserValidationResponse) : ロール検証結果 (必須)
    - current_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - loan_request_response (LoanRequestResponse) : 貸出申請応答

    【例外処理】
    - HTTPException(404) : 貸出申請が取得できない場合
    - HTTPException(400) : 承認可能な状態ではない場合
    - HTTPException(400) : 開始日を過ぎている場合
    - HTTPException(400) : 指定期間が既存の承認済み・貸出中の申請と重複する場合

    【処理フロー】
    1. 対象の貸出申請を取得する
    2. 期間の重複を確認する
    3. 貸出申請を承認する
    4. 貸出申請の詳細を取得する
    5. 申請者へ通知する
    6. 戻り値を返却
    """

    # 1〜5. 対象の貸出申請取得・期間重複確認・貸出申請承認・貸出申請詳細取得・申請者通知
    loan_request_detail = services.approve_loan_request(db, loan_request_id, current_user.id)

    # 6. 戻り値を返却
    return LoanRequestResponse.model_validate(loan_request_detail, from_attributes=True)


@app.put("/loan-requests/{loan_request_id}/reject")
def reject_loan_request_endpoint(
    loan_request_reject_request: LoanRequestRejectRequest,
    loan_request_id: int,
    admin_user: UserValidationResponse = Depends(auth.require_admin),
    current_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> LoanRequestResponse:
    """
    申請却下

    設計書：サーバー処理（main）/貸出申請・承認/申請却下_v0.1.0.md

    【処理概要】
    - 管理者が、申請中の貸出申請を却下する。
    - 対象の貸出申請を取得し、状態が「申請中」であることを確認する。
    - 申請を却下状態に更新し、申請者へ通知を送信する。

    【パラメータ】
    - loan_request_reject_request (LoanRequestRejectRequest) : 申請却下リクエスト (必須)
    - loan_request_id (int) : 内部ID (必須)
    - admin_user (UserValidationResponse) : ロール検証結果 (必須)
    - current_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - loan_request_response (LoanRequestResponse) : 貸出申請応答

    【例外処理】
    - HTTPException(404) : 貸出申請が取得できない場合
    - HTTPException(400) : 却下可能な状態ではない場合

    【処理フロー】
    1. 対象の貸出申請を取得する
    2. 貸出申請を却下する
    3. 貸出申請の詳細を取得する
    4. 申請者へ通知する
    5. 戻り値を返却
    """

    # 1〜4. 対象の貸出申請取得・貸出申請却下・貸出申請詳細取得・申請者通知
    loan_request_detail = services.reject_loan_request(db, loan_request_id, current_user.id, loan_request_reject_request)

    # 5. 戻り値を返却
    return LoanRequestResponse.model_validate(loan_request_detail, from_attributes=True)


@app.put("/loan-requests/{loan_request_id}/admin-cancel")
def admin_cancel_loan_request_endpoint(
    loan_request_admin_cancel_request: LoanRequestAdminCancelRequest,
    loan_request_id: int,
    admin_user: UserValidationResponse = Depends(auth.require_admin),
    current_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> LoanRequestResponse:
    """
    管理者申請取消

    設計書：サーバー処理（main）/貸出申請・承認/管理者申請取消_v0.1.0.md

    【処理概要】
    - 管理者が、承認済みの貸出申請を取消する。
    - 対象の貸出申請を取得し、状態が「承認済み」であることを確認する。
    - 申請を取消状態に更新し、申請者へ通知を送信する。

    【パラメータ】
    - loan_request_admin_cancel_request (LoanRequestAdminCancelRequest) : 管理者申請取消リクエスト (必須)
    - loan_request_id (int) : 内部ID (必須)
    - admin_user (UserValidationResponse) : ロール検証結果 (必須)
    - current_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - loan_request_response (LoanRequestResponse) : 貸出申請応答

    【例外処理】
    - HTTPException(404) : 貸出申請が取得できない場合
    - HTTPException(400) : 取消可能な状態ではない場合（「申請中」の申請は却下（F09）で取消する対象のため、本機能の対象は「承認済み」のみ）

    【処理フロー】
    1. 対象の貸出申請を取得する
    2. 貸出申請を取消する
    3. 貸出申請の詳細を取得する
    4. 申請者へ通知する
    5. 戻り値を返却
    """

    # 1〜4. 対象の貸出申請取得・貸出申請取消・貸出申請詳細取得・申請者通知
    loan_request_detail = services.admin_cancel_loan_request(
        db, loan_request_id, current_user.id, loan_request_admin_cancel_request
    )

    # 5. 戻り値を返却
    return LoanRequestResponse.model_validate(loan_request_detail, from_attributes=True)


# ====================================================================================================
# 貸出・返却エンドポイント
# - lend_loan_request_endpoint : 貸出処理
# - return_loan_request_endpoint : 返却処理

# 設計書：サーバー処理（main）/貸出・返却/
# オーケストレーション層（services.py）を経由し、データアクセス層（crud.py）を直接呼び出さない。
# ====================================================================================================


@app.put("/loan-requests/{loan_request_id}/lend")
def lend_loan_request_endpoint(
    loan_request_id: int,
    admin_user: UserValidationResponse = Depends(auth.require_admin),
    current_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> LoanLendReturnResponse:
    """
    貸出処理

    設計書：サーバー処理（main）/貸出・返却/貸出処理_v0.1.0.md

    【処理概要】
    - 管理者が、承認済みの貸出申請に対して備品を貸し出す。
    - 対象の貸出申請を取得し、状態が「承認済み」であること、開始日が今日以前であることを確認する。
    - 対象備品を取得し、無効化されていないこと、貸出中の別申請が存在しないことを確認する。
    - 申請を貸出中状態に更新する。

    【パラメータ】
    - loan_request_id (int) : 内部ID (必須)
    - admin_user (UserValidationResponse) : ロール検証結果 (必須)
    - current_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - loan_lend_return_response (LoanLendReturnResponse) : 貸出・返却応答

    【例外処理】
    - HTTPException(404) : 貸出申請が取得できない場合
    - HTTPException(400) : 貸出処理可能な状態ではない場合
    - HTTPException(400) : 開始日前のため貸出処理できない場合
    - HTTPException(400) : 対象備品が無効化されている場合
    - HTTPException(400) : 同一備品が既に貸出中の場合

    【処理フロー】
    1. 対象の貸出申請を取得する
    2. 対象備品を取得する
    3. 貸出中の別申請が存在しないことを確認する
    4. 貸出処理する
    5. 貸出申請の詳細を取得する
    6. 戻り値を返却
    """

    # 1〜5. 対象の貸出申請取得・対象備品取得・貸出中別申請確認・貸出処理・貸出申請詳細取得
    loan_request_detail = services.lend_loan_request(db, loan_request_id, current_user.id)

    # 6. 戻り値を返却
    return LoanLendReturnResponse.model_validate(loan_request_detail, from_attributes=True)


@app.put("/loan-requests/{loan_request_id}/return")
def return_loan_request_endpoint(
    loan_request_return_request: LoanRequestReturnRequest,
    loan_request_id: int,
    admin_user: UserValidationResponse = Depends(auth.require_admin),
    current_user: UserValidationResponse = Depends(auth.require_password_changed),
    db: Session = Depends(get_db),
) -> LoanLendReturnResponse:
    """
    返却処理

    設計書：サーバー処理（main）/貸出・返却/返却処理_v0.1.0.md

    【処理概要】
    - 管理者が、貸出中の貸出申請に対して備品の返却を記録する。
    - 対象の貸出申請を取得し、状態が「貸出中」であることを確認する。
    - 申請を返却済み状態に更新する。返却日時はサーバー時刻を自動記録し、状態メモを任意で残せる。

    【パラメータ】
    - loan_request_return_request (LoanRequestReturnRequest) : 返却処理リクエスト (必須)
    - loan_request_id (int) : 内部ID (必須)
    - admin_user (UserValidationResponse) : ロール検証結果 (必須)
    - current_user (UserValidationResponse) : 初回パスワード変更検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - loan_lend_return_response (LoanLendReturnResponse) : 貸出・返却応答

    【例外処理】
    - HTTPException(404) : 貸出申請が取得できない場合
    - HTTPException(400) : 返却処理可能な状態ではない場合

    【処理フロー】
    1. 対象の貸出申請を取得する
    2. 返却処理する
    3. 貸出申請の詳細を取得する
    4. 戻り値を返却
    """

    # 1〜3. 対象の貸出申請取得・返却処理・貸出申請詳細取得
    loan_request_detail = services.return_loan_request(
        db, loan_request_id, current_user.id, loan_request_return_request
    )

    # 4. 戻り値を返却
    return LoanLendReturnResponse.model_validate(loan_request_detail, from_attributes=True)
