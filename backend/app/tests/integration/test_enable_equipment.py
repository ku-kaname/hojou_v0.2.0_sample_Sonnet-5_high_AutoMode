# ==================================================
# 備品再有効化
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：enable_equipment_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/備品管理/備品再有効化_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 無効化済みの備品を再有効化した場合、HTTP 200・is_active=trueとなること
def test_enable_equipment_001_enable_disabled_equipment(client, make_user, make_equipment, login):
    make_user("admin01", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    equipment = make_equipment(is_active=False)
    token = login("admin01", "AdminPass1")

    response = client.put(f"/equipment/{equipment.asset_number}/enable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["is_active"] is True


# ========== 結合テストNo.2 ==========
# 再有効化後も、無効化前のname等の他項目が変更されないこと
def test_enable_equipment_002_other_fields_unchanged(client, make_user, make_equipment, login):
    make_user("admin02", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    equipment = make_equipment(name="テストPC", category="ノートPC", is_active=False)
    token = login("admin02", "AdminPass1")

    response = client.put(f"/equipment/{equipment.asset_number}/enable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "テストPC"
    assert body["category"] == "ノートPC"


# ========== 結合テストNo.3 ==========
# 既に有効化済みの備品を再有効化した場合、HTTP 400が返却されること
def test_enable_equipment_003_already_enabled(client, make_user, make_equipment, login):
    make_user("admin03", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    equipment = make_equipment()
    token = login("admin03", "AdminPass1")

    response = client.put(f"/equipment/{equipment.asset_number}/enable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 400
    assert response.json()["detail"] == "既に有効化されています"


# ========== 結合テストNo.4 ==========
# 存在しない資産番号を指定した場合、HTTP 404が返却されること
def test_enable_equipment_004_not_found(client, make_user, login):
    make_user("admin04", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin04", "AdminPass1")

    response = client.put("/equipment/未登録資産番号/enable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404
    assert response.json()["detail"] == "備品が見つかりません"


# ========== 結合テストNo.5 ==========
# 管理者権限でないユーザーが再有効化した場合、HTTP 403が返却されること
def test_enable_equipment_005_forbidden_not_admin(client, make_user, make_equipment, login):
    make_user("u005", "一般ユーザー", "password1", role="general")
    equipment = make_equipment(is_active=False)
    token = login("u005", "password1")

    response = client.put(f"/equipment/{equipment.asset_number}/enable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.6 ==========
# 初回パスワード変更未完了の管理者が再有効化した場合、HTTP 403が返却されること
def test_enable_equipment_006_forbidden_password_not_changed(client, make_user, make_equipment, login):
    make_user("admin06", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    equipment = make_equipment(is_active=False)
    token = login("admin06", "AdminPass1")

    response = client.put(f"/equipment/{equipment.asset_number}/enable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.7 ==========
# トークン未指定で再有効化した場合、HTTP 401が返却されること
def test_enable_equipment_007_token_missing(client, make_equipment):
    equipment = make_equipment(is_active=False)

    response = client.put(f"/equipment/{equipment.asset_number}/enable")

    assert response.status_code == 401
