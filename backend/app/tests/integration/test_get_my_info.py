# ==================================================
# 自分情報取得
# テスト対象ファイル：auth.py
# テスト対象クラス：-
# テスト対象メソッド：get_my_info
# テスト仕様書：テスト仕様書/結合テスト仕様書/認証・認可（auth）/自分情報取得_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 有効なユーザーが自分の情報を取得できること
def test_get_my_info_001_success(client, make_user, login):
    make_user("u001", "テスト太郎", "password1", role="general")
    token = login("u001", "password1")

    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "u001"
    assert body["name"] == "テスト太郎"
    assert body["department"] is None
    assert body["role"] == "general"
    assert body["must_change_password"] is False


# ========== 結合テストNo.2 ==========
# 初回パスワード変更未完了（must_change_password=true）のユーザーでも取得できること（適用除外確認）
def test_get_my_info_002_must_change_password_true(client, make_user, login):
    make_user("u002", "テスト次郎", "password1", must_change_password=True)
    token = login("u002", "password1")

    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["must_change_password"] is True


# ========== 結合テストNo.3 ==========
# トークン未指定で取得した場合、HTTP 401が返却されること
def test_get_my_info_003_token_missing(client):
    response = client.get("/me")

    assert response.status_code == 401


# ========== 結合テストNo.4 ==========
# ログイン後に無効化されたユーザーが取得した場合、HTTP 401が返却されること
def test_get_my_info_004_deactivated_after_login(client, make_user, login, db):
    user = make_user("u004", "テスト四郎", "password1")
    token = login("u004", "password1")

    user.is_active = False
    db.commit()

    response = client.get("/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["detail"] == "資格情報を検証できませんでした"
