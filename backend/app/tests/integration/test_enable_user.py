# ==================================================
# ユーザー再有効化
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：enable_user_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/ユーザー管理/ユーザー再有効化_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 無効化済みのユーザーを再有効化した場合、HTTP 200・is_active=trueとなること
def test_enable_user_001_enable_disabled_user(client, make_user, login):
    make_user("admin01", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_user("target01", "対象ユーザー", "password1", role="general", is_active=False)
    token = login("admin01", "AdminPass1")

    response = client.put("/users/target01/enable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["is_active"] is True


# ========== 結合テストNo.2 ==========
# 存在しないユーザーIDを指定した場合、HTTP 404が返却されること
def test_enable_user_002_not_found(client, make_user, login):
    make_user("admin02", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin02", "AdminPass1")

    response = client.put("/users/notfounduser/enable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404
    assert response.json()["detail"] == "ユーザーが見つかりません"


# ========== 結合テストNo.3 ==========
# 既に有効化済みのユーザーを指定した場合、HTTP 400が返却されること
def test_enable_user_003_already_enabled(client, make_user, login):
    make_user("admin03", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_user("target03", "対象ユーザー", "password1", role="general", is_active=True)
    token = login("admin03", "AdminPass1")

    response = client.put("/users/target03/enable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 400
    assert response.json()["detail"] == "既に有効化されています"


# ========== 結合テストNo.4 ==========
# 管理者権限でないユーザーが再有効化した場合、HTTP 403が返却されること
def test_enable_user_004_forbidden_not_admin(client, make_user, login):
    make_user("u004", "一般ユーザー", "password1", role="general")
    make_user("target04", "対象ユーザー", "password1", role="general", is_active=False)
    token = login("u004", "password1")

    response = client.put("/users/target04/enable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.5 ==========
# 初回パスワード変更未完了の管理者が再有効化した場合、HTTP 403が返却されること
def test_enable_user_005_forbidden_password_not_changed(client, make_user, login):
    make_user("admin05", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    make_user("target05", "対象ユーザー", "password1", role="general", is_active=False)
    token = login("admin05", "AdminPass1")

    response = client.put("/users/target05/enable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.6 ==========
# トークン未指定で再有効化した場合、HTTP 401が返却されること
def test_enable_user_006_token_missing(client, make_user):
    make_user("target06", "対象ユーザー", "password1", role="general", is_active=False)

    response = client.put("/users/target06/enable")

    assert response.status_code == 401
