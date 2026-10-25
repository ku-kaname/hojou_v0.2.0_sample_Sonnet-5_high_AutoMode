# ==================================================
# 備品予約状況取得
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：get_equipment_reservations_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/備品管理/備品予約状況取得_結合テスト仕様書.md
# ==================================================

from datetime import date


# ========== 結合テストNo.1 ==========
# 状態が「承認済み」「貸出中」の申請が開始日昇順で返却され、他の状態（申請中）の申請は対象外となること
def test_get_equipment_reservations_endpoint_001_ordered_excludes_other_status(
    client, make_user, make_equipment, make_loan_request, login
):
    equipment = make_equipment(asset_number="AST-3001")
    applicant = make_user("u001", "申請者", "password1", role="general")
    # 開始日が後の「貸出中」申請
    make_loan_request(
        applicant.id,
        status="lending",
        equipment_internal_id=equipment.id,
        start_date=date(2026, 11, 10),
        due_date=date(2026, 11, 20),
    )
    # 開始日が先の「承認済み」申請
    make_loan_request(
        applicant.id,
        status="approved",
        equipment_internal_id=equipment.id,
        start_date=date(2026, 11, 1),
        due_date=date(2026, 11, 9),
    )
    # 対象外（申請中）の申請
    make_loan_request(
        applicant.id,
        status="pending",
        equipment_internal_id=equipment.id,
        start_date=date(2026, 10, 20),
        due_date=date(2026, 10, 25),
    )
    make_user("admin01", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin01", "AdminPass1")

    response = client.get("/equipment/AST-3001/reservations", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["start_date"] == "2026-11-01"
    assert body[0]["due_date"] == "2026-11-09"
    assert body[0]["status"] == "approved"
    assert body[1]["start_date"] == "2026-11-10"
    assert body[1]["due_date"] == "2026-11-20"
    assert body[1]["status"] == "lending"


# ========== 結合テストNo.2 ==========
# 管理者が取得する場合、borrower_nameに申請者氏名が設定されること
def test_get_equipment_reservations_endpoint_002_admin_borrower_name_set(
    client, make_user, make_equipment, make_loan_request, login
):
    equipment = make_equipment(asset_number="AST-3002")
    applicant = make_user("u002", "予約申請者", "password1", role="general")
    make_loan_request(applicant.id, status="approved", equipment_internal_id=equipment.id)
    make_user("admin02", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin02", "AdminPass1")

    response = client.get("/equipment/AST-3002/reservations", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body[0]["borrower_name"] == "予約申請者"


# ========== 結合テストNo.3 ==========
# 一般ユーザーが取得する場合、borrower_nameがnullとなること
def test_get_equipment_reservations_endpoint_003_general_borrower_name_null(
    client, make_user, make_equipment, make_loan_request, login
):
    equipment = make_equipment(asset_number="AST-3003")
    applicant = make_user("u003", "予約申請者", "password1", role="general")
    make_loan_request(applicant.id, status="approved", equipment_internal_id=equipment.id)
    token = login("u003", "password1")

    response = client.get("/equipment/AST-3003/reservations", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert body[0]["borrower_name"] is None


# ========== 結合テストNo.4 ==========
# 対象の申請が存在しない場合、空リストが返却されること
def test_get_equipment_reservations_endpoint_004_empty_when_no_requests(client, make_user, make_equipment, login):
    make_equipment(asset_number="AST-3004")
    make_user("admin04", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin04", "AdminPass1")

    response = client.get("/equipment/AST-3004/reservations", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == []


# ========== 結合テストNo.5 ==========
# 存在しない資産番号を指定した場合、HTTP 404が返却されること
def test_get_equipment_reservations_endpoint_005_not_found(client, make_user, login):
    make_user("admin05", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin05", "AdminPass1")

    response = client.get("/equipment/AST-UNKNOWN/reservations", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404
    assert response.json()["detail"] == "備品が見つかりません"


# ========== 結合テストNo.6 ==========
# 一般ユーザーが無効化済みの備品の予約状況を取得しようとした場合、存在しない場合と同一のHTTP 404が返却されること
def test_get_equipment_reservations_endpoint_006_general_inactive_not_found(
    client, make_user, make_equipment, login
):
    make_equipment(asset_number="AST-3006", is_active=False)
    make_user("u006", "一般ユーザー", "password1", role="general")
    token = login("u006", "password1")

    response = client.get("/equipment/AST-3006/reservations", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404
    assert response.json()["detail"] == "備品が見つかりません"


# ========== 結合テストNo.7 ==========
# equipment_idが上限（32文字）を超過している場合、HTTP 422が返却されること
def test_get_equipment_reservations_endpoint_007_equipment_id_too_long(client, make_user, login):
    make_user("admin07", "テスト管理者", "AdminPass1", role="admin")
    token = login("admin07", "AdminPass1")

    response = client.get(
        "/equipment/" + "a" * 33 + "/reservations", headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 422


# ========== 結合テストNo.8 ==========
# 初回パスワード変更未完了のユーザーがアクセスした場合、HTTP 403が返却されること
def test_get_equipment_reservations_endpoint_008_forbidden_password_not_changed(client, make_user, login):
    make_user("u008", "未変更ユーザー", "password1", role="general", must_change_password=True)
    token = login("u008", "password1")

    response = client.get("/equipment/AST-ANY/reservations", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.9 ==========
# トークン未指定でアクセスした場合、HTTP 401が返却されること
def test_get_equipment_reservations_endpoint_009_token_missing(client):
    response = client.get("/equipment/AST-ANY/reservations")

    assert response.status_code == 401
