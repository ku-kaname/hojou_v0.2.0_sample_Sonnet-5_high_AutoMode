import csv
import io

from app import crud

# ==================================================
# 備品CSV一括登録
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：bulk_import_equipment_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/備品管理/備品CSV一括登録_結合テスト仕様書.md
# ==================================================

_HEADER = ["資産番号", "備品名", "分類", "説明", "保管場所"]


def _build_csv_bytes(rows: list[list[str]], header: list[str] | None = None) -> bytes:
    """CSVアップロードテスト用のCSVファイル内容（bytes）を組み立てる"""

    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\r\n")
    writer.writerow(header if header is not None else _HEADER)
    for row in rows:
        writer.writerow(row)
    return output.getvalue().encode("utf-8")


def _upload(client, token, content: bytes):
    """multipart/form-dataでCSVファイルをアップロードする"""

    return client.post(
        "/equipment/bulk-import",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("import.csv", content, "text/csv")},
    )


# ========== 結合テストNo.1 ==========
# 全項目を指定した2行の正常なCSVで一括登録した場合、HTTP 200・registered_count=2でDBに登録されること
def test_bulk_import_equipment_001_register_two_rows(client, make_user, login, db):
    make_user("admin01", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin01", "AdminPass1")
    content = _build_csv_bytes(
        [
            ["AST-BULK-001", "テストPC1", "ノートPC", "説明1", "本社倉庫"],
            ["AST-BULK-002", "テストPC2", "デスクトップPC", "説明2", "別館倉庫"],
        ]
    )

    response = _upload(client, token, content)

    assert response.status_code == 200
    assert response.json()["registered_count"] == 2
    registered_1 = crud.get_equipment_by_asset_number(db, "AST-BULK-001")
    registered_2 = crud.get_equipment_by_asset_number(db, "AST-BULK-002")
    assert registered_1 is not None
    assert registered_1.name == "テストPC1"
    assert registered_2 is not None
    assert registered_2.name == "テストPC2"


# ========== 結合テストNo.2 ==========
# 説明・保管場所を空欄にしたデータ行を含むCSVで一括登録した場合、description=null・location=nullで登録されること
def test_bulk_import_equipment_002_register_with_empty_optional_fields(client, make_user, login, db):
    make_user("admin02", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin02", "AdminPass1")
    content = _build_csv_bytes([["AST-BULK-003", "テストPC3", "ノートPC", "", ""]])

    response = _upload(client, token, content)

    assert response.status_code == 200
    assert response.json()["registered_count"] == 1
    registered = crud.get_equipment_by_asset_number(db, "AST-BULK-003")
    assert registered is not None
    assert registered.description is None
    assert registered.location is None


# ========== 結合テストNo.3 ==========
# ファイルサイズが5MBを超えるCSVをアップロードした場合、HTTP 400が返却されること
def test_bulk_import_equipment_003_file_too_large(client, make_user, login):
    make_user("admin03", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin03", "AdminPass1")
    content = _build_csv_bytes([["AST-BULK-004", "テストPC4", "ノートPC", "a" * (5 * 1024 * 1024 + 10), ""]])

    response = _upload(client, token, content)

    assert response.status_code == 400
    assert response.json()["detail"] == "ファイルサイズは5MB以内にしてください"


# ========== 結合テストNo.4 ==========
# ヘッダー列が不正な（列名・順序が異なる）CSVをアップロードした場合、HTTP 400が返却されること
def test_bulk_import_equipment_004_invalid_header(client, make_user, login):
    make_user("admin04", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin04", "AdminPass1")
    content = _build_csv_bytes(
        [["AST-BULK-005", "テストPC5", "ノートPC"]], header=["資産番号", "備品名", "分類"]
    )

    response = _upload(client, token, content)

    assert response.status_code == 400
    assert response.json()["detail"] == "CSVのヘッダー列が不正です（資産番号・備品名・分類・説明・保管場所の順で指定してください）"


# ========== 結合テストNo.5 ==========
# データ行数が1,000行を超えるCSVをアップロードした場合、HTTP 400が返却されること
def test_bulk_import_equipment_005_too_many_rows(client, make_user, login):
    make_user("admin05", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin05", "AdminPass1")
    rows = [[f"AST-BULK-{i:04d}", f"テストPC{i}", "ノートPC", "", ""] for i in range(1001)]
    content = _build_csv_bytes(rows)

    response = _upload(client, token, content)

    assert response.status_code == 400
    assert response.json()["detail"] == "データ行数は1,000行以内にしてください"


# ========== 結合テストNo.6 ==========
# 資産番号が33文字（上限超過）のデータ行を含むCSVをアップロードした場合、HTTP 400が返却されること
def test_bulk_import_equipment_006_asset_number_too_long(client, make_user, login):
    make_user("admin06", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin06", "AdminPass1")
    content = _build_csv_bytes([["A" * 33, "テストPC6", "ノートPC", "", ""]])

    response = _upload(client, token, content)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert {"row_number": 2, "error_message": "資産番号は32文字以内の半角英数字と`-`で入力してください"} in detail


# ========== 結合テストNo.7 ==========
# 資産番号に許可されていない文字（記号等）を含むデータ行を含むCSVをアップロードした場合、HTTP 400が返却されること
def test_bulk_import_equipment_007_asset_number_invalid_character(client, make_user, login):
    make_user("admin07", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin07", "AdminPass1")
    content = _build_csv_bytes([["AST#007", "テストPC7", "ノートPC", "", ""]])

    response = _upload(client, token, content)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert {"row_number": 2, "error_message": "資産番号は32文字以内の半角英数字と`-`で入力してください"} in detail


# ========== 結合テストNo.8 ==========
# 備品名が空のデータ行を含むCSVをアップロードした場合、HTTP 400が返却されること
def test_bulk_import_equipment_008_name_empty(client, make_user, login):
    make_user("admin08", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin08", "AdminPass1")
    content = _build_csv_bytes([["AST-BULK-008", "", "ノートPC", "", ""]])

    response = _upload(client, token, content)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert {"row_number": 2, "error_message": "備品名は1〜100文字で入力してください"} in detail


# ========== 結合テストNo.9 ==========
# 備品名が101文字（上限超過）のデータ行を含むCSVをアップロードした場合、HTTP 400が返却されること
def test_bulk_import_equipment_009_name_too_long(client, make_user, login):
    make_user("admin09", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin09", "AdminPass1")
    content = _build_csv_bytes([["AST-BULK-009", "a" * 101, "ノートPC", "", ""]])

    response = _upload(client, token, content)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert {"row_number": 2, "error_message": "備品名は1〜100文字で入力してください"} in detail


# ========== 結合テストNo.10 ==========
# 分類が空のデータ行を含むCSVをアップロードした場合、HTTP 400が返却されること
def test_bulk_import_equipment_010_category_empty(client, make_user, login):
    make_user("admin10", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin10", "AdminPass1")
    content = _build_csv_bytes([["AST-BULK-010", "テストPC10", "", "", ""]])

    response = _upload(client, token, content)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert {"row_number": 2, "error_message": "分類は1〜50文字で入力してください"} in detail


# ========== 結合テストNo.11 ==========
# 説明が501文字（上限超過）のデータ行を含むCSVをアップロードした場合、HTTP 400が返却されること
def test_bulk_import_equipment_011_description_too_long(client, make_user, login):
    make_user("admin11", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin11", "AdminPass1")
    content = _build_csv_bytes([["AST-BULK-011", "テストPC11", "ノートPC", "a" * 501, ""]])

    response = _upload(client, token, content)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert {"row_number": 2, "error_message": "説明は500文字以内で入力してください"} in detail


# ========== 結合テストNo.12 ==========
# 保管場所が101文字（上限超過）のデータ行を含むCSVをアップロードした場合、HTTP 400が返却されること
def test_bulk_import_equipment_012_location_too_long(client, make_user, login):
    make_user("admin12", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin12", "AdminPass1")
    content = _build_csv_bytes([["AST-BULK-012", "テストPC12", "ノートPC", "", "a" * 101]])

    response = _upload(client, token, content)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert {"row_number": 2, "error_message": "保管場所は100文字以内で入力してください"} in detail


# ========== 結合テストNo.13 ==========
# ファイル内で資産番号が重複する2行を含むCSVをアップロードした場合、HTTP 400が返却されること
def test_bulk_import_equipment_013_duplicate_within_file(client, make_user, login):
    make_user("admin13", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin13", "AdminPass1")
    content = _build_csv_bytes(
        [
            ["AST-BULK-013", "テストPC13-1", "ノートPC", "", ""],
            ["AST-BULK-013", "テストPC13-2", "ノートPC", "", ""],
        ]
    )

    response = _upload(client, token, content)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert {"row_number": 2, "error_message": "資産番号がファイル内で重複しています"} in detail
    assert {"row_number": 3, "error_message": "資産番号がファイル内で重複しています"} in detail


# ========== 結合テストNo.14 ==========
# DB内に既に存在する資産番号のデータ行を含むCSVをアップロードした場合、HTTP 400が返却されること
def test_bulk_import_equipment_014_duplicate_in_db(client, make_user, make_equipment, login):
    make_user("admin14", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_equipment(asset_number="AST-001")
    token = login("admin14", "AdminPass1")
    content = _build_csv_bytes([["AST-001", "テストPC14", "ノートPC", "", ""]])

    response = _upload(client, token, content)

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert {"row_number": 2, "error_message": "資産番号は既に登録されています"} in detail


# ========== 結合テストNo.15 ==========
# 1行でもエラーがある場合、他の正常行も含め全件登録されないこと
def test_bulk_import_equipment_015_no_partial_commit(client, make_user, make_equipment, login, db):
    make_user("admin15", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_equipment(asset_number="AST-002")
    token = login("admin15", "AdminPass1")
    content = _build_csv_bytes(
        [
            ["AST-BULK-015", "テストPC15", "ノートPC", "", ""],
            ["AST-002", "テストPC15-2", "ノートPC", "", ""],
        ]
    )

    response = _upload(client, token, content)

    assert response.status_code == 400
    assert crud.get_equipment_by_asset_number(db, "AST-BULK-015") is None


# ========== 結合テストNo.16 ==========
# 管理者権限でないユーザーがアップロードした場合、HTTP 403が返却されること
def test_bulk_import_equipment_016_forbidden_not_admin(client, make_user, login):
    make_user("u016", "一般ユーザー", "password1", role="general")
    token = login("u016", "password1")
    content = _build_csv_bytes([["AST-BULK-016", "テストPC16", "ノートPC", "", ""]])

    response = _upload(client, token, content)

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.17 ==========
# 初回パスワード変更未完了の管理者がアップロードした場合、HTTP 403が返却されること
def test_bulk_import_equipment_017_forbidden_password_not_changed(client, make_user, login):
    make_user("admin17", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    token = login("admin17", "AdminPass1")
    content = _build_csv_bytes([["AST-BULK-017", "テストPC17", "ノートPC", "", ""]])

    response = _upload(client, token, content)

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.18 ==========
# トークン未指定でアップロードした場合、HTTP 401が返却されること
def test_bulk_import_equipment_018_token_missing(client):
    content = _build_csv_bytes([["AST-BULK-018", "テストPC18", "ノートPC", "", ""]])

    response = client.post("/equipment/bulk-import", files={"file": ("import.csv", content, "text/csv")})

    assert response.status_code == 401


# ========== 結合テストNo.19 ==========
# CSVファイル（file）を指定せずにアップロードした場合、HTTP 422が返却されること
def test_bulk_import_equipment_019_file_missing(client, make_user, login):
    make_user("admin19", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin19", "AdminPass1")

    response = client.post("/equipment/bulk-import", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 422
