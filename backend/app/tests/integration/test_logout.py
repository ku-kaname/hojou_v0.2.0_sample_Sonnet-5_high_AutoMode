# ==================================================
# ログアウト
# テスト対象ファイル：auth.py
# テスト対象クラス：-
# テスト対象メソッド：logout
# テスト仕様書：テスト仕様書/結合テスト仕様書/認証・認可（auth）/ログアウト_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# ログアウト成功後、ログアウト前に発行されたトークンでGET /meを実行するとHTTP 401になること
def test_logout_001_success_old_token_rejected(client, make_user, login):
    make_user("u001", "テスト太郎", "password1")
    token = login("u001", "password1")
    headers = {"Authorization": f"Bearer {token}"}

    logout_response = client.post("/logout", headers=headers)
    assert logout_response.status_code == 204

    me_response = client.get("/me", headers=headers)
    assert me_response.status_code == 401
    assert me_response.json()["detail"] == "資格情報を検証できませんでした"


# ========== 結合テストNo.2 ==========
# トークン未指定でログアウトした場合、HTTP 401が返却されること
def test_logout_002_token_missing(client):
    response = client.post("/logout")

    assert response.status_code == 401


# ========== 結合テストNo.3 ==========
# 無効なトークンでログアウトした場合、HTTP 401が返却されること
def test_logout_003_invalid_token(client):
    response = client.post("/logout", headers={"Authorization": "Bearer invalid-token-xyz"})

    assert response.status_code == 401
