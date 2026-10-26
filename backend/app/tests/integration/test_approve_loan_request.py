from datetime import date

from app import crud

# ==================================================
# 申請承認
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：approve_loan_request_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/貸出申請・承認/申請承認_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 開始日が未来の申請中の申請を承認した場合、HTTP 200で承認内容が返却され、申請者宛に通知が1件登録されること
def test_approve_loan_request_endpoint_001_approve_pending_request(
    client, make_user, make_loan_request, login, db
):
    make_user("admin001", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant001", "申請者太郎", "password1")
    loan_request = make_loan_request(
        applicant.id, status="pending", start_date=date(2026, 11, 1), due_date=date(2026, 11, 10)
    )
    token = login("admin001", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["decided_at"] is not None

    notifications = crud.get_notifications_by_recipient(db, applicant.id)
    assert len(notifications) == 1
    assert notifications[0].notification_type == "approved"
    assert notifications[0].loan_request_id == loan_request.id


# ========== 結合テストNo.2 ==========
# 存在しない内部IDを指定した場合、HTTP 404が返却されること
def test_approve_loan_request_endpoint_002_not_found(client, make_user, login):
    make_user("admin002", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin002", "AdminPass1")

    response = client.put(
        "/loan-requests/99999/approve",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "貸出申請が見つかりません"


# ========== 結合テストNo.3 ==========
# 承認済みの申請を承認しようとした場合、HTTP 400が返却されること
def test_approve_loan_request_endpoint_003_already_approved(client, make_user, make_loan_request, login):
    make_user("admin003", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant003", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="approved")
    token = login("admin003", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "この申請は承認できません"


# ========== 結合テストNo.4 ==========
# 却下済みの申請を承認しようとした場合、HTTP 400が返却されること
def test_approve_loan_request_endpoint_004_already_rejected(client, make_user, make_loan_request, login):
    make_user("admin004", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant004", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="rejected")
    token = login("admin004", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "この申請は承認できません"


# ========== 結合テストNo.5 ==========
# 開始日が過去の申請中の申請を承認しようとした場合、HTTP 400が返却されること
def test_approve_loan_request_endpoint_005_start_date_in_past(client, make_user, make_loan_request, login):
    make_user("admin005", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant005", "申請者太郎", "password1")
    loan_request = make_loan_request(
        applicant.id, status="pending", start_date=date(2026, 10, 1), due_date=date(2026, 10, 20)
    )
    token = login("admin005", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "開始日を過ぎた申請は承認できません"


# ========== 結合テストNo.6 ==========
# 指定期間が既存の承認済み申請（同一備品）と重複する場合、HTTP 400が返却されること
def test_approve_loan_request_endpoint_006_overlaps_approved_request(
    client, make_user, make_equipment, make_loan_request, login
):
    make_user("admin006", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant_a = make_user("applicantA006", "申請者A", "password1")
    applicant_b = make_user("applicantB006", "申請者B", "password1")
    equipment = make_equipment(asset_number="AST-AP-006")
    make_loan_request(
        applicant_a.id,
        status="approved",
        equipment_internal_id=equipment.id,
        start_date=date(2026, 11, 1),
        due_date=date(2026, 11, 10),
    )
    overlapping_request = make_loan_request(
        applicant_b.id,
        status="pending",
        equipment_internal_id=equipment.id,
        start_date=date(2026, 11, 5),
        due_date=date(2026, 11, 15),
    )
    token = login("admin006", "AdminPass1")

    response = client.put(
        f"/loan-requests/{overlapping_request.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "指定した期間は既に貸出予定があります"


# ========== 結合テストNo.7 ==========
# 管理者権限でないユーザーが承認する場合、HTTP 403が返却されること
def test_approve_loan_request_endpoint_007_forbidden_not_admin(client, make_user, make_loan_request, login):
    make_user("u007", "一般ユーザー", "password1")
    applicant = make_user("applicant007", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="pending")
    token = login("u007", "password1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.8 ==========
# 初回パスワード変更未完了の管理者が承認する場合、HTTP 403が返却されること
def test_approve_loan_request_endpoint_008_forbidden_password_not_changed(
    client, make_user, make_loan_request, login
):
    make_user("admin008", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    applicant = make_user("applicant008", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="pending")
    token = login("admin008", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/approve",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.9 ==========
# トークン未指定で承認する場合、HTTP 401が返却されること
def test_approve_loan_request_endpoint_009_token_missing(client, make_user, make_loan_request):
    applicant = make_user("applicant009", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="pending")

    response = client.put(f"/loan-requests/{loan_request.id}/approve")

    assert response.status_code == 401
