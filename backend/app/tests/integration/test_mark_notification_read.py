from app import crud

# ==================================================
# 通知既読化
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：mark_notification_read_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/共通/通知既読化_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 自分宛の未読通知を既読化できること
def test_mark_notification_read_001_success(client, make_user, login, make_notification_target, db):
    user = make_user("u001", "テスト太郎", "password1")
    token = login("u001", "password1")
    loan_request_id = make_notification_target(user.id)
    notification = crud.create_notification(db, user.id, "new_request", loan_request_id)

    response = client.put(
        f"/notifications/{notification.id}/read",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["is_read"] is True


# ========== 結合テストNo.2 ==========
# 存在しない通知IDを指定した場合、HTTP 404が返却されること
def test_mark_notification_read_002_notification_not_found(client, make_user, login):
    make_user("u002", "テスト次郎", "password1")
    token = login("u002", "password1")

    response = client.put(
        "/notifications/9999/read",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "対象の通知が見つかりませんでした"


# ========== 結合テストNo.3 ==========
# 他ユーザー宛の通知を指定した場合、通知不存在時と同一のメッセージでHTTP 404が返却されること
def test_mark_notification_read_003_other_user_notification(
    client, make_user, login, make_notification_target, db
):
    owner = make_user("u003a", "テスト三郎A", "password1")
    other = make_user("u003b", "テスト三郎B", "password1")
    loan_request_id = make_notification_target(owner.id)
    notification = crud.create_notification(db, other.id, "new_request", loan_request_id)

    token = login("u003a", "password1")
    response = client.put(
        f"/notifications/{notification.id}/read",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "対象の通知が見つかりませんでした"


# ========== 結合テストNo.4 ==========
# 初回パスワード変更未完了のユーザーはアクセスが拒否されること
def test_mark_notification_read_004_must_change_password_forbidden(
    client, make_user, login, make_notification_target, db
):
    user = make_user("u004", "テスト四郎", "password1", must_change_password=True)
    loan_request_id = make_notification_target(user.id)
    notification = crud.create_notification(db, user.id, "new_request", loan_request_id)
    token = login("u004", "password1")

    response = client.put(
        f"/notifications/{notification.id}/read",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.5 ==========
# トークン未指定で既読化した場合、HTTP 401が返却されること
def test_mark_notification_read_005_token_missing(client, make_user, make_notification_target, db):
    user = make_user("u005", "テスト五郎", "password1")
    loan_request_id = make_notification_target(user.id)
    notification = crud.create_notification(db, user.id, "new_request", loan_request_id)

    response = client.put(f"/notifications/{notification.id}/read")

    assert response.status_code == 401


# ========== 結合テストNo.6 ==========
# notification_idに数値以外の文字列を指定した場合、HTTP 422が返却されること
def test_mark_notification_read_006_notification_id_not_numeric(client, make_user, login):
    make_user("u006", "テスト六郎", "password1")
    token = login("u006", "password1")

    response = client.put(
        "/notifications/abc/read",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422
