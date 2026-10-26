import csv
import io
from datetime import date, timedelta

# ==================================================
# 貸出履歴CSV出力
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：export_loan_request_history_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/履歴・状況確認/貸出履歴CSV出力_結合テスト仕様書.md
# ==================================================

_CSV_HEADER = [
    "資産番号",
    "備品名",
    "申請者氏名",
    "開始日",
    "返却予定日",
    "用途",
    "状態",
    "却下・取消理由",
    "申請日時",
    "承認・却下日時",
    "承認・却下者氏名",
    "貸出日時",
    "貸出処理者氏名",
    "返却日時",
    "返却処理者氏名",
    "状態メモ",
    "取消日時",
    "取消処理者氏名",
]


def _parse_csv_rows(response_content: bytes) -> list[list[str]]:
    text = response_content.decode("utf-8-sig")
    return list(csv.reader(io.StringIO(text)))


# ========== 結合テストNo.1 ==========
# 検索結果がCSV形式（UTF-8 BOM付き・ヘッダー行18列・値）で返却されること
def test_export_loan_request_history_endpoint_001_bom_and_header(
    client, make_user, make_equipment, make_loan_request, login
):
    make_user("admin001", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant001", "申請者太郎", "password1")
    equipment = make_equipment(asset_number="AST-EXP-001")
    loan_request = make_loan_request(applicant.id, status="pending", equipment_internal_id=equipment.id)
    token = login("admin001", "AdminPass1")

    response = client.get("/loan-requests/all/export", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.content.startswith(b"\xef\xbb\xbf")
    rows = _parse_csv_rows(response.content)
    assert rows[0] == _CSV_HEADER
    assert len(rows) == 2
    data_row = rows[1]
    assert data_row[0] == equipment.asset_number
    assert data_row[1] == equipment.name
    assert data_row[2] == "申請者太郎"
    assert data_row[3] == str(loan_request.start_date)
    assert data_row[4] == str(loan_request.due_date)
    assert data_row[5] == loan_request.purpose


# ========== 結合テストNo.2 ==========
# 状態が日本語ラベルに変換されること
def test_export_loan_request_history_endpoint_002_status_labels(
    client, make_user, make_equipment, make_loan_request, login
):
    make_user("admin002", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant002", "申請者太郎", "password1")
    token = login("admin002", "AdminPass1")
    headers = {"Authorization": f"Bearer {token}"}

    equipment_pending = make_equipment(asset_number="AST-EXP-002-PENDING")
    make_loan_request(applicant.id, status="pending", equipment_internal_id=equipment_pending.id)

    equipment_approved = make_equipment(asset_number="AST-EXP-002-APPROVED")
    make_loan_request(applicant.id, status="approved", equipment_internal_id=equipment_approved.id)

    today = date.today()

    equipment_lending = make_equipment(asset_number="AST-EXP-002-LENDING")
    lending_request = make_loan_request(
        applicant.id,
        status="pending",
        equipment_internal_id=equipment_lending.id,
        start_date=today,
        due_date=today + timedelta(days=9),
    )
    client.put(f"/loan-requests/{lending_request.id}/approve", headers=headers)
    client.put(f"/loan-requests/{lending_request.id}/lend", headers=headers)

    equipment_returned = make_equipment(asset_number="AST-EXP-002-RETURNED")
    returned_request = make_loan_request(
        applicant.id,
        status="pending",
        equipment_internal_id=equipment_returned.id,
        start_date=today,
        due_date=today + timedelta(days=9),
    )
    client.put(f"/loan-requests/{returned_request.id}/approve", headers=headers)
    client.put(f"/loan-requests/{returned_request.id}/lend", headers=headers)
    client.put(f"/loan-requests/{returned_request.id}/return", headers=headers, json={})

    equipment_rejected = make_equipment(asset_number="AST-EXP-002-REJECTED")
    rejected_request = make_loan_request(applicant.id, status="pending", equipment_internal_id=equipment_rejected.id)
    client.put(
        f"/loan-requests/{rejected_request.id}/reject", headers=headers, json={"rejection_reason": "都合により"}
    )

    equipment_cancelled = make_equipment(asset_number="AST-EXP-002-CANCELLED")
    cancelled_request = make_loan_request(applicant.id, status="pending", equipment_internal_id=equipment_cancelled.id)
    applicant_token = login("applicant002", "password1")
    client.put(
        f"/loan-requests/{cancelled_request.id}/cancel",
        headers={"Authorization": f"Bearer {applicant_token}"},
    )

    response = client.get("/loan-requests/all/export", headers=headers)

    assert response.status_code == 200
    rows = _parse_csv_rows(response.content)
    status_by_asset_number = {row[0]: row[6] for row in rows[1:]}
    assert status_by_asset_number[equipment_pending.asset_number] == "申請中"
    assert status_by_asset_number[equipment_approved.asset_number] == "承認済み"
    assert status_by_asset_number[equipment_lending.asset_number] == "貸出中"
    assert status_by_asset_number[equipment_returned.asset_number] == "返却済み"
    assert status_by_asset_number[equipment_rejected.asset_number] == "却下"
    assert status_by_asset_number[equipment_cancelled.asset_number] == "取消"


# ========== 結合テストNo.3 ==========
# 数式注入対策（先頭が=・+・-・@の値に'が付与されること）
def test_export_loan_request_history_endpoint_003_csv_injection_escaped(client, make_user, make_equipment, login):
    make_user("admin003", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_user("applicant003", "申請者太郎", "password1")
    token = login("admin003", "AdminPass1")

    # 用途欄に数式注入を試みる値を指定して貸出申請を作成する（貸出申請エンドポイント経由）
    equipment = make_equipment(asset_number="AST-EXP-003")
    applicant_token = login("applicant003", "password1")
    client.post(
        "/loan-requests",
        headers={"Authorization": f"Bearer {applicant_token}"},
        json={
            "asset_number": equipment.asset_number,
            "start_date": "2026-11-01",
            "due_date": "2026-11-10",
            "purpose": "=SUM(A1)",
        },
    )

    response = client.get("/loan-requests/all/export", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    rows = _parse_csv_rows(response.content)
    assert len(rows) == 2
    assert rows[1][5] == "'=SUM(A1)"


# ========== 結合テストNo.4 ==========
# 検索条件（絞り込み）が反映されること
def test_export_loan_request_history_endpoint_004_filter_applied(
    client, make_user, make_equipment, make_loan_request, login
):
    make_user("admin004", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("applicant004", "申請者太郎", "password1")

    equipment_target = make_equipment(asset_number="AST-EXP-004A")
    make_loan_request(applicant.id, status="pending", equipment_internal_id=equipment_target.id)
    equipment_other = make_equipment(asset_number="AST-EXP-004B")
    make_loan_request(applicant.id, status="pending", equipment_internal_id=equipment_other.id)

    token = login("admin004", "AdminPass1")

    response = client.get(
        "/loan-requests/all/export",
        params={"asset_number": "AST-EXP-004A"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    rows = _parse_csv_rows(response.content)
    assert len(rows) == 2
    assert rows[1][0] == "AST-EXP-004A"


# ========== 結合テストNo.5 ==========
# 対象がない場合、ヘッダー行のみのCSVが返却されること
def test_export_loan_request_history_endpoint_005_header_only(client, make_user, login):
    make_user("admin005", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin005", "AdminPass1")

    response = client.get("/loan-requests/all/export", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    rows = _parse_csv_rows(response.content)
    assert rows == [_CSV_HEADER]


# ========== 結合テストNo.6 ==========
# Content-Dispositionヘッダーが正しく設定されること
def test_export_loan_request_history_endpoint_006_content_disposition(client, make_user, login):
    make_user("admin006", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin006", "AdminPass1")

    response = client.get("/loan-requests/all/export", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.headers["content-disposition"] == 'attachment; filename="loan_history.csv"'
    assert response.headers["content-type"] == "text/csv; charset=utf-8"


# ========== 結合テストNo.7 ==========
# 管理者権限でないユーザーが取得した場合、HTTP 403が返却されること
def test_export_loan_request_history_endpoint_007_forbidden_not_admin(client, make_user, login):
    make_user("u007", "一般ユーザー", "password1")
    token = login("u007", "password1")

    response = client.get("/loan-requests/all/export", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.8 ==========
# 初回パスワード変更未完了の管理者が取得した場合、HTTP 403が返却されること
def test_export_loan_request_history_endpoint_008_forbidden_password_not_changed(client, make_user, login):
    make_user("admin008", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    token = login("admin008", "AdminPass1")

    response = client.get("/loan-requests/all/export", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.9 ==========
# トークン未指定で取得した場合、HTTP 401が返却されること
def test_export_loan_request_history_endpoint_009_token_missing(client):
    response = client.get("/loan-requests/all/export")

    assert response.status_code == 401


# ========== 結合テストNo.10 ==========
# 資産番号（asset_number）が33文字（上限超過）の場合、HTTP 422が返却されること
def test_export_loan_request_history_endpoint_010_asset_number_too_long(client, make_user, login):
    make_user("admin010", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin010", "AdminPass1")

    response = client.get(
        "/loan-requests/all/export",
        params={"asset_number": "A" * 33},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


# ========== 結合テストNo.11 ==========
# 借用者ユーザーID（user_id）が33文字（上限超過）の場合、HTTP 422が返却されること
def test_export_loan_request_history_endpoint_011_user_id_too_long(client, make_user, login):
    make_user("admin011", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin011", "AdminPass1")

    response = client.get(
        "/loan-requests/all/export",
        params={"user_id": "a" * 33},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


# ========== 結合テストNo.12 ==========
# 開始日（start_date_from）に日付形式でない文字列を指定した場合、HTTP 422が返却されること
def test_export_loan_request_history_endpoint_012_start_date_from_invalid_format(client, make_user, login):
    make_user("admin012", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin012", "AdminPass1")

    response = client.get(
        "/loan-requests/all/export",
        params={"start_date_from": "not-a-date"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
