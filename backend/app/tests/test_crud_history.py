from datetime import date, datetime, timedelta

from app import crud
from app.models import Equipment, LoanRequest, User

# ==================================================
# 期限超過一覧取得
# テスト対象ファイル：crud.py
# テスト対象クラス：-
# テスト対象メソッド：get_overdue_loan_requests
# テスト仕様書：テスト仕様書/単体テスト仕様書/CRUD/履歴・状況確認/期限超過一覧取得_単体テスト仕様書.md
# ==================================================


def _create_user(db_session, user_id="user1", name="申請者太郎"):
    # テスト用のユーザーレコードをインメモリSQLiteに登録する
    now = datetime.now()
    user = User(
        user_id=user_id,
        name=name,
        hashed_password="dummy-hashed-password",
        created_at=now,
        updated_at=now,
    )
    db_session.add(user)
    db_session.commit()
    return user


def _create_equipment(db_session, asset_number="A-001", name="備品A"):
    # テスト用の備品レコードをインメモリSQLiteに登録する
    now = datetime.now()
    equipment = Equipment(
        asset_number=asset_number,
        name=name,
        category="分類A",
        created_at=now,
        updated_at=now,
    )
    db_session.add(equipment)
    db_session.commit()
    return equipment


def _create_loan_request(db_session, equipment, user, status, due_date, purpose="検証用"):
    # テスト用の貸出申請レコードをインメモリSQLiteに登録する
    now = datetime.now()
    loan_request = LoanRequest(
        equipment_id=equipment.id,
        applicant_user_id=user.id,
        start_date=due_date - timedelta(days=7),
        due_date=due_date,
        purpose=purpose,
        status=status,
        requested_at=now,
        lent_at=now if status == "lending" else None,
    )
    db_session.add(loan_request)
    db_session.commit()
    return loan_request


# ========== 単体テストNo.1 ==========
# 状態が「貸出中」かつ返却予定日が指定日より前の申請が取得され、期限超過日数が正しく算出されること
def test_get_overdue_loan_requests_001_overdue_lending(db_session):
    today = date(2026, 10, 25)
    user = _create_user(db_session)
    equipment = _create_equipment(db_session)
    _create_loan_request(db_session, equipment, user, status="lending", due_date=today - timedelta(days=3))

    overdue_rows = crud.get_overdue_loan_requests(db_session, today)

    assert len(overdue_rows) == 1
    assert overdue_rows[0].overdue_days == 3
    assert overdue_rows[0].asset_number == "A-001"
    assert overdue_rows[0].equipment_name == "備品A"
    assert overdue_rows[0].applicant_name == "申請者太郎"


# ========== 単体テストNo.2 ==========
# 状態が「貸出中」で返却予定日が指定日と同日の申請は、対象外（期限超過ではない）となること
def test_get_overdue_loan_requests_002_due_today(db_session):
    today = date(2026, 10, 25)
    user = _create_user(db_session)
    equipment = _create_equipment(db_session)
    _create_loan_request(db_session, equipment, user, status="lending", due_date=today)

    overdue_rows = crud.get_overdue_loan_requests(db_session, today)

    assert overdue_rows == []


# ========== 単体テストNo.3 ==========
# 状態が「貸出中」で返却予定日が指定日より未来の申請は対象外となること
def test_get_overdue_loan_requests_003_due_in_future(db_session):
    today = date(2026, 10, 25)
    user = _create_user(db_session)
    equipment = _create_equipment(db_session)
    _create_loan_request(db_session, equipment, user, status="lending", due_date=today + timedelta(days=1))

    overdue_rows = crud.get_overdue_loan_requests(db_session, today)

    assert overdue_rows == []


# ========== 単体テストNo.4 ==========
# 返却予定日が過去でも、状態が「貸出中」以外（返却済み・承認済み等）の申請は対象外となること
def test_get_overdue_loan_requests_004_not_lending_status(db_session):
    today = date(2026, 10, 25)
    user = _create_user(db_session)
    equipment = _create_equipment(db_session)
    _create_loan_request(db_session, equipment, user, status="returned", due_date=today - timedelta(days=3))

    overdue_rows = crud.get_overdue_loan_requests(db_session, today)

    assert overdue_rows == []


# ========== 単体テストNo.5 ==========
# 複数の期限超過申請が存在する場合、返却予定日の昇順（期限超過が長い申請が先頭）で返却されること
def test_get_overdue_loan_requests_005_sort_order(db_session):
    today = date(2026, 10, 25)
    user = _create_user(db_session)
    equipment_a = _create_equipment(db_session, asset_number="A-001", name="備品A")
    equipment_b = _create_equipment(db_session, asset_number="A-002", name="備品B")
    _create_loan_request(db_session, equipment_a, user, status="lending", due_date=today - timedelta(days=2))
    _create_loan_request(db_session, equipment_b, user, status="lending", due_date=today - timedelta(days=5))

    overdue_rows = crud.get_overdue_loan_requests(db_session, today)

    assert len(overdue_rows) == 2
    assert overdue_rows[0].asset_number == "A-002"
    assert overdue_rows[0].overdue_days == 5
    assert overdue_rows[1].asset_number == "A-001"
    assert overdue_rows[1].overdue_days == 2


# ========== 単体テストNo.6 ==========
# 期限超過の申請が1件も存在しない場合、空リストが返却されること
def test_get_overdue_loan_requests_006_no_data(db_session):
    today = date(2026, 10, 25)

    overdue_rows = crud.get_overdue_loan_requests(db_session, today)

    assert overdue_rows == []
