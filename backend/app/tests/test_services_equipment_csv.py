import csv
import io

import pytest
from fastapi import HTTPException

from app import services

# ==================================================
# 備品CSV行形式検証
# テスト対象ファイル：services.py
# テスト対象クラス：-
# テスト対象メソッド：_validate_equipment_csv_row
# テスト仕様書：テスト仕様書/単体テスト仕様書/サーバー処理（main）/備品管理/備品CSV行形式検証_単体テスト仕様書.md
# ==================================================


def _make_row(asset_number="A-001", name="備品A", category="分類A", description="説明", location="保管場所"):
    # 備品CSVの1データ行（資産番号・備品名・分類・説明・保管場所の順）を、正常値をデフォルトに生成する
    return [asset_number, name, category, description, location]


# ========== 単体テストNo.1 ==========
# 資産番号が半角英数字と`-`のみで32文字（上限値）の場合、エラーとならないこと
def test_validate_equipment_csv_row_001_asset_number_32_chars():
    row = _make_row(asset_number="A" * 32)

    row_errors = services._validate_equipment_csv_row(2, row)

    assert row_errors == []


# ========== 単体テストNo.2 ==========
# 資産番号が33文字（上限値超過）の場合、エラーとなること
def test_validate_equipment_csv_row_002_asset_number_33_chars():
    row = _make_row(asset_number="A" * 33)

    row_errors = services._validate_equipment_csv_row(2, row)

    assert any(error.error_message == "資産番号は32文字以内の半角英数字と`-`で入力してください" for error in row_errors)


# ========== 単体テストNo.3 ==========
# 資産番号に全角文字を含む場合、エラーとなること
def test_validate_equipment_csv_row_003_asset_number_fullwidth():
    row = _make_row(asset_number="Ａ－００１")

    row_errors = services._validate_equipment_csv_row(2, row)

    assert any(error.error_message == "資産番号は32文字以内の半角英数字と`-`で入力してください" for error in row_errors)


# ========== 単体テストNo.4 ==========
# 資産番号が空文字（下限値未満）の場合、エラーとなること
def test_validate_equipment_csv_row_004_asset_number_empty():
    row = _make_row(asset_number="")

    row_errors = services._validate_equipment_csv_row(2, row)

    assert any(error.error_message == "資産番号は32文字以内の半角英数字と`-`で入力してください" for error in row_errors)


# ========== 単体テストNo.5 ==========
# 備品名が1文字の場合と100文字の場合のいずれもエラーとならないこと
def test_validate_equipment_csv_row_005_name_boundary_valid():
    row_errors_1_char = services._validate_equipment_csv_row(2, _make_row(name="A"))
    row_errors_100_chars = services._validate_equipment_csv_row(2, _make_row(name="A" * 100))

    assert row_errors_1_char == []
    assert row_errors_100_chars == []


# ========== 単体テストNo.6 ==========
# 備品名が0文字の場合と101文字の場合のいずれもエラーとなること
def test_validate_equipment_csv_row_006_name_boundary_invalid():
    row_errors_0_chars = services._validate_equipment_csv_row(2, _make_row(name=""))
    row_errors_101_chars = services._validate_equipment_csv_row(2, _make_row(name="A" * 101))

    assert any(error.error_message == "備品名は1〜100文字で入力してください" for error in row_errors_0_chars)
    assert any(error.error_message == "備品名は1〜100文字で入力してください" for error in row_errors_101_chars)


# ========== 単体テストNo.7 ==========
# 分類が1文字の場合と50文字の場合のいずれもエラーとならないこと
def test_validate_equipment_csv_row_007_category_boundary_valid():
    row_errors_1_char = services._validate_equipment_csv_row(2, _make_row(category="A"))
    row_errors_50_chars = services._validate_equipment_csv_row(2, _make_row(category="A" * 50))

    assert row_errors_1_char == []
    assert row_errors_50_chars == []


# ========== 単体テストNo.8 ==========
# 分類が0文字の場合と51文字の場合のいずれもエラーとなること
def test_validate_equipment_csv_row_008_category_boundary_invalid():
    row_errors_0_chars = services._validate_equipment_csv_row(2, _make_row(category=""))
    row_errors_51_chars = services._validate_equipment_csv_row(2, _make_row(category="A" * 51))

    assert any(error.error_message == "分類は1〜50文字で入力してください" for error in row_errors_0_chars)
    assert any(error.error_message == "分類は1〜50文字で入力してください" for error in row_errors_51_chars)


