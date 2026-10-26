from datetime import date

# ==================================================
# 貸出申請
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：create_loan_request_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/貸出申請・承認/貸出申請_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 有効な備品・重複のない期間で申請した場合、HTTP 200で登録内容が返却されること
def test_create_loan_request_endpoint_001_register_valid_request(client, make_user, make_equipment, login):
    make_user("u001", "一般ユーザー", "password1", must_change_password=False)
    equipment = make_equipment(name="テストPC", asset_number="AST-LR-001")
    token = login("u001", "password1")

    response = client.post(
        "/loan-requests",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_number": "AST-LR-001",
            "start_date": "2026-11-01",
            "due_date": "2026-11-10",
            "purpose": "テスト用途",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["asset_number"] == "AST-LR-001"
    assert body["equipment_name"] == equipment.name
    assert body["applicant_name"] == "一般ユーザー"
    assert body["start_date"] == "2026-11-01"
    assert body["due_date"] == "2026-11-10"
    assert body["purpose"] == "テスト用途"
    assert body["status"] == "pending"
    assert body["rejection_reason"] is None
    assert body["decided_at"] is None
    assert body["cancelled_at"] is None


# ========== 結合テストNo.2 ==========
# 返却予定日が開始日より前の日付を指定した場合、HTTP 400が返却されること
def test_create_loan_request_endpoint_002_due_date_before_start_date(client, make_user, make_equipment, login):
    make_user("u002", "一般ユーザー", "password1")
    make_equipment(asset_number="AST-LR-002")
    token = login("u002", "password1")

    response = client.post(
        "/loan-requests",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_number": "AST-LR-002",
            "start_date": "2026-11-10",
            "due_date": "2026-11-01",
            "purpose": "テスト用途",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "返却予定日は開始日以降の日付を指定してください"


# ========== 結合テストNo.3 ==========
# 存在しない資産番号を指定した場合、HTTP 404が返却されること
def test_create_loan_request_endpoint_003_equipment_not_found(client, make_user, login):
    make_user("u003", "一般ユーザー", "password1")
    token = login("u003", "password1")

    response = client.post(
        "/loan-requests",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_number": "AST-NOT-EXIST",
            "start_date": "2026-11-01",
            "due_date": "2026-11-10",
            "purpose": "テスト用途",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "備品が見つかりません"


# ========== 結合テストNo.4 ==========
# 無効化済みの備品の資産番号を指定した場合、存在しない場合と同一のHTTP 404が返却されること
def test_create_loan_request_endpoint_004_equipment_disabled(client, make_user, make_equipment, login):
    make_user("u004", "一般ユーザー", "password1")
    make_equipment(asset_number="AST-LR-004", is_active=False)
    token = login("u004", "password1")

    response = client.post(
        "/loan-requests",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_number": "AST-LR-004",
            "start_date": "2026-11-01",
            "due_date": "2026-11-10",
            "purpose": "テスト用途",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "備品が見つかりません"


# ========== 結合テストNo.5 ==========
# 指定期間が既存の承認済み申請（同一備品）と重複する場合、HTTP 400が返却されること
def test_create_loan_request_endpoint_005_overlaps_approved_request(
    client, make_user, make_equipment, make_loan_request, login
):
    applicant = make_user("other005", "既存申請者", "password1")
    make_user("u005", "一般ユーザー", "password1")
    equipment = make_equipment(asset_number="AST-LR-005")
    make_loan_request(
        applicant.id,
        status="approved",
        equipment_internal_id=equipment.id,
        start_date=date(2026, 11, 1),
        due_date=date(2026, 11, 10),
    )
    token = login("u005", "password1")

    response = client.post(
        "/loan-requests",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_number": "AST-LR-005",
            "start_date": "2026-11-05",
            "due_date": "2026-11-15",
            "purpose": "テスト用途",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "指定した期間は既に貸出予定があります"


# ========== 結合テストNo.6 ==========
# 指定期間が既存の貸出中申請（同一備品）と重複する場合、HTTP 400が返却されること
def test_create_loan_request_endpoint_006_overlaps_lending_request(
    client, make_user, make_equipment, make_loan_request, login
):
    applicant = make_user("other006", "既存申請者", "password1")
    make_user("u006", "一般ユーザー", "password1")
    equipment = make_equipment(asset_number="AST-LR-006")
    make_loan_request(
        applicant.id,
        status="lending",
        equipment_internal_id=equipment.id,
        start_date=date(2026, 11, 1),
        due_date=date(2026, 11, 10),
    )
    token = login("u006", "password1")

    response = client.post(
        "/loan-requests",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_number": "AST-LR-006",
            "start_date": "2026-11-05",
            "due_date": "2026-11-15",
            "purpose": "テスト用途",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "指定した期間は既に貸出予定があります"


# ========== 結合テストNo.7 ==========
# 必須パラメータ（asset_number）が欠落している場合、HTTP 422が返却されること
def test_create_loan_request_endpoint_007_missing_required_asset_number(client, make_user, login):
    make_user("u007", "一般ユーザー", "password1")
    token = login("u007", "password1")

    response = client.post(
        "/loan-requests",
        headers={"Authorization": f"Bearer {token}"},
        json={"start_date": "2026-11-01", "due_date": "2026-11-10", "purpose": "テスト用途"},
    )

    assert response.status_code == 422


# ========== 結合テストNo.8 ==========
# asset_numberが上限（32文字）を超過している場合、HTTP 422が返却されること
def test_create_loan_request_endpoint_008_asset_number_too_long(client, make_user, login):
    make_user("u008", "一般ユーザー", "password1")
    token = login("u008", "password1")

    response = client.post(
        "/loan-requests",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_number": "A" * 33,
            "start_date": "2026-11-01",
            "due_date": "2026-11-10",
            "purpose": "テスト用途",
        },
    )

    assert response.status_code == 422


# ========== 結合テストNo.9 ==========
# purposeが上限（200文字）を超過している場合、HTTP 422が返却されること
def test_create_loan_request_endpoint_009_purpose_too_long(client, make_user, make_equipment, login):
    make_user("u009", "一般ユーザー", "password1")
    make_equipment(asset_number="AST-LR-009")
    token = login("u009", "password1")

    response = client.post(
        "/loan-requests",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_number": "AST-LR-009",
            "start_date": "2026-11-01",
            "due_date": "2026-11-10",
            "purpose": "a" * 201,
        },
    )

    assert response.status_code == 422


# ========== 結合テストNo.10 ==========
# 初回パスワード変更未完了のユーザーが申請した場合、HTTP 403が返却されること
def test_create_loan_request_endpoint_010_forbidden_password_not_changed(client, make_user, make_equipment, login):
    make_user("u010", "一般ユーザー", "password1", must_change_password=True)
    make_equipment(asset_number="AST-LR-010")
    token = login("u010", "password1")

    response = client.post(
        "/loan-requests",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "asset_number": "AST-LR-010",
            "start_date": "2026-11-01",
            "due_date": "2026-11-10",
            "purpose": "テスト用途",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.11 ==========
# トークン未指定で申請した場合、HTTP 401が返却されること
def test_create_loan_request_endpoint_011_token_missing(client, make_equipment):
    make_equipment(asset_number="AST-LR-011")

    response = client.post(
        "/loan-requests",
        json={
            "asset_number": "AST-LR-011",
            "start_date": "2026-11-01",
            "due_date": "2026-11-10",
            "purpose": "テスト用途",
        },
    )

    assert response.status_code == 401
