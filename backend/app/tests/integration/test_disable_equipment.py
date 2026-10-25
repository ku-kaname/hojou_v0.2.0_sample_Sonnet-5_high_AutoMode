# ==================================================
# 備品無効化
# テスト対象ファイル：main.py
# テスト対象クラス：-
# テスト対象メソッド：disable_equipment_endpoint
# テスト仕様書：テスト仕様書/結合テスト仕様書/サーバー処理（main）/備品管理/備品無効化_結合テスト仕様書.md
# ==================================================


# ========== 結合テストNo.1 ==========
# 申請が存在しない有効な備品を無効化した場合、HTTP 200・is_active=falseとなること
def test_disable_equipment_001_disable_without_requests(client, make_user, make_equipment, login):
    make_user("admin01", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    equipment = make_equipment()
    token = login("admin01", "AdminPass1")

    response = client.put(f"/equipment/{equipment.asset_number}/disable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["is_active"] is False


# ========== 結合テストNo.2 ==========
# 返却済み（returned）の申請のみが存在する備品は無効化できること
def test_disable_equipment_002_returned_request_allows_disable(
    client, make_user, make_equipment, make_loan_request, login
):
    make_user("admin02", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("u02", "一般ユーザー", "password1", role="general")
    equipment = make_equipment()
    make_loan_request(applicant.id, status="returned", equipment_internal_id=equipment.id)
    token = login("admin02", "AdminPass1")

    response = client.put(f"/equipment/{equipment.asset_number}/disable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["is_active"] is False


# ========== 結合テストNo.3 ==========
# 却下済み（rejected）の申請のみが存在する備品は無効化できること
def test_disable_equipment_003_rejected_request_allows_disable(
    client, make_user, make_equipment, make_loan_request, login
):
    make_user("admin03", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("u03", "一般ユーザー", "password1", role="general")
    equipment = make_equipment()
    make_loan_request(applicant.id, status="rejected", equipment_internal_id=equipment.id)
    token = login("admin03", "AdminPass1")

    response = client.put(f"/equipment/{equipment.asset_number}/disable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["is_active"] is False


# ========== 結合テストNo.4 ==========
# 取消済み（cancelled）の申請のみが存在する備品は無効化できること
def test_disable_equipment_004_cancelled_request_allows_disable(
    client, make_user, make_equipment, make_loan_request, login
):
    make_user("admin04", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("u04", "一般ユーザー", "password1", role="general")
    equipment = make_equipment()
    make_loan_request(applicant.id, status="cancelled", equipment_internal_id=equipment.id)
    token = login("admin04", "AdminPass1")

    response = client.put(f"/equipment/{equipment.asset_number}/disable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["is_active"] is False


# ========== 結合テストNo.5 ==========
# 申請中（pending）の申請が存在する場合、HTTP 400が返却され、is_active=trueが維持されること
def test_disable_equipment_005_pending_request_blocks_disable(
    client, make_user, make_equipment, make_loan_request, login, db
):
    make_user("admin05", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("u05", "一般ユーザー", "password1", role="general")
    equipment = make_equipment()
    make_loan_request(applicant.id, status="pending", equipment_internal_id=equipment.id)
    token = login("admin05", "AdminPass1")

    response = client.put(f"/equipment/{equipment.asset_number}/disable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 400
    assert response.json()["detail"] == "申請中・承認済み・貸出中の申請があるため無効化できません"
    db.refresh(equipment)
    assert equipment.is_active is True


# ========== 結合テストNo.6 ==========
# 承認済み（approved）の申請が存在する場合、HTTP 400が返却されること
def test_disable_equipment_006_approved_request_blocks_disable(
    client, make_user, make_equipment, make_loan_request, login
):
    make_user("admin06", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("u06", "一般ユーザー", "password1", role="general")
    equipment = make_equipment()
    make_loan_request(applicant.id, status="approved", equipment_internal_id=equipment.id)
    token = login("admin06", "AdminPass1")

    response = client.put(f"/equipment/{equipment.asset_number}/disable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 400
    assert response.json()["detail"] == "申請中・承認済み・貸出中の申請があるため無効化できません"


# ========== 結合テストNo.7 ==========
# 貸出中（lending）の申請が存在する場合、HTTP 400が返却されること
def test_disable_equipment_007_lending_request_blocks_disable(
    client, make_user, make_equipment, make_loan_request, login
):
    make_user("admin07", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    applicant = make_user("u07", "一般ユーザー", "password1", role="general")
    equipment = make_equipment()
    make_loan_request(applicant.id, status="lending", equipment_internal_id=equipment.id)
    token = login("admin07", "AdminPass1")

    response = client.put(f"/equipment/{equipment.asset_number}/disable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 400
    assert response.json()["detail"] == "申請中・承認済み・貸出中の申請があるため無効化できません"


# ========== 結合テストNo.8 ==========
# 既に無効化済みの備品を無効化した場合、HTTP 400が返却されること
def test_disable_equipment_008_already_disabled(client, make_user, make_equipment, login):
    make_user("admin08", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    equipment = make_equipment(is_active=False)
    token = login("admin08", "AdminPass1")

    response = client.put(f"/equipment/{equipment.asset_number}/disable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 400
    assert response.json()["detail"] == "既に無効化されています"


# ========== 結合テストNo.9 ==========
# 存在しない資産番号を指定した場合、HTTP 404が返却されること
def test_disable_equipment_009_not_found(client, make_user, login):
    make_user("admin09", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    token = login("admin09", "AdminPass1")

    response = client.put("/equipment/未登録資産番号/disable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404
    assert response.json()["detail"] == "備品が見つかりません"


# ========== 結合テストNo.10 ==========
# 管理者権限でないユーザーが無効化した場合、HTTP 403が返却されること
def test_disable_equipment_010_forbidden_not_admin(client, make_user, make_equipment, login):
    make_user("u010", "一般ユーザー", "password1", role="general")
    equipment = make_equipment()
    token = login("u010", "password1")

    response = client.put(f"/equipment/{equipment.asset_number}/disable", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == "この操作には管理者権限が必要です"
