from app import crud

# ==================================================
# 申請却下
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：reject_loan_request_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/貸出申請・承認/申請却下_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 申請中の申請を却下した場合、HTTP 200で却下内容が返却され、申請者宛に通知が1件登録されること
def test_reject_loan_request_endpoint_001_reject_pending_request(client, make_user, make_loan_request, login, db):
    make_user("admin001", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant001", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="pending")
    token = login("admin001", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/reject",
        headers={"Authorization": f"Bearer {token}"},
        json={"rejection_reason": "備品の点検予定のため"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "rejected"
    assert body["rejection_reason"] == "備品の点検予定のため"
    assert body["decided_at"] is not None

    notifications = crud.get_notifications_by_recipient(db, applicant.id)
    assert len(notifications) == 1
    assert notifications[0].notification_type == "rejected"
    assert notifications[0].loan_request_id == loan_request.id


# ========== 結合テストNo.2 ==========
# 存在しない内部IDを指定した場合、HTTP 404が返却されること
def test_reject_loan_request_endpoint_002_not_found(client, make_user, login):
    make_user("admin002", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin002", "AdminPass1")

    response = client.put(
        "/loan-requests/99999/reject",
        headers={"Authorization": f"Bearer {token}"},
        json={"rejection_reason": "テスト理由"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "貸出申請が見つかりません"


# ========== 結合テストNo.3 ==========
# 承認済みの申請を却下しようとした場合、HTTP 400が返却されること
def test_reject_loan_request_endpoint_003_already_approved(client, make_user, make_loan_request, login):
    make_user("admin003", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant003", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="approved")
    token = login("admin003", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/reject",
        headers={"Authorization": f"Bearer {token}"},
        json={"rejection_reason": "テスト理由"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "この申請は却下できません"


# ========== 結合テストNo.4 ==========
# 必須パラメータ（rejection_reason）が欠落している場合、HTTP 422が返却されること
def test_reject_loan_request_endpoint_004_missing_required_rejection_reason(
    client, make_user, make_loan_request, login
):
    make_user("admin004", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant004", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="pending")
    token = login("admin004", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/reject",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    assert response.status_code == 422


# ========== 結合テストNo.5 ==========
# rejection_reasonが上限（200文字）を超過している場合、HTTP 422が返却されること
def test_reject_loan_request_endpoint_005_rejection_reason_too_long(
    client, make_user, make_loan_request, login
):
    make_user("admin005", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant005", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="pending")
    token = login("admin005", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/reject",
        headers={"Authorization": f"Bearer {token}"},
        json={"rejection_reason": "a" * 201},
    )

    assert response.status_code == 422


# ========== 結合テストNo.6 ==========
# 管理者権限でないユーザーが却下する場合、HTTP 403が返却されること
def test_reject_loan_request_endpoint_006_forbidden_not_admin(client, make_user, make_loan_request, login):
    make_user("u006", "一般ユーザー", "password1")
    applicant = make_user("applicant006", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="pending")
    token = login("u006", "password1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/reject",
        headers={"Authorization": f"Bearer {token}"},
        json={"rejection_reason": "テスト理由"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.7 ==========
# 初回パスワード変更未完了の管理者が却下する場合、HTTP 403が返却されること
def test_reject_loan_request_endpoint_007_forbidden_password_not_changed(
    client, make_user, make_loan_request, login
):
    make_user("admin007", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    applicant = make_user("applicant007", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="pending")
    token = login("admin007", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/reject",
        headers={"Authorization": f"Bearer {token}"},
        json={"rejection_reason": "テスト理由"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.8 ==========
# トークン未指定で却下する場合、HTTP 401が返却されること
def test_reject_loan_request_endpoint_008_token_missing(client, make_user, make_loan_request):
    applicant = make_user("applicant008", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="pending")

    response = client.put(
        f"/loan-requests/{loan_request.id}/reject",
        json={"rejection_reason": "テスト理由"},
    )

    assert response.status_code == 401
