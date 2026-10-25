# ==================================================
# 備品検索・一覧取得
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：search_equipment_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/備品管理/備品検索・一覧取得_結合テスト仕様書.md
# ==================================================

from datetime import date


# ========== 結合テストNo.1 ==========
# 一般ユーザーが条件なしで取得する場合、有効な備品のみ資産番号昇順で返却されること
def test_search_equipment_endpoint_001_general_only_active(client, make_user, make_equipment, login):
    make_equipment(asset_number="AST-0001", name="対象備品1", category="ノートPC", is_active=True)
    make_equipment(asset_number="AST-0002", name="対象備品2", category="ノートPC", is_active=True)
    make_equipment(asset_number="AST-0003", name="無効化済み備品", category="ノートPC", is_active=False)
    make_user("u001", "一般ユーザー", "password1", role="general")
    token = login("u001", "password1")

    response = client.get("/equipment", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    # 無効化済みの備品（AST-0003）は含まれないこと
    assert [item["asset_number"] for item in body] == ["AST-0001", "AST-0002"]
    target = body[0]
    assert target["name"] == "対象備品1"
    assert target["category"] == "ノートPC"
    assert target["description"] is None
    assert target["location"] is None
    assert target["is_active"] is True
    assert target["lending_status"] == "available"
    assert target["due_date"] is None


# ========== 結合テストNo.2 ==========
# 管理者が条件なしで取得する場合、有効・無効化済み両方の備品が返却されること
def test_search_equipment_endpoint_002_admin_includes_inactive(client, make_user, make_equipment, login):
    make_equipment(asset_number="AST-0101", is_active=True)
    make_equipment(asset_number="AST-0102", is_active=False)
    make_user("admin01", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin01", "AdminPass1")

    response = client.get("/equipment", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    asset_numbers = [item["asset_number"] for item in body]
    assert "AST-0101" in asset_numbers
    assert "AST-0102" in asset_numbers
    active_item = next(item for item in body if item["asset_number"] == "AST-0101")
    inactive_item = next(item for item in body if item["asset_number"] == "AST-0102")
    assert active_item["is_active"] is True
    assert inactive_item["is_active"] is False


# ========== 結合テストNo.3 ==========
# 管理者がis_active=falseを指定した場合、無効化済みの備品のみ返却されること
def test_search_equipment_endpoint_003_admin_filter_inactive(client, make_user, make_equipment, login):
    make_equipment(asset_number="AST-0201", is_active=True)
    make_equipment(asset_number="AST-0202", is_active=False)
    make_user("admin02", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin02", "AdminPass1")

    response = client.get(
        "/equipment", params={"is_active": "false"}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["asset_number"] for item in body] == ["AST-0202"]


# ========== 結合テストNo.4 ==========
# 管理者がis_active=trueを指定した場合、有効な備品のみ返却されること
def test_search_equipment_endpoint_004_admin_filter_active(client, make_user, make_equipment, login):
    make_equipment(asset_number="AST-0301", is_active=True)
    make_equipment(asset_number="AST-0302", is_active=False)
    make_user("admin03", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin03", "AdminPass1")

    response = client.get(
        "/equipment", params={"is_active": "true"}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["asset_number"] for item in body] == ["AST-0301"]


# ========== 結合テストNo.5 ==========
# categoryを指定した場合、完全一致する分類の備品のみ返却されること
def test_search_equipment_endpoint_005_category_exact_match(client, make_user, make_equipment, login):
    make_equipment(asset_number="AST-0401", category="ノートPC")
    make_equipment(asset_number="AST-0402", category="モニター")
    make_user("admin04", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin04", "AdminPass1")

    response = client.get(
        "/equipment", params={"category": "ノートPC"}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["asset_number"] for item in body] == ["AST-0401"]


# ========== 結合テストNo.6 ==========
# keywordを指定した場合、備品名に部分一致する備品のみ返却されること
def test_search_equipment_endpoint_006_keyword_matches_name(client, make_user, make_equipment, login):
    make_equipment(asset_number="AST-0501", name="ノートPC（A）")
    make_equipment(asset_number="AST-0502", name="モニター")
    make_user("admin05", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin05", "AdminPass1")

    response = client.get(
        "/equipment", params={"keyword": "ノートPC"}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["asset_number"] for item in body] == ["AST-0501"]


# ========== 結合テストNo.7 ==========
# keywordを指定した場合、説明に部分一致する備品のみ返却されること
def test_search_equipment_endpoint_007_keyword_matches_description(client, make_user, make_equipment, login):
    make_equipment(asset_number="AST-0601", name="対象機器", description="在庫入替対象")
    make_equipment(asset_number="AST-0602", name="別候補機器", description="特になし")
    make_user("admin06", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin06", "AdminPass1")

    response = client.get(
        "/equipment", params={"keyword": "在庫入替"}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["asset_number"] for item in body] == ["AST-0601"]


# ========== 結合テストNo.8 ==========
# 対象備品が貸出中の場合、lending_status=lending・due_dateが貸出中申請の返却予定日と一致すること
def test_search_equipment_endpoint_008_lending_status_lending(client, make_user, make_equipment, make_loan_request, login):
    equipment = make_equipment(asset_number="AST-0701")
    applicant = make_user("u008", "申請者", "password1", role="general")
    make_loan_request(
        applicant.id,
        status="lending",
        equipment_internal_id=equipment.id,
        due_date=date(2026, 12, 1),
    )
    make_user("admin07", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin07", "AdminPass1")

    response = client.get("/equipment", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    target = next(item for item in body if item["asset_number"] == "AST-0701")
    assert target["lending_status"] == "lending"
    assert target["due_date"] == "2026-12-01"


# ========== 結合テストNo.9 ==========
# 対象備品が貸出中でない場合、lending_status=available・due_date=nullとなること
def test_search_equipment_endpoint_009_lending_status_available(client, make_user, make_equipment, login):
    make_equipment(asset_number="AST-0801")
    make_user("admin08", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin08", "AdminPass1")

    response = client.get("/equipment", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    target = next(item for item in body if item["asset_number"] == "AST-0801")
    assert target["lending_status"] == "available"
    assert target["due_date"] is None


# ========== 結合テストNo.10 ==========
# 一般ユーザーがis_active=falseを指定しても無視され、有効な備品のみ返却されること
def test_search_equipment_endpoint_010_general_ignores_is_active(client, make_user, make_equipment, login):
    make_equipment(asset_number="AST-0901", is_active=True)
    make_equipment(asset_number="AST-0902", is_active=False)
    make_user("u010", "一般ユーザー", "password1", role="general")
    token = login("u010", "password1")

    response = client.get(
        "/equipment", params={"is_active": "false"}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    body = response.json()
    assert [item["asset_number"] for item in body] == ["AST-0901"]


# ========== 結合テストNo.11 ==========
# categoryに空文字を指定した場合、バリデーションエラーにならず該当がないため空リストが返却されること
def test_search_equipment_endpoint_011_category_empty_string(client, make_user, make_equipment, login):
    make_equipment(asset_number="AST-1001", category="結合テスト")
    make_user("admin11", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin11", "AdminPass1")

    response = client.get("/equipment", params={"category": ""}, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == []


# ========== 結合テストNo.12 ==========
# categoryが上限（50文字）を超過している場合、HTTP 422が返却されること
def test_search_equipment_endpoint_012_category_too_long(client, make_user, login):
    make_user("admin12", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin12", "AdminPass1")

    response = client.get(
        "/equipment", params={"category": "a" * 51}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 422


# ========== 結合テストNo.13 ==========
# keywordが上限（100文字）を超過している場合、HTTP 422が返却されること
def test_search_equipment_endpoint_013_keyword_too_long(client, make_user, login):
    make_user("admin13", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin13", "AdminPass1")

    response = client.get(
        "/equipment", params={"keyword": "a" * 101}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 422


# ========== 結合テストNo.14 ==========
# is_activeに真偽値へ変換できない値を指定している場合、HTTP 422が返却されること
def test_search_equipment_endpoint_014_is_active_type_mismatch(client, make_user, login):
    make_user("admin14", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin14", "AdminPass1")

    response = client.get(
        "/equipment", params={"is_active": "abc"}, headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 422


# ========== 結合テストNo.15 ==========
# 初回パスワード変更未完了のユーザーがアクセスした場合、HTTP 403が返却されること
def test_search_equipment_endpoint_015_forbidden_password_not_changed(client, make_user, login):
    make_user("u015", "未変更ユーザー", "password1", role="general", must_change_password=True)
    token = login("u015", "password1")

    response = client.get("/equipment", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.16 ==========
# トークン未指定でアクセスした場合、HTTP 401が返却されること
def test_search_equipment_endpoint_016_token_missing(client):
    response = client.get("/equipment")

    assert response.status_code == 401
