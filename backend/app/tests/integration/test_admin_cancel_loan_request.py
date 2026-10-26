from app import crud

# ==================================================
# 管理者申請取消
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：admin_cancel_loan_request_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/貸出申請・承認/管理者申請取消_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 承認済みの申請を取消した場合、HTTP 200で取消内容が返却され、申請者宛に通知が1件登録されること
def test_admin_cancel_loan_request_endpoint_001_cancel_approved_request(
    client, make_user, make_loan_request, login, db
):
    make_user("admin001", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant001", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="approved")
    token = login("admin001", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/admin-cancel",
        headers={"Authorization": f"Bearer {token}"},
        json={"cancellation_reason": "備品の緊急点検のため"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "cancelled"
    assert body["rejection_reason"] == "備品の緊急点検のため"
    assert body["cancelled_at"] is not None

    notifications = crud.get_notifications_by_recipient(db, applicant.id)
    assert len(notifications) == 1
    assert notifications[0].notification_type == "cancelled"
    assert notifications[0].loan_request_id == loan_request.id


# ========== 結合テストNo.2 ==========
# 存在しない内部IDを指定した場合、HTTP 404が返却されること
def test_admin_cancel_loan_request_endpoint_002_not_found(client, make_user, login):
    make_user("admin002", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin002", "AdminPass1")

    response = client.put(
        "/loan-requests/99999/admin-cancel",
        headers={"Authorization": f"Bearer {token}"},
        json={"cancellation_reason": "テスト理由"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "貸出申請が見つかりません"


# ========== 結合テストNo.3 ==========
# 申請中の申請を取消しようとした場合、HTTP 400が返却されること
def test_admin_cancel_loan_request_endpoint_003_pending_request(client, make_user, make_loan_request, login):
    make_user("admin003", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant003", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="pending")
    token = login("admin003", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/admin-cancel",
        headers={"Authorization": f"Bearer {token}"},
        json={"cancellation_reason": "テスト理由"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "この申請は取消できません"


# ========== 結合テストNo.4 ==========
# 貸出中の申請を取消しようとした場合、HTTP 400が返却されること
def test_admin_cancel_loan_request_endpoint_004_lending_request(client, make_user, make_loan_request, login):
    make_user("admin004", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant004", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="lending")
    token = login("admin004", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/admin-cancel",
        headers={"Authorization": f"Bearer {token}"},
        json={"cancellation_reason": "テスト理由"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "この申請は取消できません"


# ========== 結合テストNo.5 ==========
# 必須パラメータ（cancellation_reason）が欠落している場合、HTTP 422が返却されること
def test_admin_cancel_loan_request_endpoint_005_missing_required_cancellation_reason(
    client, make_user, make_loan_request, login
):
    make_user("admin005", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant005", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="approved")
    token = login("admin005", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/admin-cancel",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    assert response.status_code == 422


# ========== 結合テストNo.6 ==========
# cancellation_reasonが上限（200文字）を超過している場合、HTTP 422が返却されること
def test_admin_cancel_loan_request_endpoint_006_cancellation_reason_too_long(
    client, make_user, make_loan_request, login
):
    make_user("admin006", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant006", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="approved")
    token = login("admin006", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/admin-cancel",
        headers={"Authorization": f"Bearer {token}"},
        json={"cancellation_reason": "a" * 201},
    )

    assert response.status_code == 422


# ========== 結合テストNo.7 ==========
# 管理者権限でないユーザーが取消する場合、HTTP 403が返却されること
def test_admin_cancel_loan_request_endpoint_007_forbidden_not_admin(client, make_user, make_loan_request, login):
    make_user("u007", "一般ユーザー", "password1")
    applicant = make_user("applicant007", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="approved")
    token = login("u007", "password1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/admin-cancel",
        headers={"Authorization": f"Bearer {token}"},
        json={"cancellation_reason": "テスト理由"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.8 ==========
# 初回パスワード変更未完了の管理者が取消する場合、HTTP 403が返却されること
def test_admin_cancel_loan_request_endpoint_008_forbidden_password_not_changed(
    client, make_user, make_loan_request, login
):
    make_user("admin008", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    applicant = make_user("applicant008", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="approved")
    token = login("admin008", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/admin-cancel",
        headers={"Authorization": f"Bearer {token}"},
        json={"cancellation_reason": "テスト理由"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.9 ==========
# トークン未指定で取消する場合、HTTP 401が返却されること
def test_admin_cancel_loan_request_endpoint_009_token_missing(client, make_user, make_loan_request):
    applicant = make_user("applicant009", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="approved")

    response = client.put(
        f"/loan-requests/{loan_request.id}/admin-cancel",
        json={"cancellation_reason": "テスト理由"},
    )

    assert response.status_code == 401
