# ==================================================
# 備品詳細取得
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：get_equipment_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/備品管理/備品詳細取得_結合テスト仕様書.md
# ==================================================

from datetime import date


# ========== 結合テストNo.1 ==========
# 一般ユーザーが貸出中でない有効な備品を取得する場合、全フィールドを取得できること
def test_get_equipment_endpoint_001_general_active_available(client, make_user, make_equipment, login):
    make_equipment(
        asset_number="AST-2001",
        name="対象備品",
        category="ノートPC",
        description="説明文",
        location="本社倉庫",
        is_active=True,
    )
    make_user("u001", "一般ユーザー", "password1", role="general")
    token = login("u001", "password1")

    response = client.get("/equipment/AST-2001", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["asset_number"] == "AST-2001"
    assert body["name"] == "対象備品"
    assert body["category"] == "ノートPC"
    assert body["description"] == "説明文"
    assert body["location"] == "本社倉庫"
    assert body["is_active"] is True
    assert body["lending_status"] == "available"
    assert body["due_date"] is None


# ========== 結合テストNo.2 ==========
# 対象備品が貸出中の場合、lending_status=lending・due_dateが貸出中申請の返却予定日と一致すること
def test_get_equipment_endpoint_002_lending_status_lending(client, make_user, make_equipment, make_loan_request, login):
    equipment = make_equipment(asset_number="AST-2002")
    applicant = make_user("u002", "申請者", "password1", role="general")
    make_loan_request(
        applicant.id,
        status="lending",
        equipment_internal_id=equipment.id,
        due_date=date(2026, 12, 15),
    )
    token = login("u002", "password1")

    response = client.get("/equipment/AST-2002", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body["lending_status"] == "lending"
    assert body["due_date"] == "2026-12-15"


# ========== 結合テストNo.3 ==========
# 管理者が無効化済みの備品を取得する場合、取得できること
def test_get_equipment_endpoint_003_admin_can_get_inactive(client, make_user, make_equipment, login):
    make_equipment(asset_number="AST-2003", is_active=False)
    make_user("admin03", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin03", "AdminPass1")

    response = client.get("/equipment/AST-2003", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["is_active"] is False


# ========== 結合テストNo.4 ==========
# 存在しない資産番号を指定した場合、HTTP 404が返却されること
def test_get_equipment_endpoint_004_not_found(client, make_user, login):
    make_user("admin04", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin04", "AdminPass1")

    response = client.get("/equipment/AST-UNKNOWN", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404
    assert response.json()["detail"] == "備品が見つかりません"


# ========== 結合テストNo.5 ==========
# 一般ユーザーが無効化済みの備品を取得しようとした場合、存在しない場合と同一のHTTP 404が返却されること
def test_get_equipment_endpoint_005_general_inactive_not_found(client, make_user, make_equipment, login):
    make_equipment(asset_number="AST-2005", is_active=False)
    make_user("u005", "一般ユーザー", "password1", role="general")
    token = login("u005", "password1")

    response = client.get("/equipment/AST-2005", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404
    assert response.json()["detail"] == "備品が見つかりません"


# ========== 結合テストNo.6 ==========
# equipment_idが上限（32文字）を超過している場合、HTTP 422が返却されること
def test_get_equipment_endpoint_006_equipment_id_too_long(client, make_user, login):
    make_user("admin06", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin06", "AdminPass1")

    response = client.get("/equipment/" + "a" * 33, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 422


# ========== 結合テストNo.7 ==========
# 初回パスワード変更未完了のユーザーがアクセスした場合、HTTP 403が返却されること
def test_get_equipment_endpoint_007_forbidden_password_not_changed(client, make_user, login):
    make_user("u007", "未変更ユーザー", "password1", role="general", must_change_password=True)
    token = login("u007", "password1")

    response = client.get("/equipment/AST-ANY", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.8 ==========
# トークン未指定でアクセスした場合、HTTP 401が返却されること
def test_get_equipment_endpoint_008_token_missing(client):
    response = client.get("/equipment/AST-ANY")

    assert response.status_code == 401
