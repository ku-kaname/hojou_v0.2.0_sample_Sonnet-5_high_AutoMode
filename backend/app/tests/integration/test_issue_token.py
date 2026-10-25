# ==================================================
# ログイン（トークン発行）
# テスト対象ファイル：auth.py
# テスト対象クラス：-
# テスト対象メソッド：issue_token
# テスト仕様書：テスト仕様書/結合テスト仕様書/認証・認可（auth）/ログイン（トークン発行）_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 正しいユーザーID・パスワードでログインに成功し、取得したアクセストークンでGET /meが成功すること
def test_issue_token_001_login_success(client, make_user):
    make_user("u001", "テスト太郎", "correctpass1")

    response = client.post("/token", json={"user_id": "u001", "password": "correctpass1"})

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    access_token = body["access_token"]

    me_response = client.get("/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_response.status_code == 200


# ========== 結合テストNo.2 ==========
# 存在しないユーザーIDでログインした場合、HTTP 401が返却されること
def test_issue_token_002_user_not_found(client):
    response = client.post("/token", json={"user_id": "no-such-user", "password": "any-password"})

    assert response.status_code == 401
    assert response.json()["detail"] == "ユーザーIDまたはパスワードが正しくありません"


# ========== 結合テストNo.3 ==========
# パスワードが不一致の場合、HTTP 401が返却されること
def test_issue_token_003_password_mismatch(client, make_user):
    make_user("u003", "テスト三郎", "correctpass1")

    response = client.post("/token", json={"user_id": "u003", "password": "wrongpass1"})

    assert response.status_code == 401
    assert response.json()["detail"] == "ユーザーIDまたはパスワードが正しくありません"


# ========== 結合テストNo.4 ==========
# 無効化済みユーザーがログインした場合、パスワードが正しくてもHTTP 401が返却されること
def test_issue_token_004_deactivated_user(client, make_user):
    make_user("u004", "テスト四郎", "correctpass1", is_active=False)

    response = client.post("/token", json={"user_id": "u004", "password": "correctpass1"})

    assert response.status_code == 401
    assert response.json()["detail"] == "ユーザーIDまたはパスワードが正しくありません"


# ========== 結合テストNo.5 ==========
# 連続5回パスワード不一致後にロックされ、正しいパスワードでも6回目のログインが拒否されること
def test_issue_token_005_locked_after_five_failures(client, make_user):
    make_user("u005", "テスト五郎", "correctpass1")

    for _ in range(5):
        response = client.post("/token", json={"user_id": "u005", "password": "wrongpass1"})
        assert response.status_code == 401
        assert response.json()["detail"] == "ユーザーIDまたはパスワードが正しくありません"

    response = client.post("/token", json={"user_id": "u005", "password": "correctpass1"})
    assert response.status_code == 401
    assert response.json()["detail"] == (
        "連続して認証に失敗したため、一時的にログインできません。しばらくしてから再試行してください"
    )


# ========== 結合テストNo.6 ==========
# 必須パラメータ（user_id）が欠落している場合、HTTP 422が返却されること
def test_issue_token_006_user_id_missing(client):
    response = client.post("/token", json={"password": "any-password"})

    assert response.status_code == 422


# ========== 結合テストNo.7 ==========
# 必須パラメータ（password）が欠落している場合、HTTP 422が返却されること
def test_issue_token_007_password_missing(client):
    response = client.post("/token", json={"user_id": "any-id"})

    assert response.status_code == 422


# ========== 結合テストNo.8 ==========
# user_idが上限（32文字）を超過している場合、HTTP 422が返却されること
def test_issue_token_008_user_id_too_long(client):
    response = client.post("/token", json={"user_id": "a" * 33, "password": "any-password"})

    assert response.status_code == 422
