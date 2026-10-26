from datetime import date, timedelta

from app import crud, services

# ==================================================
# 期限通知生成
# テスト対象ファイル：services.py
# テスト対象クラス：-
# テスト対象メソッド：generate_due_reminder_notifications
# テスト仕様書：テスト仕様書/結合テスト仕様書/オーケストレーション処理（services）/貸出・返却/期限通知生成_結合テスト仕様書.md
# ==================================================
#
# HTTPエンドポイントを持たない日次バッチ本体のため、TestClient（HTTP経由）ではなく、
# services.generate_due_reminder_notificationsを直接呼び出し、DBへの反映結果を検証する。


# ========== 結合テストNo.1 ==========
# 貸出中で返却予定日が明日の申請に期限通知が送信されること
def test_generate_due_reminder_notifications_001_due_tomorrow(db, make_user, make_loan_request):
    applicant = make_user("applicant001", "申請者太郎", "password1")
    today = date.today()
    loan_request = make_loan_request(
        applicant.id,
        status="lending",
        start_date=today - timedelta(days=9),
        due_date=today + timedelta(days=1),
    )

    services.generate_due_reminder_notifications(db)

    notifications = crud.get_notifications_by_recipient(db, applicant.id)
    assert len(notifications) == 1
    assert notifications[0].notification_type == "due_reminder"
    assert notifications[0].loan_request_id == loan_request.id


# ========== 結合テストNo.2 ==========
# 貸出中で返却予定日が過去（期限超過中）の申請に期限通知が送信されること
def test_generate_due_reminder_notifications_002_overdue(db, make_user, make_loan_request):
    applicant = make_user("applicant002", "申請者太郎", "password1")
    today = date.today()
    loan_request = make_loan_request(
        applicant.id,
        status="lending",
        start_date=today - timedelta(days=10),
        due_date=today - timedelta(days=1),
    )

    services.generate_due_reminder_notifications(db)

    notifications = crud.get_notifications_by_recipient(db, applicant.id)
    assert len(notifications) == 1
    assert notifications[0].notification_type == "due_reminder"
    assert notifications[0].loan_request_id == loan_request.id


# ========== 結合テストNo.3 ==========
# 貸出中で返却予定日が今日の申請は通知対象外であること
def test_generate_due_reminder_notifications_003_due_today_excluded(db, make_user, make_loan_request):
    applicant = make_user("applicant003", "申請者太郎", "password1")
    today = date.today()
    make_loan_request(
        applicant.id,
        status="lending",
        start_date=today - timedelta(days=9),
        due_date=today,
    )

    services.generate_due_reminder_notifications(db)

    assert len(crud.get_notifications_by_recipient(db, applicant.id)) == 0


# ========== 結合テストNo.4 ==========
# 貸出中で返却予定日が明日より先（2日後）の申請は通知対象外であること
def test_generate_due_reminder_notifications_004_due_in_two_days_excluded(db, make_user, make_loan_request):
    applicant = make_user("applicant004", "申請者太郎", "password1")
    today = date.today()
    make_loan_request(
        applicant.id,
        status="lending",
        start_date=today - timedelta(days=8),
        due_date=today + timedelta(days=2),
    )

    services.generate_due_reminder_notifications(db)

    assert len(crud.get_notifications_by_recipient(db, applicant.id)) == 0


# ========== 結合テストNo.5 ==========
# 貸出中以外（承認済み・取消済み）の申請は、返却予定日が明日や過去であっても通知対象外であること
def test_generate_due_reminder_notifications_005_non_lending_excluded(db, make_user, make_loan_request):
    approved_applicant = make_user("applicant005a", "申請者A", "password1")
    cancelled_applicant = make_user("applicant005b", "申請者B", "password1")
    today = date.today()
    make_loan_request(
        approved_applicant.id,
        status="approved",
        start_date=today,
        due_date=today + timedelta(days=1),
    )
    make_loan_request(
        cancelled_applicant.id,
        status="cancelled",
        start_date=today - timedelta(days=10),
        due_date=today - timedelta(days=1),
    )

    services.generate_due_reminder_notifications(db)

    assert len(crud.get_notifications_by_recipient(db, approved_applicant.id)) == 0
    assert len(crud.get_notifications_by_recipient(db, cancelled_applicant.id)) == 0


# ========== 結合テストNo.6 ==========
# 期限超過中の申請に対し複数回呼び出した場合、毎回通知が登録されること
def test_generate_due_reminder_notifications_006_repeated_calls_each_notify(db, make_user, make_loan_request):
    applicant = make_user("applicant006", "申請者太郎", "password1")
    today = date.today()
    loan_request = make_loan_request(
        applicant.id,
        status="lending",
        start_date=today - timedelta(days=10),
        due_date=today - timedelta(days=1),
    )

    services.generate_due_reminder_notifications(db)
    services.generate_due_reminder_notifications(db)

    notifications = crud.get_notifications_by_recipient(db, applicant.id)
    assert len(notifications) == 2
    assert all(
        n.notification_type == "due_reminder" and n.loan_request_id == loan_request.id for n in notifications
    )