# ========== 単体テストNo.9 ==========
# 説明が0文字・500文字の場合はエラーとならず、501文字の場合はエラーとなること
def test_validate_equipment_csv_row_009_description_boundary():
    row_errors_0_chars = services._validate_equipment_csv_row(2, _make_row(description=""))
    row_errors_500_chars = services._validate_equipment_csv_row(2, _make_row(description="A" * 500))
    row_errors_501_chars = services._validate_equipment_csv_row(2, _make_row(description="A" * 501))

    assert row_errors_0_chars == []
    assert row_errors_500_chars == []
    assert any(error.error_message == "説明は500文字以内で入力してください" for error in row_errors_501_chars)


# ========== 単体テストNo.10 ==========
# 保管場所が0文字・100文字の場合はエラーとならず、101文字の場合はエラーとなること
def test_validate_equipment_csv_row_010_location_boundary():
    row_errors_0_chars = services._validate_equipment_csv_row(2, _make_row(location=""))
    row_errors_100_chars = services._validate_equipment_csv_row(2, _make_row(location="A" * 100))
    row_errors_101_chars = services._validate_equipment_csv_row(2, _make_row(location="A" * 101))

    assert row_errors_0_chars == []
    assert row_errors_100_chars == []
    assert any(error.error_message == "保管場所は100文字以内で入力してください" for error in row_errors_101_chars)


# ========== 単体テストNo.11 ==========
# 資産番号・備品名・分類・説明・保管場所のすべてが不正な場合、5件すべてのエラーが返ること
def test_validate_equipment_csv_row_011_all_invalid():
    row = _make_row(
        asset_number="A" * 33,
        name="A" * 101,
        category="A" * 51,
        description="A" * 501,
        location="A" * 101,
    )

    row_errors = services._validate_equipment_csv_row(2, row)

    assert len(row_errors) == 5
    error_messages = {error.error_message for error in row_errors}
    assert error_messages == {
        "資産番号は32文字以内の半角英数字と`-`で入力してください",
        "備品名は1〜100文字で入力してください",
        "分類は1〜50文字で入力してください",
        "説明は500文字以内で入力してください",
        "保管場所は100文字以内で入力してください",
    }


# ========== 単体テストNo.12 ==========
# 資産番号・備品名・分類・説明・保管場所のすべてが正常値の場合、空のエラーリストが返ること
def test_validate_equipment_csv_row_012_all_valid():
    row_errors = services._validate_equipment_csv_row(2, _make_row())

    assert row_errors == []


# ========== 単体テストNo.13 ==========
# 資産番号が半角英数字と`-`のみで1文字（下限値）の場合、エラーとならないこと
def test_validate_equipment_csv_row_013_asset_number_1_char():
    row_errors = services._validate_equipment_csv_row(2, _make_row(asset_number="A"))

    assert row_errors == []


# ==================================================
# 備品CSV一括登録
# テスト対象ファイル：services.py
# テスト対象クラス：-
# テスト対象メソッド：bulk_import_equipment
# テスト仕様書：テスト仕様書/単体テスト仕様書/サーバー処理（main）/備品管理/備品CSV一括登録_単体テスト仕様書.md
# ==================================================


def _build_csv_bytes(header: list[str], data_rows: list[list[str]]) -> bytes:
    # ヘッダー行・データ行からCSVファイル内容（バイト列）を生成する
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(header)
    for data_row in data_rows:
        writer.writerow(data_row)
    return buffer.getvalue().encode("utf-8")


# ========== 単体テストNo.1 ==========
# CSVファイルのサイズが5MBを超える場合、400エラーが発生し解析処理が行われないこと
def test_bulk_import_equipment_001_file_too_large(mocker):
    mocker.patch.object(services.crud, "get_existing_asset_numbers")
    mock_bulk_create = mocker.patch.object(services.crud, "bulk_create_equipments")
    oversized_content = b"a" * (services._EQUIPMENT_CSV_MAX_SIZE + 1)

    with pytest.raises(HTTPException) as exc_info:
        services.bulk_import_equipment(mocker.Mock(), oversized_content)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "ファイルサイズは5MB以内にしてください"
    mock_bulk_create.assert_not_called()


# ========== 単体テストNo.2 ==========
# ヘッダー行の列順が「資産番号・備品名・分類・説明・保管場所」と一致しない場合、400エラーが発生すること
def test_bulk_import_equipment_002_invalid_header(mocker):
    mocker.patch.object(services.crud, "get_existing_asset_numbers", return_value=[])
    swapped_header = ["備品名", "資産番号", "分類", "説明", "保管場所"]
    file_content = _build_csv_bytes(swapped_header, [])

    with pytest.raises(HTTPException) as exc_info:
        services.bulk_import_equipment(mocker.Mock(), file_content)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "CSVのヘッダー列が不正です（資産番号・備品名・分類・説明・保管場所の順で指定してください）"
    )


