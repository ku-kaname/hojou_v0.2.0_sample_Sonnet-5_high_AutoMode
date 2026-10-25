from app import services

# ==================================================
# CSV数式注入対策
# テスト対象ファイル：services.py
# テスト対象クラス：-
# テスト対象メソッド：_escape_csv_injection
# テスト仕様書：テスト仕様書/単体テスト仕様書/サーバー処理（main）/履歴・状況確認/CSV数式注入対策_単体テスト仕様書.md
# ==================================================


# ========== 単体テストNo.1 ==========
# 先頭文字が`=`の場合、先頭に`'`が付与されること
def test_escape_csv_injection_001_leading_equal():
    result = services._escape_csv_injection("=SUM(A1:A2)")

    assert result == "'=SUM(A1:A2)"


# ========== 単体テストNo.2 ==========
# 先頭文字が`+`の場合、先頭に`'`が付与されること
def test_escape_csv_injection_002_leading_plus():
    result = services._escape_csv_injection("+81-00-0000")

    assert result == "'+81-00-0000"


# ========== 単体テストNo.3 ==========
# 先頭文字が`-`の場合、先頭に`'`が付与されること
def test_escape_csv_injection_003_leading_minus():
    result = services._escape_csv_injection("-1+1")

    assert result == "'-1+1"


# ========== 単体テストNo.4 ==========
# 先頭文字が`@`の場合、先頭に`'`が付与されること
def test_escape_csv_injection_004_leading_at():
    result = services._escape_csv_injection("@SUM(1)")

    assert result == "'@SUM(1)"


# ========== 単体テストNo.5 ==========
# 先頭文字が`=`・`+`・`-`・`@`のいずれにも該当しない場合、値が変更されないこと
def test_escape_csv_injection_005_normal_text():
    result = services._escape_csv_injection("備品A")

    assert result == "備品A"


# ========== 単体テストNo.6 ==========
# 空文字の場合、`'`が付与されず変更されないこと
def test_escape_csv_injection_006_empty_string():
    result = services._escape_csv_injection("")

    assert result == ""
