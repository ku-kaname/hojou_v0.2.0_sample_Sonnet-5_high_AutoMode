from datetime import date, timedelta

from app import crud

# ==================================================
# 期限超過一覧取得
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：get_overdue_loan_requests_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/履歴・状況確認/期限超過一覧取得_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 複数の期限超過申請が返却予定日の昇順で返却されること
def test_get_overdue_loan_requests_endpoint_001_multiple_sorted_asc(
    client, make_user, make_equipment, make_loan_request, login, db
):
    admin = make_user("admin001", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant001", "申請者太郎", "password1")
    today = date.today()

    equipment_1 = make_equipment(asset_number="AST-OD-001")
    loan_request_due_5 = make_loan_request(
        applicant.id,
        status="approved",
        equipment_internal_id=equipment_1.id,
        start_date=today - timedelta(days=10),
        due_date=today - timedelta(days=5),
    )
    crud.lend_loan_request(db, loan_request_due_5.id, admin.id)

    equipment_2 = make_equipment(asset_number="AST-OD-002")
    loan_request_due_2 = make_loan_request(
        applicant.id,
        status="approved",
        equipment_internal_id=equipment_2.id,
        start_date=today - timedelta(days=10),
        due_date=today - timedelta(days=2),
    )
    crud.lend_loan_request(db, loan_request_due_2.id, admin.id)

    token = login("admin001", "AdminPass1")

    response = client.get("/loan-requests/overdue", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["id"] == loan_request_due_5.id
    assert body[1]["id"] == loan_request_due_2.id
    assert body[0]["overdue_days"] == 5
    assert body[1]["overdue_days"] == 2
    assert body[0]["asset_number"] == equipment_1.asset_number
    assert body[0]["equipment_name"] == equipment_1.name
    assert body[0]["applicant_name"] == "申請者太郎"


# ========== 結合テストNo.2 ==========
# 対象がない場合、空リストが返却されること
def test_get_overdue_loan_requests_endpoint_002_empty_list(client, make_user, login):
    make_user("admin002", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin002", "AdminPass1")

    response = client.get("/loan-requests/overdue", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == []


# ========== 結合テストNo.3 ==========
# 貸出中以外の状態、または返却予定日が今日以降の貸出中の申請は一覧に含まれないこと
def test_get_overdue_loan_requests_endpoint_003_only_overdue_lending_included(
    client, make_user, make_loan_request, login, db
):
    admin = make_user("admin003", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant003", "申請者太郎", "password1")
    today = date.today()

    make_loan_request(
        applicant.id,
        status="approved",
        start_date=today - timedelta(days=10),
        due_date=today - timedelta(days=5),
    )

    not_overdue_request = make_loan_request(
        applicant.id,
        status="approved",
        start_date=today - timedelta(days=10),
        due_date=today,
    )
    crud.lend_loan_request(db, not_overdue_request.id, admin.id)

    overdue_request = make_loan_request(
        applicant.id,
        status="approved",
        start_date=today - timedelta(days=10),
        due_date=today - timedelta(days=1),
    )
    crud.lend_loan_request(db, overdue_request.id, admin.id)

    token = login("admin003", "AdminPass1")

    response = client.get("/loan-requests/overdue", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == overdue_request.id


# ========== 結合テストNo.4 ==========
# 管理者権限でないユーザーが取得した場合、HTTP 403が返却されること
def test_get_overdue_loan_requests_endpoint_004_forbidden_not_admin(client, make_user, login):
    make_user("u004", "一般ユーザー", "password1")
    token = login("u004", "password1")

    response = client.get("/loan-requests/overdue", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.5 ==========
# 初回パスワード変更未完了の管理者が取得した場合、HTTP 403が返却されること
def test_get_overdue_loan_requests_endpoint_005_forbidden_password_not_changed(client, make_user, login):
    make_user("admin005", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    token = login("admin005", "AdminPass1")

    response = client.get("/loan-requests/overdue", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.6 ==========
# トークン未指定で取得した場合、HTTP 401が返却されること
def test_get_overdue_loan_requests_endpoint_006_token_missing(client):
    response = client.get("/loan-requests/overdue")

    assert response.status_code == 401
