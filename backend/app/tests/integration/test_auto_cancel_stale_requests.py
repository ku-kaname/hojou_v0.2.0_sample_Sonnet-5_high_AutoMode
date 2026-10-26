from datetime import date, timedelta

from app import crud, services

# ==================================================
# ノーショー自動取消
# テスト対象ファイル：services.py
# テスト対象クラス：-
# テスト対象メソッド：auto_cancel_stale_requests
# テスト仕様書：テスト仕様書/結合テスト仕様書/オーケストレーション処理（services）/貸出・返却/ノーショー自動取消_結合テスト仕様書.md
# ==================================================
#
# HTTPエンドポイントを持たない日次バッチ本体のため、TestClient（HTTP経由）ではなく、
# services.auto_cancel_stale_requestsを直接呼び出し、DBへの反映結果を検証する。


# ========== 結合テストNo.1 ==========
# 承認済みで返却予定日が過去の申請が自動取消され、申請者宛に通知が登録されること
def test_auto_cancel_stale_requests_001_approved_overdue(db, make_user, make_loan_request):
    applicant = make_user("applicant001", "申請者太郎", "password1")
    today = date.today()
    loan_request = make_loan_request(
        applicant.id,
        status="approved",
        start_date=today - timedelta(days=20),
        due_date=today - timedelta(days=1),
    )

    services.auto_cancel_stale_requests(db)

    db.refresh(loan_request)
    assert loan_request.status == "cancelled"
    assert loan_request.cancelled_at is not None
    assert loan_request.cancelled_by_user_id is None

    notifications = crud.get_notifications_by_recipient(db, applicant.id)
    assert len(notifications) == 1
    assert notifications[0].notification_type == "cancelled"
    assert notifications[0].loan_request_id == loan_request.id


# ========== 結合テストNo.2 ==========
# 申請中で開始日が過去の申請が自動取消され、申請者宛に通知が登録されること
def test_auto_cancel_stale_requests_002_pending_overdue(db, make_user, make_loan_request):
    applicant = make_user("applicant002", "申請者太郎", "password1")
    today = date.today()
    loan_request = make_loan_request(
        applicant.id,
        status="pending",
        start_date=today - timedelta(days=1),
        due_date=today + timedelta(days=8),
    )

    services.auto_cancel_stale_requests(db)

    db.refresh(loan_request)
    assert loan_request.status == "cancelled"
    assert loan_request.cancelled_at is not None
    assert loan_request.cancelled_by_user_id is None

    notifications = crud.get_notifications_by_recipient(db, applicant.id)
    assert len(notifications) == 1
    assert notifications[0].notification_type == "cancelled"
    assert notifications[0].loan_request_id == loan_request.id


# ========== 結合テストNo.3 ==========
# 承認済みだが返却予定日が今日以降の申請は取消対象外であること
def test_auto_cancel_stale_requests_003_approved_not_overdue(db, make_user, make_loan_request):
    applicant = make_user("applicant003", "申請者太郎", "password1")
    today = date.today()
    loan_request = make_loan_request(
        applicant.id,
        status="approved",
        start_date=today,
        due_date=today + timedelta(days=9),
    )

    services.auto_cancel_stale_requests(db)

    db.refresh(loan_request)
    assert loan_request.status == "approved"
    assert len(crud.get_notifications_by_recipient(db, applicant.id)) == 0


# ========== 結合テストNo.4 ==========
# 申請中だが開始日が今日以降の申請は取消対象外であること
def test_auto_cancel_stale_requests_004_pending_not_overdue(db, make_user, make_loan_request):
    applicant = make_user("applicant004", "申請者太郎", "password1")
    today = date.today()
    loan_request = make_loan_request(
        applicant.id,
        status="pending",
        start_date=today,
        due_date=today + timedelta(days=9),
    )

    services.auto_cancel_stale_requests(db)

    db.refresh(loan_request)
    assert loan_request.status == "pending"
    assert len(crud.get_notifications_by_recipient(db, applicant.id)) == 0


# ========== 結合テストNo.5 ==========
# 貸出中・返却済みの申請は、返却予定日や開始日が過去であっても取消対象外であること
def test_auto_cancel_stale_requests_005_lending_and_returned_not_affected(db, make_user, make_loan_request):
    lending_applicant = make_user("applicant005a", "申請者A", "password1")
    returned_applicant = make_user("applicant005b", "申請者B", "password1")
    today = date.today()
    lending_request = make_loan_request(
        lending_applicant.id,
        status="lending",
        start_date=today - timedelta(days=10),
        due_date=today - timedelta(days=1),
    )
    returned_request = make_loan_request(
        returned_applicant.id,
        status="returned",
        start_date=today - timedelta(days=10),
        due_date=today - timedelta(days=1),
    )

    services.auto_cancel_stale_requests(db)

    db.refresh(lending_request)
    db.refresh(returned_request)
    assert lending_request.status == "lending"
    assert returned_request.status == "returned"
    assert len(crud.get_notifications_by_recipient(db, lending_applicant.id)) == 0
    assert len(crud.get_notifications_by_recipient(db, returned_applicant.id)) == 0


# ========== 結合テストNo.6 ==========
# 取消対象の申請が存在しない場合、例外なく処理が完了すること
def test_auto_cancel_stale_requests_006_no_target(db):
    services.auto_cancel_stale_requests(db)
