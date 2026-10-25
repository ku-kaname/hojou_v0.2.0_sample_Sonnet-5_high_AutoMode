# ==================================================
# パスワード初期化
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：reset_user_password_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/ユーザー管理/パスワード初期化_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# パスワードを初期化した場合、must_change_password=trueとなり、新パスワードでログインできること
def test_reset_user_password_001_reset_and_login_with_new_password(client, make_user, login):
    make_user("admin01", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_user("target01", "対象ユーザー", "password1", role="general")
    token = login("admin01", "AdminPass1")

    response = client.put(
        "/users/target01/reset-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": "ResetPass123"},
    )

    assert response.status_code == 200
    assert response.json()["must_change_password"] is True

    login_response = client.post("/token", json={"user_id": "target01", "password": "ResetPass123"})
    assert login_response.status_code == 200


# ========== 結合テストNo.2 ==========
# パスワード初期化により、既発行の旧トークンが失効すること
def test_reset_user_password_002_revokes_old_token(client, make_user, login):
    make_user("admin02", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_user("target02", "対象ユーザー", "password1", role="general")
    admin_token = login("admin02", "AdminPass1")
    old_token = login("target02", "password1")

    response = client.put(
        "/users/target02/reset-password",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"password": "ResetPass123"},
    )

    assert response.status_code == 200

    old_token_response = client.get("/me", headers={"Authorization": f"Bearer {old_token}"})
    assert old_token_response.status_code == 401
    assert old_token_response.json()["detail"] == "資格情報を検証できませんでした"


# ========== 結合テストNo.3 ==========
# 存在しないユーザーIDを指定した場合、HTTP 404が返却されること
def test_reset_user_password_003_not_found(client, make_user, login):
    make_user("admin03", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin03", "AdminPass1")

    response = client.put(
        "/users/notfounduser/reset-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": "ResetPass123"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "ユーザーが見つかりません"


# ========== 結合テストNo.4 ==========
# 新パスワードが下限（8文字）未満である場合、HTTP 422が返却されること
def test_reset_user_password_004_password_too_short(client, make_user, login):
    make_user("admin04", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_user("target04", "対象ユーザー", "password1", role="general")
    token = login("admin04", "AdminPass1")

    response = client.put(
        "/users/target04/reset-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": "short1"},
    )

    assert response.status_code == 422


# ========== 結合テストNo.5 ==========
# 必須パラメータ（password）が欠落している場合、HTTP 422が返却されること
def test_reset_user_password_005_missing_required_password(client, make_user, login):
    make_user("admin05", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_user("target05", "対象ユーザー", "password1", role="general")
    token = login("admin05", "AdminPass1")

    response = client.put(
        "/users/target05/reset-password",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    assert response.status_code == 422


# ========== 結合テストNo.6 ==========
# 管理者権限でないユーザーが初期化した場合、HTTP 403が返却されること
def test_reset_user_password_006_forbidden_not_admin(client, make_user, login):
    make_user("u006", "一般ユーザー", "password1", role="general")
    token = login("u006", "password1")

    response = client.put(
        "/users/u006/reset-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": "ResetPass123"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.7 ==========
# 初回パスワード変更未完了の管理者が初期化した場合、HTTP 403が返却されること
def test_reset_user_password_007_forbidden_password_not_changed(client, make_user, login):
    make_user("admin07", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    make_user("target07", "対象ユーザー", "password1", role="general")
    token = login("admin07", "AdminPass1")

    response = client.put(
        "/users/target07/reset-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": "ResetPass123"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.8 ==========
# トークン未指定で初期化した場合、HTTP 401が返却されること
def test_reset_user_password_008_token_missing(client, make_user):
    make_user("target08", "対象ユーザー", "password1", role="general")

    response = client.put("/users/target08/reset-password", json={"password": "ResetPass123"})

    assert response.status_code == 401
