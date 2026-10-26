from datetime import date, timedelta

# ==================================================
# 貸出処理
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：lend_loan_request_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/貸出・返却/貸出処理_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 承認済み・開始日が今日以前の申請を貸出処理した場合、HTTP 200で貸出内容が返却されること
def test_lend_loan_request_endpoint_001_lend_approved_request(client, make_user, make_loan_request, login):
    make_user("admin001", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant001", "申請者太郎", "password1")
    today = date.today()
    loan_request = make_loan_request(
        applicant.id, status="approved", start_date=today, due_date=today + timedelta(days=9)
    )
    token = login("admin001", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/lend",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == loan_request.id
    assert body["status"] == "lending"
    assert body["lent_at"] is not None
    assert body["applicant_name"] == "申請者太郎"
    assert body["start_date"] == today.isoformat()
    assert body["due_date"] == (today + timedelta(days=9)).isoformat()


# ========== 結合テストNo.2 ==========
# 存在しない内部IDを指定した場合、HTTP 404が返却されること
def test_lend_loan_request_endpoint_002_not_found(client, make_user, login):
    make_user("admin002", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin002", "AdminPass1")

    response = client.put(
        "/loan-requests/99999/lend",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "貸出申請が見つかりません"


# ========== 結合テストNo.3 ==========
# 承認済み以外（申請中）の申請を貸出処理しようとした場合、HTTP 400が返却されること
def test_lend_loan_request_endpoint_003_not_approved(client, make_user, make_loan_request, login):
    make_user("admin003", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant003", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="pending")
    token = login("admin003", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/lend",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "この申請は貸出処理できません"


# ========== 結合テストNo.4 ==========
# 開始日が未来の承認済み申請を貸出処理しようとした場合、HTTP 400が返却されること
def test_lend_loan_request_endpoint_004_start_date_in_future(client, make_user, make_loan_request, login):
    make_user("admin004", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant004", "申請者太郎", "password1")
    today = date.today()
    loan_request = make_loan_request(
        applicant.id,
        status="approved",
        start_date=today + timedelta(days=5),
        due_date=today + timedelta(days=14),
    )
    token = login("admin004", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/lend",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "開始日前は貸出処理できません"


# ========== 結合テストNo.5 ==========
# 対象備品が無効化されている承認済み申請を貸出処理しようとした場合、HTTP 400が返却されること
def test_lend_loan_request_endpoint_005_equipment_inactive(
    client, make_user, make_equipment, make_loan_request, login
):
    make_user("admin005", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant005", "申請者太郎", "password1")
    equipment = make_equipment(asset_number="AST-LD-005", is_active=False)
    today = date.today()
    loan_request = make_loan_request(
        applicant.id,
        status="approved",
        equipment_internal_id=equipment.id,
        start_date=today,
        due_date=today + timedelta(days=9),
    )
    token = login("admin005", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/lend",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "この備品は無効化されているため貸出処理できません"


# ========== 結合テストNo.6 ==========
# 同一備品が既に貸出中の承認済み申請を貸出処理しようとした場合、HTTP 400が返却されること
def test_lend_loan_request_endpoint_006_equipment_already_lending(
    client, make_user, make_equipment, make_loan_request, login
):
    make_user("admin006", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant_a = make_user("applicantA006", "申請者A", "password1")
    applicant_b = make_user("applicantB006", "申請者B", "password1")
    equipment = make_equipment(asset_number="AST-LD-006")
    today = date.today()
    make_loan_request(
        applicant_a.id,
        status="lending",
        equipment_internal_id=equipment.id,
        start_date=today - timedelta(days=1),
        due_date=today + timedelta(days=8),
    )
    approved_request = make_loan_request(
        applicant_b.id,
        status="approved",
        equipment_internal_id=equipment.id,
        start_date=today,
        due_date=today + timedelta(days=9),
    )
    token = login("admin006", "AdminPass1")

    response = client.put(
        f"/loan-requests/{approved_request.id}/lend",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "この備品は貸出中のため貸出処理できません"


# ========== 結合テストNo.7 ==========
# 管理者権限でないユーザーが貸出処理する場合、HTTP 403が返却されること
def test_lend_loan_request_endpoint_007_forbidden_not_admin(client, make_user, make_loan_request, login):
    make_user("u007", "一般ユーザー", "password1")
    applicant = make_user("applicant007", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="approved")
    token = login("u007", "password1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/lend",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.8 ==========
# 初回パスワード変更未完了の管理者が貸出処理する場合、HTTP 403が返却されること
def test_lend_loan_request_endpoint_008_forbidden_password_not_changed(
    client, make_user, make_loan_request, login
):
    make_user("admin008", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    applicant = make_user("applicant008", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="approved")
    token = login("admin008", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/lend",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.9 ==========
# トークン未指定で貸出処理する場合、HTTP 401が返却されること
def test_lend_loan_request_endpoint_009_token_missing(client, make_user, make_loan_request):
    applicant = make_user("applicant009", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="approved")

    response = client.put(f"/loan-requests/{loan_request.id}/lend")

    assert response.status_code == 401
