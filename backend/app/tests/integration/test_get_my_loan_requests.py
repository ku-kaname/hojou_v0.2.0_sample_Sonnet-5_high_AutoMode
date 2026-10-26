from datetime import datetime

# ==================================================
# 自分申請一覧取得
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：get_my_loan_requests_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/履歴・状況確認/自分申請一覧取得_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 複数の自分の申請が申請日時の降順で返却されること
def test_get_my_loan_requests_endpoint_001_multiple_sorted_desc(
    client, make_user, make_equipment, make_loan_request, login, db
):
    applicant = make_user("applicant001", "申請者太郎", "password1")
    equipment = make_equipment(asset_number="AST-MY-001")

    loan_request_old = make_loan_request(applicant.id, status="pending", equipment_internal_id=equipment.id)
    loan_request_old.requested_at = datetime(2026, 10, 20, 9, 0, 0)
    loan_request_new = make_loan_request(applicant.id, status="pending", equipment_internal_id=equipment.id)
    loan_request_new.requested_at = datetime(2026, 10, 21, 9, 0, 0)
    db.commit()

    token = login("applicant001", "password1")

    response = client.get("/loan-requests", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["id"] == loan_request_new.id
    assert body[1]["id"] == loan_request_old.id
    assert body[0]["asset_number"] == equipment.asset_number
    assert body[0]["equipment_name"] == equipment.name
    assert body[0]["start_date"] == str(loan_request_new.start_date)
    assert body[0]["due_date"] == str(loan_request_new.due_date)
    assert body[0]["purpose"] == loan_request_new.purpose
    assert body[0]["status"] == "pending"


# ========== 結合テストNo.2 ==========
# 対象がない場合、空リストが返却されること
def test_get_my_loan_requests_endpoint_002_empty_list(client, make_user, login):
    make_user("applicant002", "申請者太郎", "password1")
    token = login("applicant002", "password1")

    response = client.get("/loan-requests", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == []


# ========== 結合テストNo.3 ==========
# 他ユーザーの申請は一覧に含まれないこと
def test_get_my_loan_requests_endpoint_003_other_user_excluded(client, make_user, make_loan_request, login):
    applicant_a = make_user("applicant_a003", "申請者A", "password1")
    applicant_b = make_user("applicant_b003", "申請者B", "password1")
    loan_request_a = make_loan_request(applicant_a.id, status="pending")
    make_loan_request(applicant_b.id, status="pending")

    token = login("applicant_a003", "password1")

    response = client.get("/loan-requests", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == loan_request_a.id


# ========== 結合テストNo.4 ==========
# 却下済みの申請の場合、却下理由（rejection_reason）が返却されること
def test_get_my_loan_requests_endpoint_004_rejected_reason(client, make_user, make_loan_request, login):
    make_user("admin004", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant004", "申請者太郎", "password1")
    loan_request = make_loan_request(applicant.id, status="pending")
    admin_token = login("admin004", "AdminPass1")
    client.put(
        f"/loan-requests/{loan_request.id}/reject",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"rejection_reason": "備品の点検予定のため"},
    )

    applicant_token = login("applicant004", "password1")

    response = client.get("/loan-requests", headers={"Authorization": f"Bearer {applicant_token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["status"] == "rejected"
    assert body[0]["rejection_reason"] == "備品の点検予定のため"


# ========== 結合テストNo.5 ==========
# 初回パスワード変更未完了のユーザーが取得した場合、HTTP 403が返却されること
def test_get_my_loan_requests_endpoint_005_forbidden_password_not_changed(client, make_user, login):
    make_user("u005", "未変更ユーザー", "password1", must_change_password=True)
    token = login("u005", "password1")

    response = client.get("/loan-requests", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.6 ==========
# トークン未指定で取得した場合、HTTP 401が返却されること
def test_get_my_loan_requests_endpoint_006_token_missing(client):
    response = client.get("/loan-requests")

    assert response.status_code == 401
