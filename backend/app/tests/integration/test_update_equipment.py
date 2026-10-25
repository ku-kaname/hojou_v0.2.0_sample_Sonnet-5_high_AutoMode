# ==================================================
# 備品編集
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：update_equipment_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/備品管理/備品編集_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 全フィールドを指定して編集した場合、HTTP 200で編集内容が返却されること
def test_update_equipment_001_update_all_fields(client, make_user, make_equipment, login):
    make_user("admin01", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_equipment(asset_number="AST-001", name="編集前PC", category="ノートPC")
    token = login("admin01", "AdminPass1")

    response = client.put(
        "/equipment/AST-001",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "編集後PC",
            "category": "デスクトップPC",
            "description": "編集後の説明",
            "location": "別館倉庫",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "編集後PC"
    assert body["category"] == "デスクトップPC"
    assert body["description"] == "編集後の説明"
    assert body["location"] == "別館倉庫"


# ========== 結合テストNo.2 ==========
# description・locationを省略（null化）して編集した場合、description=null・location=nullとなること
def test_update_equipment_002_clear_optional_fields(client, make_user, make_equipment, login):
    make_user("admin02", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    equipment = make_equipment(description="編集前の説明", location="本社倉庫")
    token = login("admin02", "AdminPass1")

    response = client.put(
        f"/equipment/{equipment.asset_number}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "編集後PC2", "category": "デスクトップPC"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["description"] is None
    assert body["location"] is None


# ========== 結合テストNo.3 ==========
# 無効化済みの備品を編集した場合、HTTP 200で編集でき、is_active=falseが維持されること
def test_update_equipment_003_update_disabled_equipment(client, make_user, make_equipment, login):
    make_user("admin03", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    equipment = make_equipment(is_active=False)
    token = login("admin03", "AdminPass1")

    response = client.put(
        f"/equipment/{equipment.asset_number}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "編集後PC3", "category": "デスクトップPC"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "編集後PC3"
    assert body["is_active"] is False


# ========== 結合テストNo.4 ==========
# 存在しない資産番号を指定した場合、HTTP 404が返却されること
def test_update_equipment_004_not_found(client, make_user, login):
    make_user("admin04", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin04", "AdminPass1")

    response = client.put(
        "/equipment/未登録資産番号",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "編集後PC4", "category": "デスクトップPC"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "備品が見つかりません"


# ========== 結合テストNo.5 ==========
# 必須パラメータ（name）が欠落している場合、HTTP 422が返却されること
def test_update_equipment_005_missing_required_name(client, make_user, make_equipment, login):
    make_user("admin05", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    equipment = make_equipment()
    token = login("admin05", "AdminPass1")

    response = client.put(
        f"/equipment/{equipment.asset_number}",
        headers={"Authorization": f"Bearer {token}"},
        json={"category": "デスクトップPC"},
    )

    assert response.status_code == 422


# ========== 結合テストNo.6 ==========
# nameが上限（100文字）を超過している場合、HTTP 422が返却されること
def test_update_equipment_006_name_too_long(client, make_user, make_equipment, login):
    make_user("admin06", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    equipment = make_equipment()
    token = login("admin06", "AdminPass1")

    response = client.put(
        f"/equipment/{equipment.asset_number}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "a" * 101, "category": "デスクトップPC"},
    )

    assert response.status_code == 422


# ========== 結合テストNo.7 ==========
# categoryが上限（50文字）を超過している場合、HTTP 422が返却されること
def test_update_equipment_007_category_too_long(client, make_user, make_equipment, login):
    make_user("admin07", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    equipment = make_equipment()
    token = login("admin07", "AdminPass1")

    response = client.put(
        f"/equipment/{equipment.asset_number}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "編集後PC7", "category": "a" * 51},
    )

    assert response.status_code == 422


# ========== 結合テストNo.8 ==========
# descriptionが上限（500文字）を超過している場合、HTTP 422が返却されること
def test_update_equipment_008_description_too_long(client, make_user, make_equipment, login):
    make_user("admin08", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    equipment = make_equipment()
    token = login("admin08", "AdminPass1")

    response = client.put(
        f"/equipment/{equipment.asset_number}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "編集後PC8", "category": "デスクトップPC", "description": "a" * 501},
    )

    assert response.status_code == 422


# ========== 結合テストNo.9 ==========
# locationが上限（100文字）を超過している場合、HTTP 422が返却されること
def test_update_equipment_009_location_too_long(client, make_user, make_equipment, login):
    make_user("admin09", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    equipment = make_equipment()
    token = login("admin09", "AdminPass1")

    response = client.put(
        f"/equipment/{equipment.asset_number}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "編集後PC9", "category": "デスクトップPC", "location": "a" * 101},
    )

    assert response.status_code == 422


# ========== 結合テストNo.10 ==========
# 管理者権限でないユーザーが編集した場合、HTTP 403が返却されること
def test_update_equipment_010_forbidden_not_admin(client, make_user, make_equipment, login):
    make_user("u010", "一般ユーザー", "password1", role="general")
    equipment = make_equipment()
    token = login("u010", "password1")

    response = client.put(
        f"/equipment/{equipment.asset_number}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "編集後PC10", "category": "デスクトップPC"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.11 ==========
# 初回パスワード変更未完了の管理者が編集した場合、HTTP 403が返却されること
def test_update_equipment_011_forbidden_password_not_changed(client, make_user, make_equipment, login):
    make_user("admin11", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    equipment = make_equipment()
    token = login("admin11", "AdminPass1")

    response = client.put(
        f"/equipment/{equipment.asset_number}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "編集後PC11", "category": "デスクトップPC"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.12 ==========
# トークン未指定で編集した場合、HTTP 401が返却されること
def test_update_equipment_012_token_missing(client, make_equipment):
    equipment = make_equipment()

    response = client.put(f"/equipment/{equipment.asset_number}", json={"name": "編集後PC12", "category": "デスクトップPC"})

    assert response.status_code == 401


# ========== 結合テストNo.13 ==========
# asset_numberはリクエストボディに項目自体が存在せず編集対象外であり、編集後も変更されないこと
def test_update_equipment_013_asset_number_unchanged(client, make_user, make_equipment, login):
    make_user("admin13", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_equipment(asset_number="AST-013")
    token = login("admin13", "AdminPass1")

    response = client.put(
        "/equipment/AST-013",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "編集後PC13", "category": "デスクトップPC"},
    )

    assert response.status_code == 200
    assert response.json()["asset_number"] == "AST-013"
