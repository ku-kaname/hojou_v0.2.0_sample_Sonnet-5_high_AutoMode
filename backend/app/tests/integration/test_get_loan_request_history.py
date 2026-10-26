from datetime import date, timedelta

# ==================================================
# 貸出履歴検索・取得
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：get_loan_request_history_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/履歴・状況確認/貸出履歴検索・取得_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 検索条件なしで全件が開始日の降順で返却されること
def test_get_loan_request_history_endpoint_001_no_filter_sorted_desc(
    client, make_user, make_equipment, make_loan_request, login
):
    make_user("admin001", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant001", "申請者太郎", "password1")
    equipment = make_equipment(asset_number="AST-HI-001")

    loan_request_old = make_loan_request(
        applicant.id,
        status="pending",
        equipment_internal_id=equipment.id,
        start_date=date(2026, 11, 1),
        due_date=date(2026, 11, 10),
    )
    loan_request_new = make_loan_request(
        applicant.id,
        status="pending",
        equipment_internal_id=equipment.id,
        start_date=date(2026, 11, 5),
        due_date=date(2026, 11, 14),
    )

    token = login("admin001", "AdminPass1")

    response = client.get("/loan-requests/all", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["id"] == loan_request_new.id
    assert body[1]["id"] == loan_request_old.id


# ========== 結合テストNo.2 ==========
# 開始日範囲（start_date_from・start_date_to）で絞り込まれること
def test_get_loan_request_history_endpoint_002_start_date_range(client, make_user, make_loan_request, login):
    make_user("admin002", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant002", "申請者太郎", "password1")

    make_loan_request(applicant.id, status="pending", start_date=date(2026, 11, 1), due_date=date(2026, 11, 10))
    in_range_request = make_loan_request(
        applicant.id, status="pending", start_date=date(2026, 11, 5), due_date=date(2026, 11, 14)
    )
    make_loan_request(applicant.id, status="pending", start_date=date(2026, 11, 20), due_date=date(2026, 11, 29))

    token = login("admin002", "AdminPass1")

    response = client.get(
        "/loan-requests/all",
        params={"start_date_from": "2026-11-03", "start_date_to": "2026-11-10"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == in_range_request.id


# ========== 結合テストNo.3 ==========
# 資産番号（asset_number）で完全一致絞り込まれること
def test_get_loan_request_history_endpoint_003_asset_number_filter(
    client, make_user, make_equipment, make_loan_request, login
):
    make_user("admin003", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant003", "申請者太郎", "password1")

    equipment_target = make_equipment(asset_number="AST-HI-003A")
    target_request = make_loan_request(applicant.id, status="pending", equipment_internal_id=equipment_target.id)
    equipment_other = make_equipment(asset_number="AST-HI-003B")
    make_loan_request(applicant.id, status="pending", equipment_internal_id=equipment_other.id)

    token = login("admin003", "AdminPass1")

    response = client.get(
        "/loan-requests/all",
        params={"asset_number": "AST-HI-003A"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == target_request.id


# ========== 結合テストNo.4 ==========
# 借用者ユーザーID（user_id）で完全一致絞り込まれること
def test_get_loan_request_history_endpoint_004_user_id_filter(client, make_user, make_loan_request, login):
    make_user("admin004", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant_a = make_user("applicant_a004", "申請者A", "password1")
    applicant_b = make_user("applicant_b004", "申請者B", "password1")
    target_request = make_loan_request(applicant_a.id, status="pending")
    make_loan_request(applicant_b.id, status="pending")

    token = login("admin004", "AdminPass1")

    response = client.get(
        "/loan-requests/all",
        params={"user_id": "applicant_a004"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == target_request.id


# ========== 結合テストNo.5 ==========
# 対象がない場合、空リストが返却されること
def test_get_loan_request_history_endpoint_005_empty_list(client, make_user, login):
    make_user("admin005", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin005", "AdminPass1")

    response = client.get("/loan-requests/all", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == []


# ========== 結合テストNo.6 ==========
# 承認・却下者・貸出処理者・返却処理者の氏名が正しく返却されること
def test_get_loan_request_history_endpoint_006_processor_names(client, make_user, make_loan_request, login):
    make_user("admin006", "処理担当管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant006", "申請者太郎", "password1")
    today = date.today()
    loan_request = make_loan_request(
        applicant.id, status="pending", start_date=today, due_date=today + timedelta(days=9)
    )
    token = login("admin006", "AdminPass1")
    headers = {"Authorization": f"Bearer {token}"}

    client.put(f"/loan-requests/{loan_request.id}/approve", headers=headers)
    client.put(f"/loan-requests/{loan_request.id}/lend", headers=headers)
    client.put(f"/loan-requests/{loan_request.id}/return", headers=headers, json={})

    response = client.get("/loan-requests/all", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["status"] == "returned"
    assert body[0]["approved_by_name"] == "処理担当管理者"
    assert body[0]["lent_by_name"] == "処理担当管理者"
    assert body[0]["returned_by_name"] == "処理担当管理者"


# ========== 結合テストNo.7 ==========
# 管理者権限でないユーザーが取得した場合、HTTP 403が返却されること
def test_get_loan_request_history_endpoint_007_forbidden_not_admin(client, make_user, login):
    make_user("u007", "一般ユーザー", "password1")
    token = login("u007", "password1")

    response = client.get("/loan-requests/all", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.8 ==========
# 初回パスワード変更未完了の管理者が取得した場合、HTTP 403が返却されること
def test_get_loan_request_history_endpoint_008_forbidden_password_not_changed(client, make_user, login):
    make_user("admin008", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    token = login("admin008", "AdminPass1")

    response = client.get("/loan-requests/all", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.9 ==========
# トークン未指定で取得した場合、HTTP 401が返却されること
def test_get_loan_request_history_endpoint_009_token_missing(client):
    response = client.get("/loan-requests/all")

    assert response.status_code == 401


# ========== 結合テストNo.10 ==========
# 資産番号（asset_number）が33文字（上限超過）の場合、HTTP 422が返却されること
def test_get_loan_request_history_endpoint_010_asset_number_too_long(client, make_user, login):
    make_user("admin010", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin010", "AdminPass1")

    response = client.get(
        "/loan-requests/all",
        params={"asset_number": "A" * 33},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


# ========== 結合テストNo.11 ==========
# 借用者ユーザーID（user_id）が33文字（上限超過）の場合、HTTP 422が返却されること
def test_get_loan_request_history_endpoint_011_user_id_too_long(client, make_user, login):
    make_user("admin011", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin011", "AdminPass1")

    response = client.get(
        "/loan-requests/all",
        params={"user_id": "a" * 33},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


# ========== 結合テストNo.12 ==========
# 開始日（start_date_from）に日付形式でない文字列を指定した場合、HTTP 422が返却されること
def test_get_loan_request_history_endpoint_012_start_date_from_invalid_format(client, make_user, login):
    make_user("admin012", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin012", "AdminPass1")

    response = client.get(
        "/loan-requests/all",
        params={"start_date_from": "not-a-date"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
