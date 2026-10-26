from datetime import datetime

# ==================================================
# 承認待ち申請一覧取得
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：get_pending_loan_requests_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/貸出申請・承認/承認待ち申請一覧取得_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 複数の申請中申請が申請日時の昇順で返却されること
def test_get_pending_loan_requests_endpoint_001_multiple_sorted_asc(
    client, make_user, make_equipment, make_loan_request, login, db
):
    make_user("admin001", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant001", "申請者太郎", "password1")
    equipment = make_equipment(asset_number="AST-PL-001")

    loan_request_old = make_loan_request(applicant.id, status="pending", equipment_internal_id=equipment.id)
    loan_request_old.requested_at = datetime(2026, 10, 20, 9, 0, 0)
    loan_request_new = make_loan_request(applicant.id, status="pending", equipment_internal_id=equipment.id)
    loan_request_new.requested_at = datetime(2026, 10, 21, 9, 0, 0)
    db.commit()

    token = login("admin001", "AdminPass1")

    response = client.get("/loan-requests/pending", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["id"] == loan_request_old.id
    assert body[1]["id"] == loan_request_new.id
    assert body[0]["asset_number"] == equipment.asset_number
    assert body[0]["equipment_name"] == equipment.name
    assert body[0]["applicant_name"] == "申請者太郎"
    assert body[0]["start_date"] == str(loan_request_old.start_date)
    assert body[0]["due_date"] == str(loan_request_old.due_date)
    assert body[0]["purpose"] == loan_request_old.purpose


# ========== 結合テストNo.2 ==========
# 対象がない場合、空リストが返却されること
def test_get_pending_loan_requests_endpoint_002_empty_list(client, make_user, login):
    make_user("admin002", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin002", "AdminPass1")

    response = client.get("/loan-requests/pending", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == []


# ========== 結合テストNo.3 ==========
# 申請中以外の状態の申請は一覧に含まれないこと
def test_get_pending_loan_requests_endpoint_003_only_pending_included(
    client, make_user, make_loan_request, login
):
    make_user("admin003", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant003", "申請者太郎", "password1")

    pending_request = make_loan_request(applicant.id, status="pending")
    make_loan_request(applicant.id, status="approved")
    make_loan_request(applicant.id, status="rejected")

    token = login("admin003", "AdminPass1")

    response = client.get("/loan-requests/pending", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == pending_request.id


# ========== 結合テストNo.4 ==========
# 管理者権限でないユーザーが取得した場合、HTTP 403が返却されること
def test_get_pending_loan_requests_endpoint_004_forbidden_not_admin(client, make_user, login):
    make_user("u004", "一般ユーザー", "password1")
    token = login("u004", "password1")

    response = client.get("/loan-requests/pending", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.5 ==========
# 初回パスワード変更未完了の管理者が取得した場合、HTTP 403が返却されること
def test_get_pending_loan_requests_endpoint_005_forbidden_password_not_changed(client, make_user, login):
    make_user("admin005", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    token = login("admin005", "AdminPass1")

    response = client.get("/loan-requests/pending", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.6 ==========
# トークン未指定で取得した場合、HTTP 401が返却されること
def test_get_pending_loan_requests_endpoint_006_token_missing(client):
    response = client.get("/loan-requests/pending")

    assert response.status_code == 401
