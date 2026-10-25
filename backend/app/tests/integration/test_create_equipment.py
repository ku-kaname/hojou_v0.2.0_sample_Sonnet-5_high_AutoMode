# ==================================================
# 備品登録
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：create_equipment_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/備品管理/備品登録_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 全フィールドを指定して登録した場合、HTTP 200で登録内容が返却されること
def test_create_equipment_001_register_all_fields(client, make_user, login):
    make_user("admin01", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin01", "AdminPass1")

    response = client.post(
        "/equipment",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_number": "AST-NEW-001",
            "name": "テストPC",
            "category": "ノートPC",
            "description": "テスト用",
            "location": "本社倉庫",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["asset_number"] == "AST-NEW-001"
    assert body["name"] == "テストPC"
    assert body["category"] == "ノートPC"
    assert body["description"] == "テスト用"
    assert body["location"] == "本社倉庫"
    assert body["is_active"] is True


# ========== 結合テストNo.2 ==========
# description・locationを省略して登録した場合、description=null・location=nullで登録されること
def test_create_equipment_002_register_without_optional_fields(client, make_user, login):
    make_user("admin02", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin02", "AdminPass1")

    response = client.post(
        "/equipment",
        headers={"Authorization": f"Bearer {token}"},
        json={"asset_number": "AST-NEW-002", "name": "テストPC2", "category": "ノートPC"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["description"] is None
    assert body["location"] is None


# ========== 結合テストNo.3 ==========
# 既に使用されている資産番号で登録した場合、HTTP 400が返却されること
def test_create_equipment_003_duplicate_asset_number(client, make_user, make_equipment, login):
    make_user("admin03", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_equipment(asset_number="AST-001")
    token = login("admin03", "AdminPass1")

    response = client.post(
        "/equipment",
        headers={"Authorization": f"Bearer {token}"},
        json={"asset_number": "AST-001", "name": "テストPC3", "category": "ノートPC"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "この資産番号は既に使用されています"


# ========== 結合テストNo.4 ==========
# 必須パラメータ（asset_number）が欠落している場合、HTTP 422が返却されること
def test_create_equipment_004_missing_required_asset_number(client, make_user, login):
    make_user("admin04", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin04", "AdminPass1")

    response = client.post(
        "/equipment",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "テストPC4", "category": "ノートPC"},
    )

    assert response.status_code == 422


# ========== 結合テストNo.5 ==========
# asset_numberが上限（32文字）を超過している場合、HTTP 422が返却されること
def test_create_equipment_005_asset_number_too_long(client, make_user, login):
    make_user("admin05", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin05", "AdminPass1")

    response = client.post(
        "/equipment",
        headers={"Authorization": f"Bearer {token}"},
        json={"asset_number": "A" * 33, "name": "テストPC5", "category": "ノートPC"},
    )

    assert response.status_code == 422


# ========== 結合テストNo.6 ==========
# asset_numberに許可されていない文字（記号等）を含む場合、HTTP 422が返却されること
def test_create_equipment_006_asset_number_invalid_character(client, make_user, login):
    make_user("admin06", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin06", "AdminPass1")

    response = client.post(
        "/equipment",
        headers={"Authorization": f"Bearer {token}"},
        json={"asset_number": "AST#001", "name": "テストPC6", "category": "ノートPC"},
    )

    assert response.status_code == 422


# ========== 結合テストNo.7 ==========
# nameが上限（100文字）を超過している場合、HTTP 422が返却されること
def test_create_equipment_007_name_too_long(client, make_user, login):
    make_user("admin07", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin07", "AdminPass1")

    response = client.post(
        "/equipment",
        headers={"Authorization": f"Bearer {token}"},
        json={"asset_number": "AST-NEW-007", "name": "a" * 101, "category": "ノートPC"},
    )

    assert response.status_code == 422


# ========== 結合テストNo.8 ==========
# categoryが上限（50文字）を超過している場合、HTTP 422が返却されること
def test_create_equipment_008_category_too_long(client, make_user, login):
    make_user("admin08", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin08", "AdminPass1")

    response = client.post(
        "/equipment",
        headers={"Authorization": f"Bearer {token}"},
        json={"asset_number": "AST-NEW-008", "name": "テストPC8", "category": "a" * 51},
    )

    assert response.status_code == 422


# ========== 結合テストNo.9 ==========
# descriptionが上限（500文字）を超過している場合、HTTP 422が返却されること
def test_create_equipment_009_description_too_long(client, make_user, login):
    make_user("admin09", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin09", "AdminPass1")

    response = client.post(
        "/equipment",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_number": "AST-NEW-009",
            "name": "テストPC9",
            "category": "ノートPC",
            "description": "a" * 501,
        },
    )

    assert response.status_code == 422


# ========== 結合テストNo.10 ==========
# locationが上限（100文字）を超過している場合、HTTP 422が返却されること
def test_create_equipment_010_location_too_long(client, make_user, login):
    make_user("admin10", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin10", "AdminPass1")

    response = client.post(
        "/equipment",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_number": "AST-NEW-010",
            "name": "テストPC10",
            "category": "ノートPC",
            "location": "a" * 101,
        },
    )

    assert response.status_code == 422


# ========== 結合テストNo.11 ==========
# 管理者権限でないユーザーが登録した場合、HTTP 403が返却されること
def test_create_equipment_011_forbidden_not_admin(client, make_user, login):
    make_user("u011", "一般ユーザー", "password1", role="general")
    token = login("u011", "password1")

    response = client.post(
        "/equipment",
        headers={"Authorization": f"Bearer {token}"},
        json={"asset_number": "AST-NEW-011", "name": "テストPC11", "category": "ノートPC"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.12 ==========
# 初回パスワード変更未完了の管理者が登録した場合、HTTP 403が返却されること
def test_create_equipment_012_forbidden_password_not_changed(client, make_user, login):
    make_user("admin12", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    token = login("admin12", "AdminPass1")

    response = client.post(
        "/equipment",
        headers={"Authorization": f"Bearer {token}"},
        json={"asset_number": "AST-NEW-012", "name": "テストPC12", "category": "ノートPC"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.13 ==========
# トークン未指定で登録した場合、HTTP 401が返却されること
def test_create_equipment_013_token_missing(client):
    response = client.post(
        "/equipment",
        json={"asset_number": "AST-NEW-013", "name": "テストPC13", "category": "ノートPC"},
    )

    assert response.status_code == 401
