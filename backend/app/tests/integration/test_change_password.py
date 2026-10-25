# ==================================================
# パスワード変更
# テスト対象ファイル：auth.py
# テスト対象クラス：-
# テスト対象メソッド：change_password
# テスト仕様書：テスト仕様書/結合テスト仕様書/認証・認可（auth）/パスワード変更_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 現在パスワードが正しい場合にパスワードが変更され、新しいアクセストークンでGET /meが成功すること
def test_change_password_001_success_new_token_works(client, make_user, login):
    make_user("u001", "テスト太郎", "oldpassword1")
    old_token = login("u001", "oldpassword1")

    response = client.put(
        "/me/password",
        headers={"Authorization": f"Bearer {old_token}"},
        json={"current_password": "oldpassword1", "new_password": "newpassword1"},
    )

    assert response.status_code == 200
    new_token = response.json()["access_token"]

    me_response = client.get("/me", headers={"Authorization": f"Bearer {new_token}"})
    assert me_response.status_code == 200


# ========== 結合テストNo.2 ==========
# パスワード変更後、変更前に取得したトークンでGET /meを実行するとHTTP 401になること
def test_change_password_002_old_token_revoked(client, make_user, login):
    make_user("u002", "テスト次郎", "oldpassword1")
    old_token = login("u002", "oldpassword1")

    client.put(
        "/me/password",
        headers={"Authorization": f"Bearer {old_token}"},
        json={"current_password": "oldpassword1", "new_password": "newpassword1"},
    )

    me_response = client.get("/me", headers={"Authorization": f"Bearer {old_token}"})
    assert me_response.status_code == 401
    assert me_response.json()["detail"] == "資格情報を検証できませんでした"


# ========== 結合テストNo.3 ==========
# 初回パスワード変更未完了のユーザーがパスワードを変更すると、must_change_passwordがfalseになること
def test_change_password_003_must_change_password_becomes_false(client, make_user, login):
    make_user("u003", "テスト三郎", "oldpassword1", must_change_password=True)
    old_token = login("u003", "oldpassword1")

    change_response = client.put(
        "/me/password",
        headers={"Authorization": f"Bearer {old_token}"},
        json={"current_password": "oldpassword1", "new_password": "newpassword1"},
    )
    new_token = change_response.json()["access_token"]

    me_response = client.get("/me", headers={"Authorization": f"Bearer {new_token}"})
    assert me_response.json()["must_change_password"] is False


# ========== 結合テストNo.4 ==========
# 現在パスワードが不一致の場合、HTTP 400が返却されること
def test_change_password_004_current_password_mismatch(client, make_user, login):
    make_user("u004", "テスト四郎", "oldpassword1")
    token = login("u004", "oldpassword1")

    response = client.put(
        "/me/password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "wrongpassword1", "new_password": "newpassword1"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "現在のパスワードが正しくありません"


# ========== 結合テストNo.5 ==========
# 新しいパスワードが8文字未満の場合、HTTP 422が返却されること
def test_change_password_005_new_password_too_short(client, make_user, login):
    make_user("u005", "テスト五郎", "oldpassword1")
    token = login("u005", "oldpassword1")

    response = client.put(
        "/me/password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "oldpassword1", "new_password": "short1"},
    )

    assert response.status_code == 422


# ========== 結合テストNo.6 ==========
# トークン未指定で変更した場合、HTTP 401が返却されること
def test_change_password_006_token_missing(client):
    response = client.put(
        "/me/password",
        json={"current_password": "any", "new_password": "newpassword1"},
    )

    assert response.status_code == 401


# ========== 結合テストNo.7 ==========
# 必須パラメータ（current_password）が欠落している場合、HTTP 422が返却されること
def test_change_password_007_current_password_missing(client, make_user, login):
    make_user("u007", "テスト七郎", "oldpassword1")
    token = login("u007", "oldpassword1")

    response = client.put(
        "/me/password",
        headers={"Authorization": f"Bearer {token}"},
        json={"new_password": "newpassword1"},
    )

    assert response.status_code == 422


# ========== 結合テストNo.8 ==========
# 必須パラメータ（new_password）が欠落している場合、HTTP 422が返却されること
def test_change_password_008_new_password_missing(client, make_user, login):
    make_user("u008", "テスト八郎", "oldpassword1")
    token = login("u008", "oldpassword1")

    response = client.put(
        "/me/password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "oldpassword1"},
    )

    assert response.status_code == 422


# ========== 結合テストNo.9 ==========
# new_passwordが上限（255文字）を超過している場合、HTTP 422が返却されること
def test_change_password_009_new_password_too_long(client, make_user, login):
    make_user("u009", "テスト九郎", "oldpassword1")
    token = login("u009", "oldpassword1")

    response = client.put(
        "/me/password",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_password": "oldpassword1", "new_password": "a" * 256},
    )

    assert response.status_code == 422
