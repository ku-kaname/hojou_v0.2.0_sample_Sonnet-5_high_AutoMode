from datetime import date, timedelta

from app import crud, services

# ==================================================
# 機能横断フロー
# テスト対象ファイル：main.py・services.py
# テスト対象クラス：-
# テスト対象メソッド：create_loan_request_endpoint・approve_loan_request_endpoint・reject_loan_request_endpoint・
#   admin_cancel_loan_request_endpoint・cancel_loan_request_endpoint・lend_loan_request_endpoint・
#   return_loan_request_endpoint・get_my_loan_requests_endpoint・get_overdue_loan_requests_endpoint・
#   get_loan_request_history_endpoint・disable_equipment_endpoint・enable_equipment_endpoint・
#   disable_user_endpoint・auto_cancel_stale_requests・generate_due_reminder_notifications
# テスト仕様書：テスト仕様書/結合テスト仕様書/機能横断/機能横断フロー_結合テスト仕様書.md
# ==================================================
#
# 既存の機能群単位の結合テスト（結合テスト（共通）〜結合テスト（履歴・状況確認））で単一エンドポイントの
# 正常系・異常系は検証済みのため、本ファイルでは複数エンドポイント・複数機能群をまたぐ一連の状態遷移・
# データ整合性・通知生成のみを対象とする。ノーショー自動取消・期限通知生成はHTTPエンドポイントを持たない
# 日次バッチ本体のため、servicesモジュールの関数を直接呼び出す。


