# ==================================================
# ユーザー詳細取得
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：get_user_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/ユーザー管理/ユーザー詳細取得_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 対象ユーザーの全フィールドを取得できること
def test_get_user_001_get_all_fields(client, make_user, login):
    make_user("admin01", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_user("target01", "対象ユーザー", "password1", role="general")
    token = login("admin01", "AdminPass1")

    response = client.get("/users/target01", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "target01"
    assert body["name"] == "対象ユーザー"
    assert body["department"] is None
    assert body["role"] == "general"
    assert body["is_active"] is True
    assert body["must_change_password"] is False
    assert "created_at" in body
    assert "updated_at" in body


# ========== 結合テストNo.2 ==========
# 存在しないユーザーIDを指定した場合、HTTP 404が返却されること
def test_get_user_002_not_found(client, make_user, login):
    make_user("admin02", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin02", "AdminPass1")

    response = client.get("/users/notfounduser", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404
    assert response.json()["detail"] == "ユーザーが見つかりません"


# ========== 結合テストNo.3 ==========
# 管理者権限でないユーザーが取得した場合、HTTP 403が返却されること
def test_get_user_003_forbidden_not_admin(client, make_user, login):
    make_user("u003", "一般ユーザー", "password1", role="general")
    token = login("u003", "password1")

    response = client.get("/users/u003", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.4 ==========
# 初回パスワード変更未完了の管理者が取得した場合、HTTP 403が返却されること
def test_get_user_004_forbidden_password_not_changed(client, make_user, login):
    make_user("admin04", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    token = login("admin04", "AdminPass1")

    response = client.get("/users/admin04", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.5 ==========
# トークン未指定で取得した場合、HTTP 401が返却されること
def test_get_user_005_token_missing(client, make_user):
    make_user("admin05", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)

    response = client.get("/users/admin05")

    assert response.status_code == 401


# ========== 結合テストNo.6 ==========
# user_idが下限（3文字）未満である場合、HTTP 422が返却されること
def test_get_user_006_user_id_too_short(client, make_user, login):
    make_user("admin06", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin06", "AdminPass1")

    response = client.get("/users/ab", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 422
