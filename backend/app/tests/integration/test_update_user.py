from app import crud

# ==================================================
# ユーザー編集
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：update_user_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/ユーザー管理/ユーザー編集_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# ロールを変更せずに氏名・所属を変更した場合、更新内容が反映され、トークン世代は変更されないこと
def test_update_user_001_update_without_role_change(client, make_user, login):
    make_user("admin01", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_user("target01", "変更前太郎", "password1", role="general")
    admin_token = login("admin01", "AdminPass1")
    old_token = login("target01", "password1")

    response = client.put(
        "/users/target01",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "変更後太郎", "department": "営業部", "role": "general"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "変更後太郎"
    assert body["department"] == "営業部"

    old_token_response = client.get("/me", headers={"Authorization": f"Bearer {old_token}"})
    assert old_token_response.status_code == 200


# ========== 結合テストNo.2 ==========
# ロールを変更した場合、トークン世代が更新され旧トークンが失効すること
def test_update_user_002_update_with_role_change_revokes_old_token(client, make_user, login):
    make_user("admin02", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_user("target02", "変更前次郎", "password1", role="general")
    admin_token = login("admin02", "AdminPass1")
    old_token = login("target02", "password1")

    response = client.put(
        "/users/target02",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "変更後次郎", "department": "営業部", "role": "admin"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "admin"

    old_token_response = client.get("/me", headers={"Authorization": f"Bearer {old_token}"})
    assert old_token_response.status_code == 401
    assert old_token_response.json()["detail"] == "資格情報を検証できませんでした"


# ========== 結合テストNo.3 ==========
# 最後の有効な管理者を一般ユーザーに変更しようとした場合、HTTP 400が返却されること
def test_update_user_003_last_admin_cannot_demote(client, db, login):
    # アプリケーション起動時（lifespan）に自動作成される初期管理者("admin")を
    # 唯一の有効な管理者として利用する。初期管理者はmust_change_password=trueで作成されるため、
    # ログインしてAPIを呼び出せるように直接falseへ変更する
    admin = crud.get_user_by_user_id(db, "admin")
    admin.must_change_password = False
    db.commit()
    token = login("admin", "AdminInitPass1")

    response = client.put(
        "/users/admin",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "システム管理者", "department": None, "role": "general"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "最後の管理者を一般ユーザーに変更することはできません"


# ========== 結合テストNo.4 ==========
# 有効な管理者が複数いる場合、管理者を一般ユーザーに変更できること
def test_update_user_004_demote_admin_when_multiple_admins_exist(client, make_user, login):
    # 初期管理者("admin")に加えて、もう1名の管理者を作成するため、合計2名の有効な管理者が存在する状態になる
    make_user("admin04", "追加管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin04", "AdminPass1")

    response = client.put(
        "/users/admin04",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "元管理者", "department": None, "role": "general"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "general"


# ========== 結合テストNo.5 ==========
# 存在しないユーザーIDを指定した場合、HTTP 404が返却されること
def test_update_user_005_not_found(client, make_user, login):
    make_user("admin05", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin05", "AdminPass1")

    response = client.put(
        "/users/notfounduser",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "テスト", "department": None, "role": "general"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "ユーザーが見つかりません"


# ========== 結合テストNo.6 ==========
# 管理者権限でないユーザーが編集した場合、HTTP 403が返却されること
def test_update_user_006_forbidden_not_admin(client, make_user, login):
    make_user("u006", "一般ユーザー", "password1", role="general")
    token = login("u006", "password1")

    response = client.put(
        "/users/u006",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "テスト", "department": None, "role": "general"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"


# ========== 結合テストNo.7 ==========
# 初回パスワード変更未完了の管理者が編集した場合、HTTP 403が返却されること
def test_update_user_007_forbidden_password_not_changed(client, make_user, login):
    make_user("admin07", "未変更管理者", "AdminPass1", role="admin", must_change_password=True)
    token = login("admin07", "AdminPass1")

    response = client.put(
        "/users/admin07",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "テスト", "department": None, "role": "admin"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.8 ==========
# トークン未指定で編集した場合、HTTP 401が返却されること
def test_update_user_008_token_missing(client, make_user):
    make_user("admin08", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)

    response = client.put(
        "/users/admin08",
        json={"name": "テスト", "department": None, "role": "admin"},
    )

    assert response.status_code == 401


# ========== 結合テストNo.9 ==========
# 必須パラメータ（name）が欠落している場合、HTTP 422が返却されること
def test_update_user_009_missing_required_name(client, make_user, login):
    make_user("admin09", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_user("target09", "対象ユーザー", "password1", role="general")
    token = login("admin09", "AdminPass1")

    response = client.put(
        "/users/target09",
        headers={"Authorization": f"Bearer {token}"},
        json={"department": None, "role": "general"},
    )

    assert response.status_code == 422
