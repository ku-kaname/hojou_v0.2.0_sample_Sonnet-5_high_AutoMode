# ==================================================
# 申請取消
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：cancel_loan_request_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/貸出申請・承認/申請取消_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 申請中の自分の申請を取消した場合、HTTP 200でstatus="cancelled"が返却されること
def test_cancel_loan_request_endpoint_001_cancel_pending_request(client, make_user, make_loan_request, login):
    user = make_user("u001", "一般ユーザー", "password1")
    loan_request = make_loan_request(user.id, status="pending")
    token = login("u001", "password1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


# ========== 結合テストNo.2 ==========
# 承認済みの自分の申請を取消した場合、HTTP 200でstatus="cancelled"が返却されること
def test_cancel_loan_request_endpoint_002_cancel_approved_request(client, make_user, make_loan_request, login):
    user = make_user("u002", "一般ユーザー", "password1")
    loan_request = make_loan_request(user.id, status="approved")
    token = login("u002", "password1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


# ========== 結合テストNo.3 ==========
# 存在しない内部IDを指定した場合、HTTP 404が返却されること
def test_cancel_loan_request_endpoint_003_not_found(client, make_user, login):
    make_user("u003", "一般ユーザー", "password1")
    token = login("u003", "password1")

    response = client.put(
        "/loan-requests/99999/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "貸出申請が見つかりません"


# ========== 結合テストNo.4 ==========
# 他人の申請中の申請を取消しようとした場合、存在しない場合と同一のHTTP 404が返却されること（存在秘匿）
def test_cancel_loan_request_endpoint_004_other_user_request_hidden(client, make_user, make_loan_request, login):
    make_user("userA004", "ユーザーA", "password1")
    user_b = make_user("userB004", "ユーザーB", "password1")
    loan_request = make_loan_request(user_b.id, status="pending")
    token = login("userA004", "password1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "貸出申請が見つかりません"


# ========== 結合テストNo.5 ==========
# 却下済みの自分の申請を取消しようとした場合、HTTP 400が返却されること
def test_cancel_loan_request_endpoint_005_rejected_request(client, make_user, make_loan_request, login):
    user = make_user("u005", "一般ユーザー", "password1")
    loan_request = make_loan_request(user.id, status="rejected")
    token = login("u005", "password1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "この申請は取消できません"


# ========== 結合テストNo.6 ==========
# 貸出中の自分の申請を取消しようとした場合、HTTP 400が返却されること
def test_cancel_loan_request_endpoint_006_lending_request(client, make_user, make_loan_request, login):
    user = make_user("u006", "一般ユーザー", "password1")
    loan_request = make_loan_request(user.id, status="lending")
    token = login("u006", "password1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "この申請は取消できません"


# ========== 結合テストNo.7 ==========
# 取消済みの自分の申請を再度取消しようとした場合、HTTP 400が返却されること
def test_cancel_loan_request_endpoint_007_already_cancelled_request(client, make_user, make_loan_request, login):
    user = make_user("u007", "一般ユーザー", "password1")
    loan_request = make_loan_request(user.id, status="cancelled")
    token = login("u007", "password1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "この申請は取消できません"


# ========== 結合テストNo.8 ==========
# 初回パスワード変更未完了のユーザーが取消する場合、HTTP 403が返却されること
def test_cancel_loan_request_endpoint_008_forbidden_password_not_changed(
    client, make_user, make_loan_request, login
):
    user = make_user("u008", "一般ユーザー", "password1", must_change_password=True)
    loan_request = make_loan_request(user.id, status="pending")
    token = login("u008", "password1")

    response = client.put(
        f"/loan-requests/{loan_request.id}/cancel",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "初回パスワードの変更が完了していません。パスワードを変更してください"


# ========== 結合テストNo.9 ==========
# トークン未指定で取消する場合、HTTP 401が返却されること
def test_cancel_loan_request_endpoint_009_token_missing(client, make_user, make_loan_request):
    user = make_user("u009", "一般ユーザー", "password1")
    loan_request = make_loan_request(user.id, status="pending")

    response = client.put(f"/loan-requests/{loan_request.id}/cancel")

    assert response.status_code == 401
