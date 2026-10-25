from app import crud

# ==================================================
# ユーザー無効化
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：disable_user_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/ユーザー管理/ユーザー無効化_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 一般ユーザーを無効化した場合、HTTP 200・is_active=false・トークン世代更新（旧トークン失効）となること
def test_disable_user_001_disable_general_user(client, make_user, login):
    make_user("admin01", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_user("target01", "対象ユーザー", "password1", role="general")
    admin_token = login("admin01", "AdminPass1")
    old_token = login("target01", "password1")

    response = client.put("/users/target01/disable", headers={"Authorization": f"Bearer {admin_token}"})

    assert response.status_code == 200
    assert response.json()["is_active"] is False

    old_token_response = client.get("/me", headers={"Authorization": f"Bearer {old_token}"})
    assert old_token_response.status_code == 401
    assert old_token_response.json()["detail"] == "資格情報を検証できませんでした"


# ========== 結合テストNo.2 ==========
# 無効化に伴い、申請中・承認済みの貸出申請が自動的に取消される（他ユーザーの申請は対象外）こと
def test_disable_user_002_auto_cancel_pending_and_approved_requests(
    client, make_user, login, make_loan_request, db
):
    make_user("admin02", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    target = make_user("target02", "対象ユーザー", "password1", role="general")
    other = make_user("other02", "別ユーザー", "password1", role="general")
    admin_token = login("admin02", "AdminPass1")

    pending_request = make_loan_request(target.id, status="pending")
    approved_request = make_loan_request(target.id, status="approved")
    other_pending_request = make_loan_request(other.id, status="pending")

    response = client.put("/users/target02/disable", headers={"Authorization": f"Bearer {admin_token}"})

    assert response.status_code == 200

    db.refresh(pending_request)
    db.refresh(approved_request)
    db.refresh(other_pending_request)
    assert pending_request.status == "cancelled"
    assert pending_request.rejection_reason == "ユーザー無効化による自動取消"
    assert approved_request.status == "cancelled"
    assert approved_request.rejection_reason == "ユーザー無効化による自動取消"
    # 無効化対象外の別ユーザーの申請は変更されないこと
    assert other_pending_request.status == "pending"


# ========== 結合テストNo.3 ==========
# 存在しないユーザーIDを指定した場合、HTTP 404が返却されること
def test_disable_user_003_not_found(client, make_user, login):
    make_user("admin03", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin03", "AdminPass1")

    response = client.put("/users/notfounduser/disable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404
    assert response.json()["detail"] == "ユーザーが見つかりません"


# ========== 結合テストNo.4 ==========
# 既に無効化済みのユーザーを指定した場合、HTTP 400が返却されること
def test_disable_user_004_already_disabled(client, make_user, login):
    make_user("admin04", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_user("target04", "対象ユーザー", "password1", role="general", is_active=False)
    token = login("admin04", "AdminPass1")

    response = client.put("/users/target04/disable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 400
    assert response.json()["detail"] == "既に無効化されています"


# ========== 結合テストNo.5 ==========
# 最後の有効な管理者を無効化しようとした場合、HTTP 400が返却されること
def test_disable_user_005_last_admin_cannot_disable(client, db, login):
    # 初期管理者("admin")を唯一の有効な管理者として利用する
    admin = crud.get_user_by_user_id(db, "admin")
    admin.must_change_password = False
    db.commit()
    token = login("admin", "AdminInitPass1")

    response = client.put("/users/admin/disable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 400
    assert response.json()["detail"] == "最後の管理者を無効化することはできません"


# ========== 結合テストNo.6 ==========
# 貸出中（lending）の貸出申請が存在する場合、HTTP 400が返却されること
def test_disable_user_006_lending_request_exists(client, make_user, login, make_loan_request):
    make_user("admin06", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    target = make_user("target06", "対象ユーザー", "password1", role="general")
    token = login("admin06", "AdminPass1")
    make_loan_request(target.id, status="lending")

    response = client.put("/users/target06/disable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 400
    assert response.json()["detail"] == "貸出中の備品があるため無効化できません"


# ========== 結合テストNo.7 ==========
# 管理者権限でないユーザーが無効化した場合、HTTP 403が返却されること
def test_disable_user_007_forbidden_not_admin(client, make_user, login):
    make_user("u007", "一般ユーザー", "password1", role="general")
    make_user("target07", "対象ユーザー", "password1", role="general")
    token = login("u007", "password1")

    response = client.put("/users/target07/disable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.8 ==========
# 初回パスワード変更未完了の管理者が無効化した場合、HTTP 403が返却されること
def test_disable_user_008_forbidden_password_not_changed(client, make_user, login):
    make_user("admin08", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    make_user("target08", "対象ユーザー", "password1", role="general")
    token = login("admin08", "AdminPass1")

    response = client.put("/users/target08/disable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.9 ==========
# トークン未指定で無効化した場合、HTTP 401が返却されること
def test_disable_user_009_token_missing(client, make_user):
    make_user("target09", "対象ユーザー", "password1", role="general")

    response = client.put("/users/target09/disable")

    assert response.status_code == 401
