from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app import services
from app.schemas import UserUpdateRequest

# ==================================================
# ユーザー編集
# テスト対象ファイル：services.py
# テスト対象クラス：-
# テスト対象メソッド：update_user
# テスト仕様書：テスト仕様書/単体テスト仕様書/サーバー処理（main）/ユーザー管理/ユーザー編集_単体テスト仕様書.md
# ==================================================


def _make_target_user(**overrides):
    # テスト用の対象ユーザー情報（update_user・disable_userが参照する属性のみを持つ）
    user = SimpleNamespace(
        id=1,
        role="general",
        is_active=True,
        token_version=0,
    )
    for key, value in overrides.items():
        setattr(user, key, value)
    return user


def _make_update_request(name="テスト太郎", department="総務部", role="general"):
    return UserUpdateRequest(name=name, department=department, role=role)


# ========== 単体テストNo.1 ==========
# 対象ユーザーが取得できない場合、404エラーが発生すること
def test_update_user_001_user_not_found(mocker):
    mocker.patch.object(services.crud, "get_user_by_user_id", return_value=None)
    mock_update = mocker.patch.object(services.crud, "update_user")

    with pytest.raises(HTTPException) as exc_info:
        services.update_user(mocker.Mock(), "no-such-user", _make_update_request())

    assert exc_info.value.status_code == 404
    mock_update.assert_not_called()


# ========== 単体テストNo.2 ==========
# 最後の有効な管理者を一般ユーザーに変更しようとした場合、400エラーが発生すること
def test_update_user_002_demote_last_admin(mocker):
    target_user = _make_target_user(role="admin", is_active=True)
    mocker.patch.object(services.crud, "get_user_by_user_id", return_value=target_user)
    mocker.patch.object(services.crud, "count_active_admins", return_value=1)
    mock_update = mocker.patch.object(services.crud, "update_user")

    with pytest.raises(HTTPException) as exc_info:
        services.update_user(mocker.Mock(), "admin1", _make_update_request(role="general"))

    assert exc_info.value.status_code == 400
    mock_update.assert_not_called()


# ========== 単体テストNo.3 ==========
# 複数の有効な管理者が存在する状態で管理者を一般ユーザーに変更する場合、正常にトークン世代が1増加して更新されること
def test_update_user_003_demote_admin_with_multiple_admins(mocker):
    target_user = _make_target_user(id=5, role="admin", is_active=True, token_version=1)
    mocker.patch.object(services.crud, "get_user_by_user_id", return_value=target_user)
    mocker.patch.object(services.crud, "count_active_admins", return_value=2)
    mock_update = mocker.patch.object(services.crud, "update_user", return_value="updated-user")

    result = services.update_user(mocker.Mock(), "admin1", _make_update_request(role="general"))

    mock_update.assert_called_once_with(mocker.ANY, 5, "テスト太郎", "総務部", "general", 2)
    assert result == "updated-user"


# ========== 単体テストNo.4 ==========
# 既に無効化済みの管理者を一般ユーザーに変更する場合、最後の管理者確認が行われず正常に更新されること
def test_update_user_004_demote_inactive_admin(mocker):
    target_user = _make_target_user(id=6, role="admin", is_active=False, token_version=0)
    mocker.patch.object(services.crud, "get_user_by_user_id", return_value=target_user)
    mock_count = mocker.patch.object(services.crud, "count_active_admins")
    mock_update = mocker.patch.object(services.crud, "update_user", return_value="updated-user")

    services.update_user(mocker.Mock(), "admin1", _make_update_request(role="general"))

    mock_count.assert_not_called()
    mock_update.assert_called_once_with(mocker.ANY, 6, "テスト太郎", "総務部", "general", 1)