# ========== 結合テストNo.1 ==========
# 申請から返却までの一連のライフサイクルで、各段階の状態・担当者名・通知が整合すること
def test_cross_functional_flows_001_full_lifecycle(client, make_user, make_equipment, login, db):
    applicant = make_user("applicant001", "申請者太郎", "password1")
    admin = make_user("admin001", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_equipment(name="テストPC", asset_number="AST-CF-001")
    today = date.today()

    # ①一般ユーザーでログイン
    applicant_token = login("applicant001", "password1")

    # ②備品検索で対象備品を確認する
    search_response = client.get(
        "/equipment",
        params={"keyword": "テストPC"},
        headers={"Authorization": f"Bearer {applicant_token}"},
    )
    assert search_response.status_code == 200
    assert any(item["asset_number"] == "AST-CF-001" for item in search_response.json())

    # ③貸出申請する
    create_response = client.post(
        "/loan-requests",
        headers={"Authorization": f"Bearer {applicant_token}"},
        json={
            "asset_number": "AST-CF-001",
            "start_date": today.isoformat(),
            "due_date": (today + timedelta(days=9)).isoformat(),
            "purpose": "機能横断テスト用途",
        },
    )
    assert create_response.status_code == 200
    loan_request_id = create_response.json()["id"]

    # ③の直後、有効な管理者全員宛に種別"new_request"の通知が生成されていること
    admin_notifications = crud.get_notifications_by_recipient(db, admin.id)
    assert len(admin_notifications) == 1
    assert admin_notifications[0].notification_type == "new_request"
    assert admin_notifications[0].loan_request_id == loan_request_id

    # ④管理者でログイン
    admin_token = login("admin001", "AdminPass1")

    # ⑤申請承認する
    approve_response = client.put(
        f"/loan-requests/{loan_request_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert approve_response.status_code == 200

    # ⑤の直後、申請者宛に種別"approved"の通知が生成されていること
    applicant_notifications = crud.get_notifications_by_recipient(db, applicant.id)
    assert len(applicant_notifications) == 1
    assert applicant_notifications[0].notification_type == "approved"

    # ⑥貸出処理する
    lend_response = client.put(
        f"/loan-requests/{loan_request_id}/lend",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert lend_response.status_code == 200

    # ⑦返却処理する
    return_response = client.put(
        f"/loan-requests/{loan_request_id}/return",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={},
    )
    assert return_response.status_code == 200

    # ⑧自分申請一覧取得で、status="returned"・lent_at・returned_atが設定されていること
    my_requests_response = client.get("/loan-requests", headers={"Authorization": f"Bearer {applicant_token}"})
    assert my_requests_response.status_code == 200
    my_request = my_requests_response.json()[0]
    assert my_request["id"] == loan_request_id
    assert my_request["status"] == "returned"
    assert my_request["lent_at"] is not None
    assert my_request["returned_at"] is not None

    # ⑧貸出履歴検索・取得で、approved_by_name・lent_by_name・returned_by_nameが
    # それぞれ操作した管理者の氏名と一致すること
    history_response = client.get("/loan-requests/all", headers={"Authorization": f"Bearer {admin_token}"})
    assert history_response.status_code == 200
    history_item = history_response.json()[0]
    assert history_item["id"] == loan_request_id
    assert history_item["approved_by_name"] == "テスト管理者"
    assert history_item["lent_by_name"] == "テスト管理者"
    assert history_item["returned_by_name"] == "テスト管理者"


# ========== 結合テストNo.2 ==========
# 却下フローで自分申請一覧・通知が整合すること
def test_cross_functional_flows_002_reject_flow(client, make_user, make_equipment, login, db):
    applicant = make_user("applicant002", "申請者太郎", "password1")
    make_user("admin002", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_equipment(asset_number="AST-CF-002")

    applicant_token = login("applicant002", "password1")

    # ①貸出申請する
    create_response = client.post(
        "/loan-requests",
        headers={"Authorization": f"Bearer {applicant_token}"},
        json={
            "asset_number": "AST-CF-002",
            "start_date": "2026-11-01",
            "due_date": "2026-11-10",
            "purpose": "機能横断テスト用途",
        },
    )
    loan_request_id = create_response.json()["id"]

    # ②管理者で申請却下する
    admin_token = login("admin002", "AdminPass1")
    reject_response = client.put(
        f"/loan-requests/{loan_request_id}/reject",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"rejection_reason": "在庫調整のため却下"},
    )
    assert reject_response.status_code == 200

    # ②の直後、申請者宛に種別"rejected"の通知が1件生成されていること
    notifications = crud.get_notifications_by_recipient(db, applicant.id)
    assert len(notifications) == 1
    assert notifications[0].notification_type == "rejected"
    assert notifications[0].loan_request_id == loan_request_id

    # ③自分申請一覧でstatus="rejected"・rejection_reasonが②の却下理由と一致すること
    my_requests_response = client.get("/loan-requests", headers={"Authorization": f"Bearer {applicant_token}"})
    my_request = my_requests_response.json()[0]
    assert my_request["status"] == "rejected"
    assert my_request["rejection_reason"] == "在庫調整のため却下"


# ========== 結合テストNo.3 ==========
# 本人による申請取消は、貸出履歴で取消者が申請者自身になり、通知が生成されないこと
def test_cross_functional_flows_003_self_cancel_flow(client, make_user, make_equipment, login, db):
    applicant = make_user("applicant003", "申請者太郎", "password1")
    make_user("admin003", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_equipment(asset_number="AST-CF-003")

    applicant_token = login("applicant003", "password1")

    # ①貸出申請する
    create_response = client.post(
        "/loan-requests",
        headers={"Authorization": f"Bearer {applicant_token}"},
        json={
            "asset_number": "AST-CF-003",
            "start_date": "2026-11-01",
            "due_date": "2026-11-10",
            "purpose": "機能横断テスト用途",
        },
    )
    loan_request_id = create_response.json()["id"]

    # ②同一ユーザーで申請取消する
    cancel_response = client.put(
        f"/loan-requests/{loan_request_id}/cancel",
        headers={"Authorization": f"Bearer {applicant_token}"},
    )
    assert cancel_response.status_code == 200

    # 申請者宛に通知が生成されていないこと（本人による取消は通知対象外）
    notifications = crud.get_notifications_by_recipient(db, applicant.id)
    assert len(notifications) == 0

    # ③管理者で貸出履歴検索・取得し、status="cancelled"・cancelled_by_nameが申請者自身の氏名と一致すること
    admin_token = login("admin003", "AdminPass1")
    history_response = client.get("/loan-requests/all", headers={"Authorization": f"Bearer {admin_token}"})
    history_item = history_response.json()[0]
    assert history_item["status"] == "cancelled"
    assert history_item["cancelled_by_name"] == "申請者太郎"


# ========== 結合テストNo.4 ==========
# 管理者による申請取消は、貸出履歴で取消者が管理者になり、申請者へ通知が生成されること
def test_cross_functional_flows_004_admin_cancel_flow(client, make_user, make_loan_request, login, db):
    applicant = make_user("applicant004", "申請者太郎", "password1")
    make_user("admin004", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    loan_request = make_loan_request(
        applicant.id, status="approved", start_date=date(2026, 11, 1), due_date=date(2026, 11, 10)
    )

    # ①管理者で管理者申請取消する
    admin_token = login("admin004", "AdminPass1")
    admin_cancel_response = client.put(
        f"/loan-requests/{loan_request.id}/admin-cancel",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"cancellation_reason": "備品メンテナンスのため取消"},
    )
    assert admin_cancel_response.status_code == 200

    # ①の直後、申請者宛に種別"cancelled"の通知が1件生成されていること
    notifications = crud.get_notifications_by_recipient(db, applicant.id)
    assert len(notifications) == 1
    assert notifications[0].notification_type == "cancelled"

    # ②自分申請一覧・貸出履歴の両方でstatus="cancelled"、
    # 貸出履歴のcancelled_by_nameが取消した管理者の氏名と一致すること
    applicant_token = login("applicant004", "password1")
    my_requests_response = client.get("/loan-requests", headers={"Authorization": f"Bearer {applicant_token}"})
    assert my_requests_response.json()[0]["status"] == "cancelled"

    history_response = client.get("/loan-requests/all", headers={"Authorization": f"Bearer {admin_token}"})
    history_item = history_response.json()[0]
    assert history_item["status"] == "cancelled"
    assert history_item["cancelled_by_name"] == "テスト管理者"


# ========== 結合テストNo.5 ==========
# ノーショー自動取消バッチにより、承認済みのまま放置された申請が自分申請一覧上で取消済みに変化し、
# 通知が生成されること
def test_cross_functional_flows_005_auto_cancel_batch_flow(client, make_user, make_loan_request, login, db):
    applicant = make_user("applicant005", "申請者太郎", "password1")
    make_user("admin005", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    today = date.today()
    loan_request = make_loan_request(
        applicant.id,
        status="approved",
        start_date=today - timedelta(days=10),
        due_date=today - timedelta(days=1),
    )

    applicant_token = login("applicant005", "password1")

    # ①自分申請一覧取得で事前状態（status="approved"）を確認する
    before_response = client.get("/loan-requests", headers={"Authorization": f"Bearer {applicant_token}"})
    assert before_response.json()[0]["status"] == "approved"

    # ②ノーショー自動取消バッチを実行する
    services.auto_cancel_stale_requests(db)

    # ②の直後、申請者宛に種別"cancelled"の通知が1件生成されていること
    notifications = crud.get_notifications_by_recipient(db, applicant.id)
    assert len(notifications) == 1
    assert notifications[0].notification_type == "cancelled"
    assert notifications[0].loan_request_id == loan_request.id

    # ③自分申請一覧取得で、status="cancelled"に変化していること
    after_response = client.get("/loan-requests", headers={"Authorization": f"Bearer {applicant_token}"})
    assert after_response.json()[0]["status"] == "cancelled"


# ========== 結合テストNo.6 ==========
# 期限超過一覧・期限通知生成バッチ・返却処理が連携すること
def test_cross_functional_flows_006_overdue_due_reminder_return_flow(client, make_user, make_loan_request, login, db):
    applicant = make_user("applicant006", "申請者太郎", "password1")
    admin = make_user("admin006", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    today = date.today()
    loan_request = make_loan_request(
        applicant.id,
        status="approved",
        start_date=today - timedelta(days=10),
        due_date=today - timedelta(days=1),
    )
    crud.lend_loan_request(db, loan_request.id, admin.id)

    admin_token = login("admin006", "AdminPass1")

    # ①期限超過一覧取得で対象申請が含まれることを確認する
    overdue_before_response = client.get("/loan-requests/overdue", headers={"Authorization": f"Bearer {admin_token}"})
    assert overdue_before_response.status_code == 200
    assert any(item["id"] == loan_request.id for item in overdue_before_response.json())

    # ②期限通知生成バッチを実行する
    services.generate_due_reminder_notifications(db)

    # ②の直後、申請者宛に種別"due_reminder"の通知が1件生成されていること
    notifications = crud.get_notifications_by_recipient(db, applicant.id)
    assert len(notifications) == 1
    assert notifications[0].notification_type == "due_reminder"
    assert notifications[0].loan_request_id == loan_request.id

    # ③管理者が返却処理を実行する
    return_response = client.put(
        f"/loan-requests/{loan_request.id}/return",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={},
    )
    assert return_response.status_code == 200

    # ④期限超過一覧取得で対象申請が一覧から除外されていること
    overdue_after_response = client.get("/loan-requests/overdue", headers={"Authorization": f"Bearer {admin_token}"})
    assert all(item["id"] != loan_request.id for item in overdue_after_response.json())


# ========== 結合テストNo.7 ==========
# 備品無効化中は新規申請が拒否され、再有効化後は申請できるようになること
def test_cross_functional_flows_007_equipment_disable_blocks_new_request(client, make_user, make_equipment, login):
    make_user("applicant007", "申請者太郎", "password1")
    make_user("admin007", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    equipment = make_equipment(asset_number="AST-CF-007")

    admin_token = login("admin007", "AdminPass1")
    applicant_token = login("applicant007", "password1")

    # ①管理者で備品無効化する
    disable_response = client.put(
        f"/equipment/{equipment.asset_number}/disable",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert disable_response.status_code == 200

    # ②一般ユーザーで同一資産番号へ貸出申請し、HTTP 404が返却されることを確認する
    create_response_disabled = client.post(
        "/loan-requests",
        headers={"Authorization": f"Bearer {applicant_token}"},
        json={
            "asset_number": "AST-CF-007",
            "start_date": "2026-11-01",
            "due_date": "2026-11-10",
            "purpose": "機能横断テスト用途",
        },
    )
    assert create_response_disabled.status_code == 404
    assert create_response_disabled.json()["detail"] == "備品が見つかりません"

    # ③管理者で備品再有効化する
    enable_response = client.put(
        f"/equipment/{equipment.asset_number}/enable",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert enable_response.status_code == 200

    # ④一般ユーザーで同一資産番号へ貸出申請し、HTTP 200・status="pending"で登録されることを確認する
    create_response_enabled = client.post(
        "/loan-requests",
        headers={"Authorization": f"Bearer {applicant_token}"},
        json={
            "asset_number": "AST-CF-007",
            "start_date": "2026-11-01",
            "due_date": "2026-11-10",
            "purpose": "機能横断テスト用途",
        },
    )
    assert create_response_enabled.status_code == 200
    assert create_response_enabled.json()["status"] == "pending"


# ========== 結合テストNo.8 ==========
# ユーザー無効化により、発行済みトークンが直後に無効化され、再ログインもできなくなること
def test_cross_functional_flows_008_user_disable_invalidates_token(client, make_user, login):
    make_user("applicant008", "申請者太郎", "password1")
    make_user("admin008", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)

    # ①一般ユーザーでログインしアクセストークンを取得する
    applicant_token = login("applicant008", "password1")

    # ②①のトークンで自分情報取得に成功することを確認する
    before_response = client.get("/me", headers={"Authorization": f"Bearer {applicant_token}"})
    assert before_response.status_code == 200

    # ③管理者で対象ユーザーを無効化する
    admin_token = login("admin008", "AdminPass1")
    disable_response = client.put(
        "/users/applicant008/disable",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert disable_response.status_code == 200

    # ④①で取得済みの同一トークンで自分情報取得し、HTTP 401（トークン世代不一致による即時失効）が
    # 返却されることを確認する
    after_response = client.get("/me", headers={"Authorization": f"Bearer {applicant_token}"})
    assert after_response.status_code == 401
    assert after_response.json()["detail"] == "資格情報を検証できませんでした"

    # ⑤同一ユーザーID・パスワードで再ログインし、HTTP 401が返却されることを確認する
    relogin_response = client.post("/token", json={"user_id": "applicant008", "password": "password1"})
    assert relogin_response.status_code == 401
    assert relogin_response.json()["detail"] == "ユーザーIDまたはパスワードが正しくありません"


# ========== 結合テストNo.9 ==========
# 同一備品への重複期間申請は作成時点では許可され、承認時点で拒否されること
def test_cross_functional_flows_009_overlap_allowed_on_create_rejected_on_approve(
    client, make_user, make_equipment, login
):
    make_user("applicantA009", "申請者A", "password1")
    make_user("applicantB009", "申請者B", "password1")
    make_user("admin009", "テスト管理者", "AdminPass1", role="admin", must_change_password=False)
    make_equipment(asset_number="AST-CF-009")

    admin_token = login("admin009", "AdminPass1")

    # ①申請者Aが期間Xで貸出申請する
    token_a = login("applicantA009", "password1")
    create_response_a = client.post(
        "/loan-requests",
        headers={"Authorization": f"Bearer {token_a}"},
        json={
            "asset_number": "AST-CF-009",
            "start_date": "2026-11-01",
            "due_date": "2026-11-10",
            "purpose": "申請者A用途",
        },
    )
    loan_request_id_a = create_response_a.json()["id"]

    # ②申請者Bが①と重複する期間で同一備品へ貸出申請し、
    # HTTP 200・status="pending"で登録されることを確認する（作成時の重複チェックは
    # 承認済み・貸出中のみが対象のため、申請中同士は重複可能。この時点では①もpendingのため重複可能）
    token_b = login("applicantB009", "password1")
    create_response_b = client.post(
        "/loan-requests",
        headers={"Authorization": f"Bearer {token_b}"},
        json={
            "asset_number": "AST-CF-009",
            "start_date": "2026-11-05",
            "due_date": "2026-11-14",
            "purpose": "申請者B用途",
        },
    )
    assert create_response_b.status_code == 200
    assert create_response_b.json()["status"] == "pending"
    loan_request_id_b = create_response_b.json()["id"]

    # ③管理者が①を承認する
    approve_response_a = client.put(
        f"/loan-requests/{loan_request_id_a}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert approve_response_a.status_code == 200

    # ④管理者が②を承認しようとし、HTTP 400（指定した期間は既に貸出予定があります）で
    # 拒否されることを確認する（承認済みとなった①と重複するため）
    approve_response_b = client.put(
        f"/loan-requests/{loan_request_id_b}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert approve_response_b.status_code == 400
    assert approve_response_b.json()["detail"] == "指定した期間は既に貸出予定があります"
