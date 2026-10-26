# ==================================================
# 返却処理
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：return_loan_request_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/貸出・返却/返却処理_結合テスト仕様書.md
# ==================================================

from app import crud


# ========== 結合テストNo.1 ==========
# 状態メモなしで貸出中の申請を返却処理した場合、HTTP 200で返却内容が返却されること
def test_return_loan_request_endpoint_001_return_without_note(client, make_user, make_loan_request, login, db):
    admin = make_user("admin001", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant001", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="approved")
    # 貸出中状態は実際の貸出処理（lend_loan_request）を経由してのみ到達するため、
    # 貸出日時（lent_at）等の整合性を保つためcrud経由で貸出中状態に遷移させる
    crud.lend_loan_request(db, loan_request.id, admin.id)
    token = login("admin001", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/return",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == loan_request.id
    assert body["status"] == "returned"
    assert body["returned_at"] is not None
    assert body["return_note"] is None


# ========== 結合テストNo.2 ==========
# 状態メモを指定して貸出中の申請を返却処理した場合、HTTP 200で指定した状態メモが返却されること
def test_return_loan_request_endpoint_002_return_with_note(client, make_user, make_loan_request, login, db):
    admin = make_user("admin002", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant002", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="approved")
    crud.lend_loan_request(db, loan_request.id, admin.id)
    token = login("admin002", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/return",
        headers={"Authorization": f"Bearer {token}"},
        json={"return_note": "汚損あり"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "returned"
    assert body["returned_at"] is not None
    assert body["return_note"] == "汚損あり"


# ========== 結合テストNo.3 ==========
# 存在しない内部IDを指定した場合、HTTP 404が返却されること
def test_return_loan_request_endpoint_003_not_found(client, make_user, login):
    make_user("admin003", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin003", "AdminPass1")

    response = client.put(
        "/loan-requests/99999/return",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "貸出申請が見つかりません"


# ========== 結合テストNo.4 ==========
# 貸出中以外（承認済み）の申請を返却処理しようとした場合、HTTP 400が返却されること
def test_return_loan_request_endpoint_004_not_lending(client, make_user, make_loan_request, login):
    make_user("admin004", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant004", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="approved")
    token = login("admin004", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/return",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "この申請は返却処理できません"


# ========== 結合テストNo.5 ==========
# 状態メモが200文字を超過する場合、HTTP 422が返却されること
def test_return_loan_request_endpoint_005_note_too_long(client, make_user, make_loan_request, login):
    make_user("admin005", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant005", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="lending")
    token = login("admin005", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/return",
        headers={"Authorization": f"Bearer {token}"},
        json={"return_note": "あ" * 201},
    )

    assert response.status_code == 422


# ========== 結合テストNo.6 ==========
# 管理者権限でないユーザーが返却処理する場合、HTTP 403が返却されること
def test_return_loan_request_endpoint_006_forbidden_not_admin(client, make_user, make_loan_request, login):
    make_user("u006", "一般ユーザー", "password1")
    applicant = make_user("applicant006", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="lending")
    token = login("u006", "password1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/return",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.7 ==========
# 初回パスワード変更未完了の管理者が返却処理する場合、HTTP 403が返却されること
def test_return_loan_request_endpoint_007_forbidden_password_not_changed(
    client, make_user, make_loan_request, login
):
    make_user("admin007", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    applicant = make_user("applicant007", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="lending")
    token = login("admin007", "AdminPass1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/return",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.8 ==========
# トークン未指定で返却処理する場合、HTTP 401が返却されること
def test_return_loan_request_endpoint_008_token_missing(client, make_user, make_loan_request):
    applicant = make_user("applicant008", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="lending")

    response = client.put(f"/loan-requests/{loan_request.id}/return", json={})

    assert response.status_code == 401
