from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app import auth
from app.schemas import LoginRequest

# ==================================================
# ログイン（トークン発行）
# テスト対象ファイル：auth.py
# テスト対象クラス：-
# テスト対象メソッド：issue_token
# テスト仕様書：テスト仕様書/単体テスト仕様書/認証・認可（auth）/ログイン（トークン発行）_単体テスト仕様書.md
# ==================================================


def _make_user(**overrides):
    # テスト用のユーザー情報（issue_tokenが参照する属性のみを持つ）
    user = SimpleNamespace(
        id=1,
        hashed_password="hashed-password",
        is_active=True,
        locked_until=None,
        failed_login_count=0,
        token_version=0,
    )
    for key, value in overrides.items():
        setattr(user, key, value)
    return user


# ========== 単体テストNo.1 ==========
# ユーザーIDに対応するユーザーが存在しない場合でもダミーハッシュとの比較が実行され
# （タイミングサイドチャネル対策）、401エラーが発生し連続認証失敗回数の更新が行われないこと
def test_issue_token_001_user_not_found(mocker):
    mocker.patch.object(auth.crud, "get_user_by_user_id", return_value=None)
    mock_verify = mocker.patch.object(auth._password_hash, "verify", return_value=False)
    mock_update_failure = mocker.patch.object(auth.crud, "update_user_login_failure")
    mock_update_success = mocker.patch.object(auth.crud, "update_user_login_success")

    login_request = LoginRequest(user_id="no-such-user", password="any-password")

    with pytest.raises(HTTPException) as exc_info:
        auth.issue_token(login_request, db=mocker.Mock())

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "ユーザーIDまたはパスワードが正しくありません"
    mock_verify.assert_called_once_with("any-password", auth._DUMMY_PASSWORD_HASH)
    mock_update_failure.assert_not_called()
    mock_update_success.assert_not_called()


# ========== 単体テストNo.2 ==========
# ロック解除日時が現在時刻より未来のユーザーでログインした場合、パスワードの一致有無にかかわらず
# 401エラーが発生し連続認証失敗回数が更新されないこと
def test_issue_token_002_locked(mocker):
    user = _make_user(locked_until=datetime.now() + timedelta(minutes=30))
    mocker.patch.object(auth.crud, "get_user_by_user_id", return_value=user)
    mocker.patch.object(auth._password_hash, "verify", return_value=True)
    mock_update_failure = mocker.patch.object(auth.crud, "update_user_login_failure")
    mock_update_success = mocker.patch.object(auth.crud, "update_user_login_success")

    login_request = LoginRequest(user_id="user1", password="correct-password")

    with pytest.raises(HTTPException) as exc_info:
        auth.issue_token(login_request, db=mocker.Mock())

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == (
        "連続して認証に失敗したため、一時的にログインできません。しばらくしてから再試行してください"
    )
    mock_update_failure.assert_not_called()
    mock_update_success.assert_not_called()


# ========== 単体テストNo.3 ==========
# ロック解除日時が設定されているが現在時刻より過去の場合、ロック中と判定されず通常の認証処理が行われること
def test_issue_token_003_lock_expired(mocker):
    user = _make_user(locked_until=datetime.now() - timedelta(minutes=1), failed_login_count=2)
    mocker.patch.object(auth.crud, "get_user_by_user_id", return_value=user)
    mocker.patch.object(auth._password_hash, "verify", return_value=True)
    mock_update_success = mocker.patch.object(auth.crud, "update_user_login_success")
    mocker.patch.object(auth, "_create_access_token", return_value="dummy-token")

    login_request = LoginRequest(user_id="user1", password="correct-password")

    token_response = auth.issue_token(login_request, db=mocker.Mock())

    mock_update_success.assert_called_once_with(mocker.ANY, user.id)
    assert token_response.token_type == "bearer"


# ========== 単体テストNo.4 ==========
# 有効フラグがfalseのユーザーが正しいパスワードでログインした場合、401エラーが発生し
# 連続認証失敗回数が加算されること
def test_issue_token_004_inactive_user(mocker):
    user = _make_user(is_active=False, locked_until=None, failed_login_count=0)
    mocker.patch.object(auth.crud, "get_user_by_user_id", return_value=user)
    mocker.patch.object(auth._password_hash, "verify", return_value=True)
    mock_update_failure = mocker.patch.object(auth.crud, "update_user_login_failure")

    login_request = LoginRequest(user_id="user1", password="correct-password")

    with pytest.raises(HTTPException) as exc_info:
        auth.issue_token(login_request, db=mocker.Mock())

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "ユーザーIDまたはパスワードが正しくありません"
    mock_update_failure.assert_called_once_with(mocker.ANY, user.id, 1, None)