# ========== 単体テストNo.5 ==========
# ロールの変更がない場合（一般→一般）、トークン世代が変更されないこと
def test_update_user_005_role_unchanged_general(mocker):
    target_user = _make_target_user(id=7, role="general", is_active=True, token_version=3)
    mocker.patch.object(services.crud, "get_user_by_user_id", return_value=target_user)
    mock_update = mocker.patch.object(services.crud, "update_user", return_value="updated-user")

    services.update_user(mocker.Mock(), "user1", _make_update_request(role="general"))

    mock_update.assert_called_once_with(mocker.ANY, 7, "テスト太郎", "総務部", "general", 3)


# ========== 単体テストNo.6 ==========
# 一般ユーザーを管理者に変更する場合、最後の管理者確認が行われずトークン世代が1増加すること
def test_update_user_006_promote_to_admin(mocker):
    target_user = _make_target_user(id=8, role="general", is_active=True, token_version=0)
    mocker.patch.object(services.crud, "get_user_by_user_id", return_value=target_user)
    mock_count = mocker.patch.object(services.crud, "count_active_admins")
    mock_update = mocker.patch.object(services.crud, "update_user", return_value="updated-user")

    services.update_user(mocker.Mock(), "user1", _make_update_request(role="admin"))

    mock_count.assert_not_called()
    mock_update.assert_called_once_with(mocker.ANY, 8, "テスト太郎", "総務部", "admin", 1)


# ========== 単体テストNo.7 ==========
# ロールの変更がない場合（管理者→管理者）、最後の管理者確認が行われずトークン世代が変更されないこと
def test_update_user_007_role_unchanged_admin(mocker):
    target_user = _make_target_user(id=9, role="admin", is_active=True, token_version=2)
    mocker.patch.object(services.crud, "get_user_by_user_id", return_value=target_user)
    mock_count = mocker.patch.object(services.crud, "count_active_admins")
    mock_update = mocker.patch.object(services.crud, "update_user", return_value="updated-user")

    services.update_user(mocker.Mock(), "admin1", _make_update_request(role="admin"))

    mock_count.assert_not_called()
    mock_update.assert_called_once_with(mocker.ANY, 9, "テスト太郎", "総務部", "admin", 2)


# ==================================================
# ユーザー無効化
# テスト対象ファイル：services.py
# テスト対象クラス：-
# テスト対象メソッド：disable_user
# テスト仕様書：テスト仕様書/単体テスト仕様書/サーバー処理（main）/ユーザー管理/ユーザー無効化_単体テスト仕様書.md
# ==================================================


# ========== 単体テストNo.1 ==========
# 対象ユーザーが取得できない場合、404エラーが発生すること
def test_disable_user_001_user_not_found(mocker):
    mocker.patch.object(services.crud, "get_user_by_user_id", return_value=None)
    mock_disable = mocker.patch.object(services.crud, "disable_user")

    with pytest.raises(HTTPException) as exc_info:
        services.disable_user(mocker.Mock(), "no-such-user")

    assert exc_info.value.status_code == 404
    mock_disable.assert_not_called()


# ========== 単体テストNo.2 ==========
# 対象ユーザーが既に無効化済みの場合、400エラーが発生すること
def test_disable_user_002_already_disabled(mocker):
    target_user = _make_target_user(is_active=False)
    mocker.patch.object(services.crud, "get_user_by_user_id", return_value=target_user)
    mock_disable = mocker.patch.object(services.crud, "disable_user")

    with pytest.raises(HTTPException) as exc_info:
        services.disable_user(mocker.Mock(), "user1")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "既に無効化されています"
    mock_disable.assert_not_called()


# ========== 単体テストNo.3 ==========
# 最後の有効な管理者を無効化しようとした場合、400エラーが発生すること
def test_disable_user_003_disable_last_admin(mocker):
    target_user = _make_target_user(role="admin", is_active=True)
    mocker.patch.object(services.crud, "get_user_by_user_id", return_value=target_user)
    mocker.patch.object(services.crud, "count_active_admins", return_value=1)
    mock_disable = mocker.patch.object(services.crud, "disable_user")

    with pytest.raises(HTTPException) as exc_info:
        services.disable_user(mocker.Mock(), "admin1")

    assert exc_info.value.status_code == 400
    mock_disable.assert_not_called()


