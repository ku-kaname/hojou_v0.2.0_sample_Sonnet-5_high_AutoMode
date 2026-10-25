# ==================================================
# ヘルスチェック
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：health_check
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/共通/ヘルスチェック_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# DB接続正常時に、HTTP 200で{"status": "ok"}が返却されること
def test_health_check_001_db_connection_ok(client):
    response = client.get("/health-check")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
