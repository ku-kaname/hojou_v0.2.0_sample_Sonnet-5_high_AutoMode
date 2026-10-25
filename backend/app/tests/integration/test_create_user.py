# ==================================================
# ユーザー登録
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：create_user_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/ユーザー管理/ユーザー登録_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 全フィールドを指定して登録した場合、HTTP 200で登録内容が返却されること
def test_create_user_001_register_all_fields(client, make_user, login):
    make_user("admin01", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin01", "AdminPass1")

    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "user_id": "newuser1",
            "name": "テスト太郎",
            "department": "総務部",
            "password": "NewPass123",
            "role": "general",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["user_id"] == "newuser1"
    assert body["name"] == "テスト太郎"
    assert body["department"] == "総務部"
    assert body["role"] == "general"
    assert body["is_active"] is True
    assert body["must_change_password"] is True


# ========== 結合テストNo.2 ==========
# departmentを省略して登録した場合、department=nullで登録されること
def test_create_user_002_register_without_department(client, make_user, login):
    make_user("admin02", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin02", "AdminPass1")

    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": "newuser2", "name": "テスト次郎", "password": "NewPass123", "role": "general"},
    )

    assert response.status_code == 200
    assert response.json()["department"] is None


# ========== 結合テストNo.3 ==========
# 既に使用されているユーザーIDで登録した場合、HTTP 400が返却されること
def test_create_user_003_duplicate_user_id(client, make_user, login):
    make_user("admin03", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_user("u001", "既存ユーザー", "password1", role="general")
    token = login("admin03", "AdminPass1")

    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": "u001", "name": "テスト三郎", "password": "NewPass123", "role": "general"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "このユーザーIDは既に使用されています"


# ========== 結合テストNo.4 ==========
# 管理者権限でないユーザーが登録した場合、HTTP 403が返却されること
def test_create_user_004_forbidden_not_admin(client, make_user, login):
    make_user("u004", "一般ユーザー", "password1", role="general")
    token = login("u004", "password1")

    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": "newuser4", "name": "テスト四郎", "password": "NewPass123", "role": "general"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.5 ==========
# 初回パスワード変更未完了の管理者が登録した場合、HTTP 403が返却されること
def test_create_user_005_forbidden_password_not_changed(client, make_user, login):
    make_user("admin05", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    token = login("admin05", "AdminPass1")

    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": "newuser5", "name": "テスト五郎", "password": "NewPass123", "role": "general"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.6 ==========
# トークン未指定で登録した場合、HTTP 401が返却されること
def test_create_user_006_token_missing(client):
    response = client.post(
        "/users",
        json={"user_id": "newuser6", "name": "テスト六郎", "password": "NewPass123", "role": "general"},
    )

    assert response.status_code == 401


# ========== 結合テストNo.7 ==========
# 必須パラメータ（user_id）が欠落している場合、HTTP 422が返却されること
def test_create_user_007_missing_required_user_id(client, make_user, login):
    make_user("admin07", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin07", "AdminPass1")

    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "テスト七郎", "password": "NewPass123", "role": "general"},
    )

    assert response.status_code == 422


# ========== 結合テストNo.8 ==========
# パスワードが下限（8文字）未満である場合、HTTP 422が返却されること
def test_create_user_008_password_too_short(client, make_user, login):
    make_user("admin08", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin08", "AdminPass1")

    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": "newuser8", "name": "テスト八郎", "password": "short1", "role": "general"},
    )

    assert response.status_code == 422


# ========== 結合テストNo.9 ==========
# user_idに許可されていない文字（記号等）を含む場合、HTTP 422が返却されること
def test_create_user_009_user_id_invalid_character(client, make_user, login):
    make_user("admin09", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin09", "AdminPass1")

    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": "newuser!9", "name": "テスト九郎", "password": "NewPass123", "role": "general"},
    )

    assert response.status_code == 422


# ========== 結合テストNo.10 ==========
# nameが上限（50文字）を超過している場合、HTTP 422が返却されること
def test_create_user_010_name_too_long(client, make_user, login):
    make_user("admin10", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin10", "AdminPass1")

    response = client.post(
        "/users",
        headers={"Authorization": f"Bearer {token}"},
        json={"user_id": "newuser10", "name": "a" * 51, "password": "NewPass123", "role": "general"},
    )

    assert response.status_code == 422
