# ==================================================
# ユーザー一覧取得
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：get_users_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/ユーザー管理/ユーザー一覧取得_結合テスト仕様書.md
# ==================================================

# 補足：アプリケーション起動時（lifespan）に環境変数ADMIN_USER_ID（既定値"admin"）の
# 初期管理者ユーザーが必ず1件自動作成されるため、各テストの期待値にはこの1件を含めて計算する。


# ========== 結合テストNo.1 ==========
# 複数ユーザーが登録済みの場合、ユーザーID昇順で全件・全フィールドが返却されること
def test_get_users_001_multiple_sorted_asc(client, make_user, login):
    make_user("zzz999", "末尾ユーザー", "password1", role="general")
    make_user("mmm555", "対象ユーザー", "password1", role="general")
    make_user("zadmin1", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("zadmin1", "AdminPass1")

    response = client.get("/users", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    # 初期管理者("admin")を含めた4件が、ユーザーID昇順で返却されることを確認する
    assert [item["user_id"] for item in body] == ["admin", "mmm555", "zadmin1", "zzz999"]

    target = next(item for item in body if item["user_id"] == "mmm555")
    assert target["name"] == "対象ユーザー"
    assert target["department"] is None
    assert target["role"] == "general"
    assert target["is_active"] is True
    assert target["must_change_password"] is False
    assert "created_at" in target
    assert "updated_at" in target


# ========== 結合テストNo.2 ==========
# 管理者権限でないユーザーがアクセスした場合、HTTP 403が返却されること
def test_get_users_002_forbidden_not_admin(client, make_user, login):
    make_user("u002", "一般ユーザー", "password1", role="general")
    token = login("u002", "password1")

    response = client.get("/users", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.3 ==========
# 初回パスワード変更未完了の管理者がアクセスした場合、HTTP 403が返却されること
def test_get_users_003_forbidden_password_not_changed(client, make_user, login):
    make_user("u003", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    token = login("u003", "AdminPass1")

    response = client.get("/users", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.4 ==========
# トークン未指定でアクセスした場合、HTTP 401が返却されること
def test_get_users_004_token_missing(client):
    response = client.get("/users")

    assert response.status_code == 401
