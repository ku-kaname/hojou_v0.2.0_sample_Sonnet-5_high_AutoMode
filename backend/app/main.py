"""
エンドポイント（共通）

【概要】
ヘルスチェック・認証・認可（auth）・通知の各エンドポイント、およびアプリケーション起動時処理
（初期管理者アカウント自動作成・日次バッチ起動定義）を定義する。他機能群のエンドポイントは各機能群バックログで追加する。
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from pwdlib import PasswordHash
from sqlalchemy import text
from sqlalchemy.orm import Session

from app import auth, crud, scheduler, services
from app.database import SessionLocal, get_db
from app.schemas import NotificationResponse, UserValidationResponse

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
