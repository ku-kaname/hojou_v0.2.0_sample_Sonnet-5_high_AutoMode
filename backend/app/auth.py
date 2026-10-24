"""
認証・認可

【概要】
ログイン（トークン発行）・ログアウト・パスワード変更・自分情報取得、および各エンドポイントで利用する
有効ユーザー検証・ロール検証・初回パスワード変更検証を定義する。
アーキテクチャ方針で定める例外（認証・認可処理はオーケストレーション層を経由せずDBアクセスまで一体的に実装する）に基づき、
エンドポイント層（main.py）から直接呼び出され、本ファイル内で必要なDBアクセスを行う。
"""

import os
from datetime import datetime, timedelta

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import (
    LoginRequest,
    PasswordChangeRequest,
    TokenResponse,
    UserResponse,
    UserValidationResponse,
)

JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE = timedelta(hours=8)

_password_hash = PasswordHash.recommended()
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ユーザーの存在有無によって応答時間に差が生じないようにするため、実在しないパスワード文字列を
# あらかじめArgon2idでハッシュ化した固定値を保持する（タイミングサイドチャネル対策）。
_DUMMY_PASSWORD_HASH = _password_hash.hash("dummy-password-for-timing-attack-mitigation")


def _create_access_token(id: int, token_version: int) -> str:
    """
    アクセストークン生成

    【処理概要】
    - 内部ID・トークン世代・有効期限（現在時刻+8時間）をペイロードに設定したJWTアクセストークンを生成する。

    【パラメータ】
    - id (int) : 内部ID (必須)
    - token_version (int) : トークン世代 (必須)

    【戻り値】
    - access_token (str) : エンコードされたアクセストークン

    【例外処理】
    - なし
    """

    payload = {
        "sub": str(id),
        "token_version": token_version,
        "exp": datetime.now() + ACCESS_TOKEN_EXPIRE,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


# ====================================================================================================
# 認証・認可処理
# - issue_token : トークン発行
# - get_current_active_user : 有効ユーザー検証
# - logout : ログアウト
# - change_password : パスワード変更
# - require_admin : ロール検証
# - require_password_changed : 初回パスワード変更検証
# - get_my_info : 自分情報取得

# 設計書：認証・認可（auth）/
# ====================================================================================================


def issue_token(login_request: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    トークン発行

    設計書：認証・認可（auth）/ログイン（トークン発行）_v0.2.0.md

    【処理概要】
    - ユーザーIDでユーザーを取得し、有効性・ロック状態・パスワード一致を検証する。
    - 認証に成功した場合、トークン世代を含めたJWTアクセストークンを発行して返却する。

    【パラメータ】
    - login_request (LoginRequest) : ログイン要求 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - token_response (TokenResponse) : トークン応答

    【例外処理】
    - HTTPException(401) : ロック中の場合
    - HTTPException(401) : ユーザーが取得できない、有効フラグがfalse、またはパスワードが不一致の場合

    【処理フロー】
    1. ユーザーを取得する
    2. パスワードを比較する
    3. ログイン結果を判定する
    4. アクセストークンを発行する
    5. 戻り値を返却
    """

    # 1. ユーザーを取得する
    user = crud.get_user_by_user_id(db, login_request.user_id)

    # 2. パスワードを比較する
    comparison_target = user.hashed_password if user is not None else _DUMMY_PASSWORD_HASH
    password_matched = _password_hash.verify(login_request.password, comparison_target)

    # 3. ログイン結果を判定する
    now = datetime.now()
    if user is not None and user.locked_until is not None and user.locked_until > now:
        raise HTTPException(
            status_code=401,
            detail="連続して認証に失敗したため、一時的にログインできません。しばらくしてから再試行してください",
        )

    if user is None or not user.is_active or not password_matched:
        if user is not None:
            failed_login_count = user.failed_login_count + 1
            locked_until = now + timedelta(minutes=15) if failed_login_count >= 5 else user.locked_until
            crud.update_user_login_failure(db, user.id, failed_login_count, locked_until)
        raise HTTPException(status_code=401, detail="ユーザーIDまたはパスワードが正しくありません")

    crud.update_user_login_success(db, user.id)

    # 4. アクセストークンを発行する
    access_token = _create_access_token(user.id, user.token_version)

    # 5. 戻り値を返却
    return TokenResponse(access_token=access_token, token_type="bearer")


def get_current_active_user(
    token: str = Depends(_oauth2_scheme),
    db: Session = Depends(get_db),
) -> UserValidationResponse:
    """
    有効ユーザー検証

    設計書：認証・認可（auth）/有効ユーザー検証_v0.2.0.md

    【処理概要】
    - リクエストヘッダーのBearerトークンをデコードし、内部IDとトークン世代を取得する。
    - 内部IDからDB上のユーザーを取得し、有効フラグとトークン世代を検証したうえで、他エンドポイントへ引き渡す。

    【パラメータ】
    - token (str) : Bearerトークン (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - user_validation_response (UserValidationResponse) : 有効ユーザー検証応答

    【例外処理】
    - HTTPException(401) : トークンが無効（署名不正・期限切れ等）、またはペイロードに内部ID・トークン世代が含まれない場合
    - HTTPException(401) : ユーザーが取得できない場合
    - HTTPException(401) : 無効化済みユーザーの場合
    - HTTPException(401) : トークン世代が不一致の場合

    【処理フロー】
    1. Bearerトークンを検証する
    2. ユーザーを取得する
    3. ユーザーの有効性とトークン世代を検証する
    4. 戻り値を返却
    """

    credentials_exception = HTTPException(
        status_code=401,
        detail="資格情報を検証できませんでした",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # 1. Bearerトークンを検証する
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        id = int(payload["sub"])
        token_version = int(payload["token_version"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise credentials_exception

    # 2. ユーザーを取得する
    user = crud.get_user_by_id(db, id)
    if user is None:
        raise credentials_exception

    # 3. ユーザーの有効性とトークン世代を検証する
    if not user.is_active:
        raise credentials_exception
    if user.token_version != token_version:
        raise credentials_exception

    # 4. 戻り値を返却
    return UserValidationResponse(
        id=user.id,
        user_id=user.user_id,
        name=user.name,
        department=user.department,
        hashed_password=user.hashed_password,
        role=user.role,
        is_active=user.is_active,
        must_change_password=user.must_change_password,
        token_version=user.token_version,
    )


def logout(
    current_user: UserValidationResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    """
    ログアウト

    設計書：認証・認可（auth）/ログアウト_v0.1.0.md

    【処理概要】
    - 要求元ユーザーのトークン世代を1つ進め、それ以前に発行された全トークンによる以降のリクエストを拒否可能にする。

    【パラメータ】
    - current_user (UserValidationResponse) : 有効ユーザー検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - なし（204 No Content）

    【例外処理】
    - なし

    【処理フロー】
    1. トークン世代を進める
    2. 戻り値を返却
    """

    # 1. トークン世代を進める
    crud.increment_token_version(db, current_user.id)

    # 2. 戻り値を返却
    return None


def change_password(
    password_change_request: PasswordChangeRequest,
    current_user: UserValidationResponse = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    パスワード変更

    設計書：認証・認可（auth）/パスワード変更_v0.2.0.md

    【処理概要】
    - 現在のパスワードを検証したうえで、新しいパスワードをハッシュ化して更新する。
    - トークン世代を進めたうえで、ログアウトさせないよう新しいアクセストークンを再発行する。

    【パラメータ】
    - password_change_request (PasswordChangeRequest) : パスワード変更要求 (必須)
    - current_user (UserValidationResponse) : 有効ユーザー検証結果 (必須)
    - db (Session) : データベース (必須)

    【戻り値】
    - token_response (TokenResponse) : トークン応答

    【例外処理】
    - HTTPException(400) : 現在のパスワードが不一致の場合

    【処理フロー】
    1. 現在のパスワードを検証する
    2. 新しいパスワードを更新する
    3. アクセストークンを再発行する
    4. 戻り値を返却
    """

    # 1. 現在のパスワードを検証する
    current_password_matched = _password_hash.verify(
        password_change_request.current_password, current_user.hashed_password
    )
    if not current_password_matched:
        raise HTTPException(status_code=400, detail="現在のパスワードが正しくありません")

    # 2. 新しいパスワードを更新する
    new_hashed_password = _password_hash.hash(password_change_request.new_password)
    updated_user = crud.update_user_password(db, current_user.id, new_hashed_password)

    # 3. アクセストークンを再発行する
    access_token = _create_access_token(current_user.id, updated_user.token_version)

    # 4. 戻り値を返却
    return TokenResponse(access_token=access_token, token_type="bearer")


def require_admin(current_user: UserValidationResponse = Depends(get_current_active_user)) -> UserValidationResponse:
    """
    ロール検証

    設計書：認証・認可（auth）/ロール検証_v0.2.0.md

    【処理概要】
    - 有効ユーザー検証の結果（ロール）を用いて、管理者ロールであるかどうかを判定する。
    - 管理者でない場合はアクセスを拒否する。

    【パラメータ】
    - current_user (UserValidationResponse) : 有効ユーザー検証結果 (必須)

    【戻り値】
    - user_validation_response (UserValidationResponse) : 有効ユーザー検証応答

    【例外処理】
    - HTTPException(403) : 管理者ロールでない場合

    【処理フロー】
    1. ロールを検証する
    2. 戻り値を返却
    """

    # 1. ロールを検証する
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="この操作には管理者権限が必要です")

    # 2. 戻り値を返却
    return current_user


def require_password_changed(
    current_user: UserValidationResponse = Depends(get_current_active_user),
) -> UserValidationResponse:
    """
    初回パスワード変更検証

    設計書：認証・認可（auth）/初回パスワード変更検証_v0.2.0.md

    【処理概要】
    - 有効ユーザー検証の結果（初回パスワード変更要否フラグ）を確認する。
    - trueの場合はアクセスを拒否する（パスワード変更（F02）・ログアウト・自分情報取得の各エンドポイントには適用しない）。

    【パラメータ】
    - current_user (UserValidationResponse) : 有効ユーザー検証結果 (必須)

    【戻り値】
    - user_validation_response (UserValidationResponse) : 有効ユーザー検証応答

    【例外処理】
    - HTTPException(403) : 初回パスワード変更が未完了の場合

    【処理フロー】
    1. 初回パスワード変更要否を検証する
    2. 戻り値を返却
    """

    # 1. 初回パスワード変更要否を検証する
    if current_user.must_change_password:
        raise HTTPException(
            status_code=403, detail="初回パスワードの変更が完了していません。パスワードを変更してください"
        )

    # 2. 戻り値を返却
    return current_user


def get_my_info(current_user: UserValidationResponse = Depends(get_current_active_user)) -> UserResponse:
    """
    自分情報取得

    設計書：認証・認可（auth）/自分情報取得_v0.2.0.md

    【処理概要】
    - 有効ユーザー検証の結果から、画面表示・初回パスワード変更要否判定に必要な項目のみを抽出して返却する。

    【パラメータ】
    - current_user (UserValidationResponse) : 有効ユーザー検証結果 (必須)

    【戻り値】
    - user_response (UserResponse) : ユーザー情報応答

    【例外処理】
    - なし

    【処理フロー】
    1. 戻り値を返却
    """

    # 1. 戻り値を返却
    return UserResponse(
        user_id=current_user.user_id,
        name=current_user.name,
        department=current_user.department,
        role=current_user.role,
        must_change_password=current_user.must_change_password,
    )