# ========== 単体テストNo.4 ==========
# 複数の有効な管理者が存在する状態で管理者を無効化する場合、処理が通過すること
def test_disable_user_004_disable_admin_with_multiple_admins(mocker):
    target_user = _make_target_user(id=5, role="admin", is_active=True, token_version=1)
    mocker.patch.object(services.crud, "get_user_by_user_id", return_value=target_user)
    mocker.patch.object(services.crud, "count_active_admins", return_value=2)
    mocker.patch.object(services.crud, "exists_lending_loan_request_by_applicant", return_value=False)
    mock_cancel = mocker.patch.object(services.crud, "cancel_pending_and_approved_loan_requests_by_applicant")
    mock_disable = mocker.patch.object(services.crud, "disable_user", return_value="disabled-user")

    result = services.disable_user(mocker.Mock(), "admin1")

    mock_cancel.assert_called_once_with(mocker.ANY, 5)
    mock_disable.assert_called_once_with(mocker.ANY, 5, 2)
    assert result == "disabled-user"


# ========== 単体テストNo.5 ==========
# 一般ユーザーを無効化する場合、最後の管理者確認が行われないこと
def test_disable_user_005_disable_general_user(mocker):
    target_user = _make_target_user(id=6, role="general", is_active=True, token_version=0)
    mocker.patch.object(services.crud, "get_user_by_user_id", return_value=target_user)
    mock_count = mocker.patch.object(services.crud, "count_active_admins")
    mocker.patch.object(services.crud, "exists_lending_loan_request_by_applicant", return_value=False)
    mocker.patch.object(services.crud, "cancel_pending_and_approved_loan_requests_by_applicant")
    mocker.patch.object(services.crud, "disable_user", return_value="disabled-user")

    services.disable_user(mocker.Mock(), "user1")

    mock_count.assert_not_called()


# ========== 単体テストNo.6 ==========
# 貸出中の申請が存在する場合、400エラーが発生すること
def test_disable_user_006_has_lending_loan_request(mocker):
    target_user = _make_target_user(id=7, role="general", is_active=True)
    mocker.patch.object(services.crud, "get_user_by_user_id", return_value=target_user)
    mocker.patch.object(services.crud, "exists_lending_loan_request_by_applicant", return_value=True)
    mock_cancel = mocker.patch.object(services.crud, "cancel_pending_and_approved_loan_requests_by_applicant")
    mock_disable = mocker.patch.object(services.crud, "disable_user")

    with pytest.raises(HTTPException) as exc_info:
        services.disable_user(mocker.Mock(), "user1")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "貸出中の備品があるため無効化できません"
    mock_cancel.assert_not_called()
    mock_disable.assert_not_called()


# ========== 単体テストNo.7 ==========
# 貸出中の申請がない場合、申請中・承認済みの申請が自動取消され、無効化が行われトークン世代が1増加すること
def test_disable_user_007_success(mocker):
    target_user = _make_target_user(id=8, role="general", is_active=True, token_version=4)
    mocker.patch.object(services.crud, "get_user_by_user_id", return_value=target_user)
    mocker.patch.object(services.crud, "exists_lending_loan_request_by_applicant", return_value=False)
    mock_cancel = mocker.patch.object(services.crud, "cancel_pending_and_approved_loan_requests_by_applicant")
    mock_disable = mocker.patch.object(services.crud, "disable_user", return_value="disabled-user")

    result = services.disable_user(mocker.Mock(), "user1")

    mock_cancel.assert_called_once_with(mocker.ANY, 8)
    mock_disable.assert_called_once_with(mocker.ANY, 8, 5)
    assert result == "disabled-user"