# ========== 単体テストNo.5 ==========
# パスワード不一致で、加算後の連続認証失敗回数が5未満の場合、401エラーが発生しロック解除日時が
# 既存値のまま更新されないこと
def test_issue_token_005_password_mismatch_under_limit(mocker):
    user = _make_user(is_active=True, locked_until=None, failed_login_count=2)
    mocker.patch.object(auth.crud, "get_user_by_user_id", return_value=user)
    mocker.patch.object(auth._password_hash, "verify", return_value=False)
    mock_update_failure = mocker.patch.object(auth.crud, "update_user_login_failure")

    login_request = LoginRequest(user_id="user1", password="wrong-password")

    with pytest.raises(HTTPException) as exc_info:
        auth.issue_token(login_request, db=mocker.Mock())

    assert exc_info.value.status_code == 401
    mock_update_failure.assert_called_once_with(mocker.ANY, user.id, 3, None)


# ========== 単体テストNo.6 ==========
# 加算後の連続認証失敗回数が5に達する場合、ロック解除日時に現在時刻+15分が設定されること
def test_issue_token_006_password_mismatch_reaches_limit(mocker):
    user = _make_user(is_active=True, locked_until=None, failed_login_count=4)
    mocker.patch.object(auth.crud, "get_user_by_user_id", return_value=user)
    mocker.patch.object(auth._password_hash, "verify", return_value=False)
    mock_update_failure = mocker.patch.object(auth.crud, "update_user_login_failure")

    login_request = LoginRequest(user_id="user1", password="wrong-password")

    with pytest.raises(HTTPException):
        auth.issue_token(login_request, db=mocker.Mock())

    mock_update_failure.assert_called_once()
    call_args = mock_update_failure.call_args.args
    assert call_args[1] == user.id
    assert call_args[2] == 5
    expected_locked_until = datetime.now() + timedelta(minutes=15)
    assert abs((call_args[3] - expected_locked_until).total_seconds()) < 5


# ========== 単体テストNo.7 ==========
# 有効フラグがtrue、未ロック、パスワードが一致する場合、連続認証失敗回数が0にリセットされ
# アクセストークンが返却されること
def test_issue_token_007_success(mocker):
    user = _make_user(is_active=True, locked_until=None, failed_login_count=3)
    mocker.patch.object(auth.crud, "get_user_by_user_id", return_value=user)
    mocker.patch.object(auth._password_hash, "verify", return_value=True)
    mock_update_success = mocker.patch.object(auth.crud, "update_user_login_success")
    mock_update_failure = mocker.patch.object(auth.crud, "update_user_login_failure")
    mocker.patch.object(auth, "_create_access_token", return_value="dummy-token")

    login_request = LoginRequest(user_id="user1", password="correct-password")

    token_response = auth.issue_token(login_request, db=mocker.Mock())

    mock_update_success.assert_called_once_with(mocker.ANY, user.id)
    mock_update_failure.assert_not_called()
    assert token_response.token_type == "bearer"


# ========== 単体テストNo.8 ==========
# 認証成功時、_create_access_tokenが取得したユーザーの内部ID・トークン世代を引数として呼び出されること
def test_issue_token_008_access_token_arguments(mocker):
    user = _make_user(id=10, is_active=True, locked_until=None, failed_login_count=3, token_version=2)
    mocker.patch.object(auth.crud, "get_user_by_user_id", return_value=user)
    mocker.patch.object(auth._password_hash, "verify", return_value=True)
    mocker.patch.object(auth.crud, "update_user_login_success")
    mock_create_access_token = mocker.patch.object(auth, "_create_access_token", return_value="dummy-token")

    login_request = LoginRequest(user_id="user1", password="correct-password")

    auth.issue_token(login_request, db=mocker.Mock())

    mock_create_access_token.assert_called_once_with(10, 2)