# ========== 単体テストNo.3 ==========
# ヘッダー行を除いたデータ行数が1,000行を超える場合、400エラーが発生すること
def test_bulk_import_equipment_003_too_many_rows(mocker):
    mocker.patch.object(services.crud, "get_existing_asset_numbers", return_value=[])
    data_rows = [[f"A-{index:04d}", "備品A", "分類A", "説明", "保管場所"] for index in range(1001)]
    file_content = _build_csv_bytes(services._EQUIPMENT_CSV_HEADER, data_rows)

    with pytest.raises(HTTPException) as exc_info:
        services.bulk_import_equipment(mocker.Mock(), file_content)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "データ行数は1,000行以内にしてください"


# ========== 単体テストNo.4 ==========
# ヘッダー行のみ（データ行0件）の場合、エラーとならず0件登録で正常終了すること
def test_bulk_import_equipment_004_no_data_rows(mocker):
    mocker.patch.object(services.crud, "get_existing_asset_numbers", return_value=[])
    mock_bulk_create = mocker.patch.object(services.crud, "bulk_create_equipments", return_value=0)
    file_content = _build_csv_bytes(services._EQUIPMENT_CSV_HEADER, [])

    registered_count = services.bulk_import_equipment(mocker.Mock(), file_content)

    mock_bulk_create.assert_called_once_with(mocker.ANY, [])
    assert registered_count == 0


# ========== 単体テストNo.5 ==========
# いずれかのデータ行の項目形式が不正な場合、エラー一覧に含まれ、登録が中止されること
def test_bulk_import_equipment_005_row_format_error(mocker):
    mocker.patch.object(services.crud, "get_existing_asset_numbers", return_value=[])
    mock_bulk_create = mocker.patch.object(services.crud, "bulk_create_equipments")
    data_rows = [
        ["A-001", "備品A", "分類A", "説明", "保管場所"],
        ["A" * 33, "備品B", "分類B", "説明", "保管場所"],
    ]
    file_content = _build_csv_bytes(services._EQUIPMENT_CSV_HEADER, data_rows)

    with pytest.raises(HTTPException) as exc_info:
        services.bulk_import_equipment(mocker.Mock(), file_content)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == [
        {"row_number": 3, "error_message": "資産番号は32文字以内の半角英数字と`-`で入力してください"}
    ]
    mock_bulk_create.assert_not_called()


# ========== 単体テストNo.6 ==========
# ファイル内の2行が同一の資産番号を持つ場合、重複したすべての行番号がエラー一覧に含まれること
def test_bulk_import_equipment_006_duplicate_in_file(mocker):
    mocker.patch.object(services.crud, "get_existing_asset_numbers", return_value=[])
    data_rows = [
        ["A-001", "備品A", "分類A", "説明", "保管場所"],
        ["A-001", "備品B", "分類B", "説明", "保管場所"],
    ]
    file_content = _build_csv_bytes(services._EQUIPMENT_CSV_HEADER, data_rows)

    with pytest.raises(HTTPException) as exc_info:
        services.bulk_import_equipment(mocker.Mock(), file_content)

    assert exc_info.value.status_code == 400
    error_list = exc_info.value.detail
    assert {"row_number": 2, "error_message": "資産番号がファイル内で重複しています"} in error_list
    assert {"row_number": 3, "error_message": "資産番号がファイル内で重複しています"} in error_list


# ========== 単体テストNo.7 ==========
# ファイル内の資産番号がDBに既に登録済みの場合、該当行番号がエラー一覧に含まれること
def test_bulk_import_equipment_007_duplicate_in_db(mocker):
    mocker.patch.object(services.crud, "get_existing_asset_numbers", return_value=["A-001"])
    data_rows = [["A-001", "備品A", "分類A", "説明", "保管場所"]]
    file_content = _build_csv_bytes(services._EQUIPMENT_CSV_HEADER, data_rows)

    with pytest.raises(HTTPException) as exc_info:
        services.bulk_import_equipment(mocker.Mock(), file_content)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == [{"row_number": 2, "error_message": "資産番号は既に登録されています"}]


# ========== 単体テストNo.8 ==========
# 全データ行が形式・重複ともに検証OKの場合、全行が登録され登録件数が返却されること
def test_bulk_import_equipment_008_success(mocker):
    mocker.patch.object(services.crud, "get_existing_asset_numbers", return_value=[])
    mock_bulk_create = mocker.patch.object(services.crud, "bulk_create_equipments", return_value=2)
    data_rows = [
        ["A-001", "備品A", "分類A", "説明", "保管場所"],
        ["A-002", "備品B", "分類B", "説明", "保管場所"],
    ]
    file_content = _build_csv_bytes(services._EQUIPMENT_CSV_HEADER, data_rows)

    registered_count = services.bulk_import_equipment(mocker.Mock(), file_content)

    import_rows = mock_bulk_create.call_args.args[1]
    assert len(import_rows) == 2
    assert registered_count == 2
