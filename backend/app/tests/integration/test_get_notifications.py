from datetime import datetime

from app import crud

# ==================================================
# 通知一覧取得
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：get_notifications_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/共通/通知一覧取得_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 複数件の通知が作成日時の降順（新しい順）で返却されること
def test_get_notifications_001_multiple_sorted_desc(client, make_user, login, make_notification_target, db):
    user = make_user("u001", "テスト太郎", "password1")
    token = login("u001", "password1")
    loan_request_id = make_notification_target(user.id)

    notification_old = crud.create_notification(db, user.id, "new_request", loan_request_id)
    notification_old.created_at = datetime(2026, 10, 20, 9, 0, 0)
    notification_mid = crud.create_notification(db, user.id, "approved", loan_request_id)
    notification_mid.created_at = datetime(2026, 10, 21, 9, 0, 0)
    notification_new = crud.create_notification(db, user.id, "rejected", loan_request_id)
    notification_new.created_at = datetime(2026, 10, 22, 9, 0, 0)
    db.commit()

    response = client.get("/notifications", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert ids == [notification_new.id, notification_mid.id, notification_old.id]


# ========== 結合テストNo.2 ==========
# 通知が0件の場合、空リストが返却されること
def test_get_notifications_002_empty_list(client, make_user, login):
    make_user("u002", "テスト次郎", "password1")
    token = login("u002", "password1")

    response = client.get("/notifications", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == []


# ========== 結合テストNo.3 ==========
# 自分宛の通知1件・他ユーザー宛の通知1件が登録済みの場合、自分宛の1件のみが返却されること
def test_get_notifications_003_other_user_excluded(client, make_user, login, make_notification_target, db):
    owner = make_user("u003a", "テスト三郎A", "password1")
    other = make_user("u003b", "テスト三郎B", "password1")
    loan_request_id = make_notification_target(owner.id)
    own_notification = crud.create_notification(db, owner.id, "new_request", loan_request_id)
    crud.create_notification(db, other.id, "new_request", loan_request_id)

    token = login("u003a", "password1")
    response = client.get("/notifications", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == own_notification.id


# ========== 結合テストNo.4 ==========
# 初回パスワード変更未完了のユーザーはアクセスが拒否されること
def test_get_notifications_004_must_change_password_forbidden(client, make_user, login):
    make_user("u004", "テスト四郎", "password1", must_change_password=True)
    token = login("u004", "password1")

    response = client.get("/notifications", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.5 ==========
# トークン未指定で取得した場合、HTTP 401が返却されること
def test_get_notifications_005_token_missing(client):
    response = client.get("/notifications")

    assert response.status_code == 401
