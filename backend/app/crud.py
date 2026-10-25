"""
データアクセス処理（共通）

【概要】
ユーザー情報・通知情報・備品情報に対するDBアクセス処理（データアクセス層）を定義する。他機能群のデータアクセス処理は各機能群バックログで追加する。
"""

from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models import Equipment, LoanRequest, Notification, User


@dataclass
class EquipmentListRow:
    """
    備品一覧行

    【概要】
    備品一覧取得（EQUIPMENTとLOAN_REQUESTの結合結果）の1行を保持する

    【属性】
    - asset_number (str): 資産番号
    - name (str): 備品名
    - category (str): 分類
    - description (str | None): 説明
    - location (str | None): 保管場所
    - is_active (bool): 有効フラグ
    - lending_status (str): 貸出状況（`available`／`lending`）
    - due_date (date | None): 返却予定日
    """

    asset_number: str
    name: str
    category: str
    description: str | None
    location: str | None
    is_active: bool
    lending_status: str
    due_date: date | None


@dataclass
class ReservationPeriodRow:
    """
    予約期間行

    【概要】
    予約期間一覧取得（LOAN_REQUESTとUSERの結合結果）の1行を保持する

    【属性】
    - start_date (date): 開始日
    - due_date (date): 返却予定日
    - status (str): 状態（`approved`／`lending`）
    - applicant_name (str): 氏名（申請者）
    """

    start_date: date
    due_date: date
    status: str
    applicant_name: str


@dataclass
class EquipmentImportRow:
    """
    登録対象備品情報

    【概要】
    備品一括登録（CSV一括登録）の登録対象リストの1要素を保持する

    【属性】
    - asset_number (str): 資産番号
    - name (str): 備品名
    - category (str): 分類
    - description (str | None): 説明
    - location (str | None): 保管場所
    """

    asset_number: str
    name: str
    category: str
    description: str | None
    location: str | None


@dataclass
class LoanRequestDetailRow:
    """
    貸出申請詳細行

    【概要】
    貸出申請詳細取得（LOAN_REQUESTとEQUIPMENT・USERの結合結果）の1行を保持する

    【属性】
    - id (int): 内部ID
    - asset_number (str): 資産番号
    - equipment_name (str): 備品名
    - applicant_name (str): 申請者氏名
    - start_date (date): 開始日
    - due_date (date): 返却予定日
    - purpose (str): 用途
    - status (str): 状態
    - rejection_reason (str | None): 却下・取消理由
    - requested_at (datetime): 申請日時
    - decided_at (datetime | None): 承認・却下日時
    - lent_at (datetime | None): 貸出日時
    - returned_at (datetime | None): 返却日時
    - cancelled_at (datetime | None): 取消日時
    - return_note (str | None): 返却時状態メモ
    """

    id: int
    asset_number: str
    equipment_name: str
    applicant_name: str
    start_date: date
    due_date: date
    purpose: str
    status: str
    rejection_reason: str | None
    requested_at: datetime
    decided_at: datetime | None
    lent_at: datetime | None
    returned_at: datetime | None
    cancelled_at: datetime | None
    return_note: str | None


@dataclass
class PendingLoanRequestRow:
    """
    承認待ち申請一覧行

    【概要】
    承認待ち申請一覧取得（LOAN_REQUESTとEQUIPMENT・USERの結合結果）の1行を保持する

    【属性】
    - id (int): 内部ID
    - asset_number (str): 資産番号
    - equipment_name (str): 備品名
    - applicant_name (str): 申請者氏名
    - start_date (date): 開始日
    - due_date (date): 返却予定日
    - purpose (str): 用途
    - requested_at (datetime): 申請日時
    """

    id: int
    asset_number: str
    equipment_name: str
    applicant_name: str
    start_date: date
    due_date: date
    purpose: str
    requested_at: datetime


@dataclass
class StaleLoanRequest:
    """
    自動取消対象申請

    【概要】
    自動取消対象申請一覧取得（LOAN_REQUEST）の1行を保持する

    【属性】
    - id (int): 内部ID
    - applicant_user_id (int): 申請者ユーザーID
    """

    id: int
    applicant_user_id: int


@dataclass
class DueReminderLoanRequest:
    """
    期限通知対象申請

    【概要】
    期限通知対象申請一覧取得（LOAN_REQUEST）の1行を保持する

    【属性】
    - id (int): 内部ID
    - applicant_user_id (int): 申請者ユーザーID
    """

    id: int
    applicant_user_id: int


# ====================================================================================================
# ユーザー操作
# - get_user_by_user_id : ユーザー取得（ユーザーID指定）
# - get_user_by_id : ユーザー取得（内部ID指定）
# - create_user : ユーザー登録
# - update_user_login_failure : ユーザー更新（ログイン失敗時）
# - update_user_login_success : ユーザー更新（ログイン成功時）
# - update_user_password : ユーザー更新（パスワード変更）
# - increment_token_version : ユーザー更新（トークン世代更新）

# 設計書：CRUD/共通/
# ====================================================================================================


def get_user_by_user_id(db: Session, user_id: str) -> User | None:
    """
    ユーザー取得（ユーザーID指定）

    設計書：CRUD/共通/ユーザー取得（ユーザーID指定）_v0.1.0.md

    【処理概要】
    - 指定したユーザーIDに一致するユーザー情報を1件取得する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - user_id (str) : ユーザーID (必須)

    【戻り値】
    - user (User | None) : ユーザー情報。該当がない場合はNone

    【例外処理】
    - なし

    【処理フロー】
    1. ユーザー取得
    2. 戻り値を返却
    """

    # 1. ユーザー取得
    # 2. 戻り値を返却
    return db.query(User).filter(User.user_id == user_id).first()


def get_user_by_id(db: Session, id: int) -> User | None:
    """
    ユーザー取得（内部ID指定）

    設計書：CRUD/共通/ユーザー取得（内部ID指定）_v0.1.0.md

    【処理概要】
    - 指定した内部IDに一致するユーザー情報を1件取得する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - id (int) : 内部ID (必須)

    【戻り値】
    - user (User | None) : ユーザー情報。該当がない場合はNone

    【例外処理】
    - なし

    【処理フロー】
    1. ユーザー取得
    2. 戻り値を返却
    """

    # 1. ユーザー取得
    # 2. 戻り値を返却
    return db.query(User).filter(User.id == id).first()


def create_user(
    db: Session,
    user_id: str,
    name: str,
    department: str | None,
    hashed_password: str,
    role: str,
) -> User:
    """
    ユーザー登録

    設計書：CRUD/共通/ユーザー登録_v0.1.0.md

    【処理概要】
    - ユーザーID・氏名・所属・パスワードハッシュ・ロールを設定したユーザーレコードを新規作成し、DBに追加する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - user_id (str) : ユーザーID (必須)
    - name (str) : 氏名 (必須)
    - department (str | None) : 所属
    - hashed_password (str) : パスワードハッシュ (必須)
    - role (str) : ロール (必須)

    【戻り値】
    - user (User) : ユーザー情報

    【例外処理】
    - なし

    【処理フロー】
    1. ユーザーレコードを新規作成してDBに追加
    2. 戻り値を返却
    """

    # 1. ユーザーレコードを新規作成してDBに追加
    now = datetime.now()
    user = User(
        user_id=user_id,
        name=name,
        department=department,
        hashed_password=hashed_password,
        role=role,
        is_active=True,
        must_change_password=True,
        failed_login_count=0,
        locked_until=None,
        token_version=0,
        created_at=now,
        updated_at=now,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 2. 戻り値を返却
    return user


def update_user_login_failure(
    db: Session,
    id: int,
    failed_login_count: int,
    locked_until: datetime | None,
) -> User:
    """
    ユーザー更新（ログイン失敗時）

    設計書：CRUD/共通/ユーザー更新（ログイン失敗時）_v0.1.0.md

    【処理概要】
    - ログイン失敗時に、連続認証失敗回数とロック解除日時を更新する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - id (int) : 内部ID (必須)
    - failed_login_count (int) : 連続認証失敗回数 (必須)
    - locked_until (datetime | None) : ロック解除日時

    【戻り値】
    - user (User) : ユーザー情報

    【例外処理】
    - なし

    【処理フロー】
    1. ユーザー更新
    2. 戻り値を返却
    """

    # 1. ユーザー更新
    user = db.query(User).filter(User.id == id).one()
    user.failed_login_count = failed_login_count
    user.locked_until = locked_until
    user.updated_at = datetime.now()
    db.commit()
    db.refresh(user)

    # 2. 戻り値を返却
    return user


def update_user_login_success(db: Session, id: int) -> User:
    """
    ユーザー更新（ログイン成功時）

    設計書：CRUD/共通/ユーザー更新（ログイン成功時）_v0.1.0.md

    【処理概要】
    - ログイン成功時に、連続認証失敗回数とロック解除日時をリセットする。

    【パラメータ】
    - db (Session) : データベース (必須)
    - id (int) : 内部ID (必須)

    【戻り値】
    - user (User) : ユーザー情報

    【例外処理】
    - なし

    【処理フロー】
    1. ユーザー更新
    2. 戻り値を返却
    """

    # 1. ユーザー更新
    user = db.query(User).filter(User.id == id).one()
    user.failed_login_count = 0
    user.locked_until = None
    user.updated_at = datetime.now()
    db.commit()
    db.refresh(user)

    # 2. 戻り値を返却
    return user


def update_user_password(db: Session, id: int, hashed_password: str) -> User:
    """
    ユーザー更新（パスワード変更）

    設計書：CRUD/共通/ユーザー更新（パスワード変更）_v0.1.0.md

    【処理概要】
    - ユーザーのパスワードハッシュを更新し、初回パスワード変更要否フラグを解除し、トークン世代を進める。

    【パラメータ】
    - db (Session) : データベース (必須)
    - id (int) : 内部ID (必須)
    - hashed_password (str) : パスワードハッシュ (必須)

    【戻り値】
    - user (User) : ユーザー情報

    【例外処理】
    - なし

    【処理フロー】
    1. ユーザー更新
    2. 戻り値を返却
    """

    # 1. ユーザー更新
    user = db.query(User).filter(User.id == id).one()
    user.hashed_password = hashed_password
    user.must_change_password = False
    user.token_version = user.token_version + 1
    user.updated_at = datetime.now()
    db.commit()
    db.refresh(user)

    # 2. 戻り値を返却
    return user


def increment_token_version(db: Session, id: int) -> None:
    """
    ユーザー更新（トークン世代更新）

    設計書：CRUD/共通/ユーザー更新（トークン世代更新）_v0.1.0.md

    【処理概要】
    - ユーザーのトークン世代を1つ進め、それ以前に発行された全トークンを失効させる。

    【パラメータ】
    - db (Session) : データベース (必須)
    - id (int) : 内部ID (必須)

    【戻り値】
    - なし

    【例外処理】
    - なし

    【処理フロー】
    1. ユーザー更新
    """

    # 1. ユーザー更新
    user = db.query(User).filter(User.id == id).one()
    user.token_version = user.token_version + 1
    user.updated_at = datetime.now()
    db.commit()


# ====================================================================================================
# 通知操作
# - get_notifications_by_recipient : 通知一覧取得
# - get_notification_by_id : 通知取得
# - update_notification_read : 通知既読化
# - create_notification : 通知登録

# 設計書：CRUD/共通/
# ====================================================================================================


def get_notifications_by_recipient(db: Session, recipient_user_id: int) -> list[Notification]:
    """
    通知一覧取得

    設計書：CRUD/共通/通知一覧取得_v0.1.0.md

    【処理概要】
    - 指定した宛先ユーザー宛の通知を一覧取得する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - recipient_user_id (int) : 宛先ユーザーID (必須)

    【戻り値】
    - notification_list (list[Notification]) : 通知情報リスト。該当がない場合は空リスト

    【例外処理】
    - なし

    【処理フロー】
    1. 通知一覧取得
    2. 戻り値を返却
    """

    # 1. 通知一覧取得
    # 2. 戻り値を返却
    return (
        db.query(Notification)
        .filter(Notification.recipient_user_id == recipient_user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )


def get_notification_by_id(db: Session, notification_id: int) -> Notification | None:
    """
    通知取得

    設計書：CRUD/共通/通知取得_v0.1.0.md

    【処理概要】
    - 内部IDをもとに通知情報を1件取得する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - notification_id (int) : 内部ID (必須)

    【戻り値】
    - notification (Notification | None) : 通知情報。該当がない場合はNone

    【例外処理】
    - なし

    【処理フロー】
    1. 通知取得
    2. 戻り値を返却
    """

    # 1. 通知取得
    # 2. 戻り値を返却
    return db.query(Notification).filter(Notification.id == notification_id).first()


def update_notification_read(db: Session, notification_id: int) -> Notification:
    """
    通知既読化

    設計書：CRUD/共通/通知既読化_v0.1.0.md

    【処理概要】
    - 入力値の内部IDに一致する通知情報の既読フラグを`true`に更新する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - notification_id (int) : 内部ID (必須)

    【戻り値】
    - notification (Notification) : 通知情報

    【例外処理】
    - なし

    【処理フロー】
    1. 通知既読化
    2. 戻り値を返却
    """

    # 1. 通知既読化
    notification = db.query(Notification).filter(Notification.id == notification_id).one()
    notification.is_read = True
    db.commit()
    db.refresh(notification)

    # 2. 戻り値を返却
    return notification


def create_notification(
    db: Session,
    recipient_user_id: int,
    notification_type: str,
    loan_request_id: int,
) -> Notification:
    """
    通知登録

    設計書：CRUD/共通/通知登録_v0.1.0.md

    【処理概要】
    - 宛先ユーザーID・種別・関連申請IDを設定した通知レコードを新規作成し、DBに追加する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - recipient_user_id (int) : 宛先ユーザーID (必須)
    - notification_type (str) : 種別 (必須)
    - loan_request_id (int) : 関連申請ID (必須)

    【戻り値】
    - notification (Notification) : 通知情報

    【例外処理】
    - なし

    【処理フロー】
    1. 通知レコードを新規作成してDBに追加
    2. 戻り値を返却
    """

    # 1. 通知レコードを新規作成してDBに追加
    notification = Notification(
        recipient_user_id=recipient_user_id,
        notification_type=notification_type,
        loan_request_id=loan_request_id,
        is_read=False,
        created_at=datetime.now(),
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    # 2. 戻り値を返却
    return notification


# ====================================================================================================
# ユーザー管理操作
# - get_users : ユーザー一覧取得
# - update_user : ユーザー編集
# - disable_user : ユーザー無効化
# - enable_user : ユーザー再有効化
# - reset_user_password : パスワード初期化
# - count_active_admins : 有効管理者数取得
# - cancel_pending_and_approved_loan_requests_by_applicant : 申請一括取消（申請者指定）
# - exists_lending_loan_request_by_applicant : 貸出中申請存在確認（申請者指定）

# 設計書：CRUD/ユーザー管理/
# ====================================================================================================


def get_users(db: Session) -> list[User]:
    """
    ユーザー一覧取得

    設計書：CRUD/ユーザー管理/ユーザー一覧取得_v0.1.0.md

    【処理概要】
    - USERテーブルの全レコードをユーザーID昇順で取得する。

    【パラメータ】
    - db (Session) : データベース (必須)

    【戻り値】
    - user_list (list[User]) : ユーザー情報リスト。該当がない場合は空リスト

    【例外処理】
    - なし

    【処理フロー】
    1. ユーザー一覧を取得する
    2. 戻り値を返却
    """

    # 1. ユーザー一覧を取得する
    # 2. 戻り値を返却
    return db.query(User).order_by(User.user_id.asc()).all()


def update_user(
    db: Session,
    user_internal_id: int,
    name: str,
    department: str | None,
    role: str,
    token_version: int,
) -> User:
    """
    ユーザー編集

    設計書：CRUD/ユーザー管理/ユーザー編集_v0.1.0.md

    【処理概要】
    - 入力値の内部IDに一致するユーザー情報の氏名・所属・ロール・トークン世代・更新日時を更新する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - user_internal_id (int) : 内部ID (必須)
    - name (str) : 氏名 (必須)
    - department (str | None) : 所属
    - role (str) : ロール (必須)
    - token_version (int) : トークン世代 (必須)

    【戻り値】
    - user (User) : ユーザー情報

    【例外処理】
    - なし

    【処理フロー】
    1. ユーザー編集
    2. 戻り値を返却
    """

    # 1. ユーザー編集
    user = db.query(User).filter(User.id == user_internal_id).one()
    user.name = name
    user.department = department
    user.role = role
    user.token_version = token_version
    user.updated_at = datetime.now()
    db.commit()
    db.refresh(user)

    # 2. 戻り値を返却
    return user


def disable_user(db: Session, user_internal_id: int, token_version: int) -> User:
    """
    ユーザー無効化

    設計書：CRUD/ユーザー管理/ユーザー無効化_v0.1.0.md

    【処理概要】
    - 入力値の内部IDに一致するユーザー情報の有効フラグを`false`に更新し、トークン世代を更新する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - user_internal_id (int) : 内部ID (必須)
    - token_version (int) : トークン世代 (必須)

    【戻り値】
    - user (User) : ユーザー情報

    【例外処理】
    - なし

    【処理フロー】
    1. ユーザー無効化
    2. 戻り値を返却
    """

    # 1. ユーザー無効化
    user = db.query(User).filter(User.id == user_internal_id).one()
    user.is_active = False
    user.token_version = token_version
    user.updated_at = datetime.now()
    db.commit()
    db.refresh(user)

    # 2. 戻り値を返却
    return user


def enable_user(db: Session, user_internal_id: int) -> User:
    """
    ユーザー再有効化

    設計書：CRUD/ユーザー管理/ユーザー再有効化_v0.1.0.md

    【処理概要】
    - 入力値の内部IDに一致するユーザー情報の有効フラグを`true`に更新する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - user_internal_id (int) : 内部ID (必須)

    【戻り値】
    - user (User) : ユーザー情報

    【例外処理】
    - なし

    【処理フロー】
    1. ユーザー再有効化
    2. 戻り値を返却
    """

    # 1. ユーザー再有効化
    user = db.query(User).filter(User.id == user_internal_id).one()
    user.is_active = True
    user.updated_at = datetime.now()
    db.commit()
    db.refresh(user)

    # 2. 戻り値を返却
    return user


def reset_user_password(db: Session, user_internal_id: int, hashed_password: str, token_version: int) -> User:
    """
    パスワード初期化

    設計書：CRUD/ユーザー管理/パスワード初期化_v0.1.0.md

    【処理概要】
    - 入力値の内部IDに一致するユーザー情報のパスワードハッシュを更新し、初回パスワード変更要否フラグを`true`に設定し、トークン世代を更新する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - user_internal_id (int) : 内部ID (必須)
    - hashed_password (str) : パスワードハッシュ (必須)
    - token_version (int) : トークン世代 (必須)

    【戻り値】
    - user (User) : ユーザー情報

    【例外処理】
    - なし

    【処理フロー】
    1. パスワード初期化
    2. 戻り値を返却
    """

    # 1. パスワード初期化
    user = db.query(User).filter(User.id == user_internal_id).one()
    user.hashed_password = hashed_password
    user.must_change_password = True
    user.token_version = token_version
    user.updated_at = datetime.now()
    db.commit()
    db.refresh(user)

    # 2. 戻り値を返却
    return user


def count_active_admins(db: Session) -> int:
    """
    有効管理者数取得

    設計書：CRUD/ユーザー管理/有効管理者数取得_v0.1.0.md

    【処理概要】
    - ロールが管理者かつ有効フラグが`true`であるユーザーの件数をUSERテーブルから取得する。

    【パラメータ】
    - db (Session) : データベース (必須)

    【戻り値】
    - active_admin_count (int) : 有効管理者数

    【例外処理】
    - なし

    【処理フロー】
    1. 有効管理者数取得
    2. 戻り値を返却
    """

    # 1. 有効管理者数取得
    # 2. 戻り値を返却
    return db.query(func.count()).select_from(User).filter(User.role == "admin", User.is_active.is_(True)).scalar()


def cancel_pending_and_approved_loan_requests_by_applicant(db: Session, applicant_user_id: int) -> None:
    """
    申請一括取消（申請者指定）

    設計書：CRUD/ユーザー管理/申請一括取消（申請者指定）_v0.1.0.md

    【処理概要】
    - 入力値の申請者ユーザーIDに一致し、状態が申請中または承認済みである申請を、LOAN_REQUESTテーブルで取消状態に更新する。
    - 取消した者ユーザーIDは、自動取消のため設定しない（空のまま）。

    【パラメータ】
    - db (Session) : データベース (必須)
    - applicant_user_id (int) : 申請者ユーザーID (必須)

    【戻り値】
    - なし

    【例外処理】
    - なし

    【処理フロー】
    1. 申請一括取消
    """

    # 1. 申請一括取消
    now = datetime.now()
    db.query(LoanRequest).filter(
        LoanRequest.applicant_user_id == applicant_user_id,
        LoanRequest.status.in_(["pending", "approved"]),
    ).update(
        {
            "status": "cancelled",
            "rejection_reason": "ユーザー無効化による自動取消",
            "cancelled_at": now,
        }
    )
    db.commit()


def exists_lending_loan_request_by_applicant(db: Session, applicant_user_id: int) -> bool:
    """
    貸出中申請存在確認（申請者指定）

    設計書：CRUD/ユーザー管理/貸出中申請存在確認（申請者指定）_v0.1.0.md

    【処理概要】
    - 入力値の申請者ユーザーIDに一致し、状態が貸出中である申請がLOAN_REQUESTテーブルに存在するかどうかを取得する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - applicant_user_id (int) : 申請者ユーザーID (必須)

    【戻り値】
    - exists (bool) : 貸出中の申請が存在する場合`true`、存在しない場合`false`

    【例外処理】
    - なし

    【処理フロー】
    1. 貸出中申請存在確認
    2. 戻り値を返却
    """

    # 1. 貸出中申請存在確認
    lending_loan_request_count = (
        db.query(func.count())
        .select_from(LoanRequest)
        .filter(LoanRequest.applicant_user_id == applicant_user_id, LoanRequest.status == "lending")
        .scalar()
    )

    # 2. 戻り値を返却
    return lending_loan_request_count >= 1


# ====================================================================================================
# 備品管理操作
# - get_equipments : 備品一覧取得
# - get_equipment_by_asset_number : 備品取得（資産番号指定）
# - get_lending_loan_request_by_equipment : 貸出中申請取得（備品指定）
# - get_approved_or_lending_loan_requests_by_equipment : 予約期間一覧取得（備品指定）
# - create_equipment : 備品登録
# - update_equipment : 備品編集
# - disable_equipment : 備品無効化
# - enable_equipment : 備品再有効化
# - exists_active_loan_request_by_equipment : 有効申請存在確認（備品指定）
# - get_existing_asset_numbers : 資産番号一覧重複確認
# - bulk_create_equipments : 備品一括登録

# 設計書：CRUD/備品管理/
# ====================================================================================================


def get_equipments(
    db: Session,
    category: str | None,
    keyword: str | None,
    is_active: bool | None,
) -> list[EquipmentListRow]:
    """
    備品一覧取得

    設計書：CRUD/備品管理/備品一覧取得_v0.1.0.md

    【処理概要】
    - 検索条件に応じて備品を一覧取得する。現在の貸出状況を合わせて取得する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - category (str | None) : 分類検索条件
    - keyword (str | None) : キーワード検索条件
    - is_active (bool | None) : 有効フラグ検索条件

    【戻り値】
    - equipment_list (list[EquipmentListRow]) : 備品一覧情報リスト。該当がない場合は空リスト

    【例外処理】
    - なし

    【処理フロー】
    1. 備品一覧取得
    2. 戻り値を返却
    """

    # 1. 備品一覧取得
    # 1.(1) EQUIPMENTテーブルと、状態が「貸出中」の申請をLOAN_REQUESTテーブルから左外部結合して取得する
    query = db.query(Equipment, LoanRequest.due_date).outerjoin(
        LoanRequest,
        (LoanRequest.equipment_id == Equipment.id) & (LoanRequest.status == "lending"),
    )
    if category is not None:
        query = query.filter(Equipment.category == category)
    if keyword is not None:
        query = query.filter(or_(Equipment.name.like(f"%{keyword}%"), Equipment.description.like(f"%{keyword}%")))
    if is_active is not None:
        query = query.filter(Equipment.is_active.is_(is_active))
    rows = query.order_by(Equipment.asset_number.asc()).all()

    # 1.(2) 取得結果の各行について、返却予定日の有無から貸出状況を判定する
    equipment_list = []
    for equipment, due_date in rows:
        if due_date is not None:
            lending_status = "lending"
        else:
            lending_status = "available"
        equipment_list.append(
            EquipmentListRow(
                asset_number=equipment.asset_number,
                name=equipment.name,
                category=equipment.category,
                description=equipment.description,
                location=equipment.location,
                is_active=equipment.is_active,
                lending_status=lending_status,
                due_date=due_date,
            )
        )

    # 2. 戻り値を返却
    return equipment_list


def get_equipment_by_asset_number(db: Session, asset_number: str) -> Equipment | None:
    """
    備品取得（資産番号指定）

    設計書：CRUD/備品管理/備品取得（資産番号指定）_v0.1.0.md

    【処理概要】
    - 指定した資産番号に一致する備品情報を1件取得する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - asset_number (str) : 資産番号 (必須)

    【戻り値】
    - equipment (Equipment | None) : 備品情報。該当がない場合はNone

    【例外処理】
    - なし

    【処理フロー】
    1. 備品取得
    2. 戻り値を返却
    """

    # 1. 備品取得
    # 2. 戻り値を返却
    return db.query(Equipment).filter(Equipment.asset_number == asset_number).first()


def get_lending_loan_request_by_equipment(db: Session, equipment_internal_id: int) -> LoanRequest | None:
    """
    貸出中申請取得（備品指定）

    設計書：CRUD/備品管理/貸出中申請取得（備品指定）_v0.1.0.md

    【処理概要】
    - 指定した備品について、現在貸出中の申請を1件取得する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - equipment_internal_id (int) : 備品内部ID (必須)

    【戻り値】
    - loan_request (LoanRequest | None) : 貸出申請情報。該当がない場合はNone

    【例外処理】
    - なし

    【処理フロー】
    1. 貸出中申請取得
    2. 戻り値を返却
    """

    # 1. 貸出中申請取得
    # 2. 戻り値を返却
    return (
        db.query(LoanRequest)
        .filter(LoanRequest.equipment_id == equipment_internal_id, LoanRequest.status == "lending")
        .first()
    )


def get_approved_or_lending_loan_requests_by_equipment(
    db: Session, equipment_internal_id: int
) -> list[ReservationPeriodRow]:
    """
    予約期間一覧取得（備品指定）

    設計書：CRUD/備品管理/予約期間一覧取得（備品指定）_v0.1.0.md

    【処理概要】
    - 指定した備品について、状態が「承認済み」「貸出中」である申請の期間を一覧取得する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - equipment_internal_id (int) : 備品内部ID (必須)

    【戻り値】
    - reservation_list (list[ReservationPeriodRow]) : 予約期間情報リスト。該当がない場合は空リスト

    【例外処理】
    - なし

    【処理フロー】
    1. 予約期間一覧取得
    2. 戻り値を返却
    """

    # 1. 予約期間一覧取得
    rows = (
        db.query(LoanRequest, User.name)
        .join(User, User.id == LoanRequest.applicant_user_id)
        .filter(LoanRequest.equipment_id == equipment_internal_id, LoanRequest.status.in_(["approved", "lending"]))
        .order_by(LoanRequest.start_date.asc())
        .all()
    )
    reservation_list = [
        ReservationPeriodRow(
            start_date=loan_request.start_date,
            due_date=loan_request.due_date,
            status=loan_request.status,
            applicant_name=applicant_name,
        )
        for loan_request, applicant_name in rows
    ]

    # 2. 戻り値を返却
    return reservation_list


def create_equipment(
    db: Session,
    asset_number: str,
    name: str,
    category: str,
    description: str | None,
    location: str | None,
) -> Equipment:
    """
    備品登録

    設計書：CRUD/備品管理/備品登録_v0.1.0.md

    【処理概要】
    - 資産番号・備品名・分類・説明・保管場所を設定した備品レコードを新規作成し、DBに追加する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - asset_number (str) : 資産番号 (必須)
    - name (str) : 備品名 (必須)
    - category (str) : 分類 (必須)
    - description (str | None) : 説明
    - location (str | None) : 保管場所

    【戻り値】
    - equipment (Equipment) : 備品情報

    【例外処理】
    - なし

    【処理フロー】
    1. 備品登録
    2. 戻り値を返却
    """

    # 1. 備品登録
    now = datetime.now()
    equipment = Equipment(
        asset_number=asset_number,
        name=name,
        category=category,
        description=description,
        location=location,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db.add(equipment)
    db.commit()
    db.refresh(equipment)

    # 2. 戻り値を返却
    return equipment


def update_equipment(
    db: Session,
    equipment_internal_id: int,
    name: str,
    category: str,
    description: str | None,
    location: str | None,
) -> Equipment:
    """
    備品編集

    設計書：CRUD/備品管理/備品編集_v0.1.0.md

    【処理概要】
    - 入力値の内部IDに一致する備品情報の備品名・分類・説明・保管場所・更新日時を更新する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - equipment_internal_id (int) : 内部ID (必須)
    - name (str) : 備品名 (必須)
    - category (str) : 分類 (必須)
    - description (str | None) : 説明
    - location (str | None) : 保管場所

    【戻り値】
    - equipment (Equipment) : 備品情報

    【例外処理】
    - なし

    【処理フロー】
    1. 備品編集
    2. 戻り値を返却
    """

    # 1. 備品編集
    equipment = db.query(Equipment).filter(Equipment.id == equipment_internal_id).one()
    equipment.name = name
    equipment.category = category
    equipment.description = description
    equipment.location = location
    equipment.updated_at = datetime.now()
    db.commit()
    db.refresh(equipment)

    # 2. 戻り値を返却
    return equipment


def disable_equipment(db: Session, equipment_internal_id: int) -> Equipment:
    """
    備品無効化

    設計書：CRUD/備品管理/備品無効化_v0.1.0.md

    【処理概要】
    - 入力値の内部IDに一致する備品情報の有効フラグを`false`に更新する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - equipment_internal_id (int) : 内部ID (必須)

    【戻り値】
    - equipment (Equipment) : 備品情報

    【例外処理】
    - なし

    【処理フロー】
    1. 備品無効化
    2. 戻り値を返却
    """

    # 1. 備品無効化
    equipment = db.query(Equipment).filter(Equipment.id == equipment_internal_id).one()
    equipment.is_active = False
    equipment.updated_at = datetime.now()
    db.commit()
    db.refresh(equipment)

    # 2. 戻り値を返却
    return equipment


def enable_equipment(db: Session, equipment_internal_id: int) -> Equipment:
    """
    備品再有効化

    設計書：CRUD/備品管理/備品再有効化_v0.1.0.md

    【処理概要】
    - 入力値の内部IDに一致する備品情報の有効フラグを`true`に更新する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - equipment_internal_id (int) : 内部ID (必須)

    【戻り値】
    - equipment (Equipment) : 備品情報

    【例外処理】
    - なし

    【処理フロー】
    1. 備品再有効化
    2. 戻り値を返却
    """

    # 1. 備品再有効化
    equipment = db.query(Equipment).filter(Equipment.id == equipment_internal_id).one()
    equipment.is_active = True
    equipment.updated_at = datetime.now()
    db.commit()
    db.refresh(equipment)

    # 2. 戻り値を返却
    return equipment


def exists_active_loan_request_by_equipment(db: Session, equipment_internal_id: int) -> bool:
    """
    有効申請存在確認（備品指定）

    設計書：CRUD/備品管理/有効申請存在確認（備品指定）_v0.1.0.md

    【処理概要】
    - 指定した備品に、状態が「申請中」「承認済み」「貸出中」のいずれかである申請があるかどうかを確認する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - equipment_internal_id (int) : 備品内部ID (必須)

    【戻り値】
    - exists (bool) : 有効申請が1件以上存在する場合True、存在しない場合False

    【例外処理】
    - なし

    【処理フロー】
    1. 有効申請存在確認
    2. 戻り値を返却
    """

    # 1. 有効申請存在確認
    active_loan_request_count = (
        db.query(func.count(LoanRequest.id))
        .filter(
            LoanRequest.equipment_id == equipment_internal_id,
            LoanRequest.status.in_(["pending", "approved", "lending"]),
        )
        .scalar()
    )

    # 2. 戻り値を返却
    return active_loan_request_count >= 1


def get_existing_asset_numbers(db: Session, asset_number_list: list[str]) -> list[str]:
    """
    資産番号一覧重複確認

    設計書：CRUD/備品管理/資産番号一覧重複確認_v0.1.0.md

    【処理概要】
    - 入力値の資産番号リストに含まれる資産番号のうち、EQUIPMENTテーブルに既に存在するものを取得する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - asset_number_list (list[str]) : 資産番号リスト (必須)

    【戻り値】
    - existing_asset_number_list (list[str]) : 登録済み資産番号リスト。該当がない場合は空リスト

    【例外処理】
    - なし

    【処理フロー】
    1. 資産番号一覧重複確認
    2. 戻り値を返却
    """

    # 1. 資産番号一覧重複確認
    # 2. 戻り値を返却
    rows = db.query(Equipment.asset_number).filter(Equipment.asset_number.in_(asset_number_list)).all()
    return [asset_number for (asset_number,) in rows]


def bulk_create_equipments(db: Session, equipment_list: list[EquipmentImportRow]) -> int:
    """
    備品一括登録

    設計書：CRUD/備品管理/備品一括登録_v0.1.0.md

    【処理概要】
    - 入力値の登録対象リストの各要素について、資産番号・備品名・分類・説明・保管場所を設定した備品レコードを新規作成し、DBに追加する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - equipment_list (list[EquipmentImportRow]) : 登録対象リスト (必須)

    【戻り値】
    - registered_count (int) : 登録件数

    【例外処理】
    - なし

    【処理フロー】
    1. 備品一括登録
    2. 戻り値を返却
    """

    # 1. 備品一括登録
    now = datetime.now()
    for equipment_row in equipment_list:
        db.add(
            Equipment(
                asset_number=equipment_row.asset_number,
                name=equipment_row.name,
                category=equipment_row.category,
                description=equipment_row.description,
                location=equipment_row.location,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
        )
    db.commit()

    # 2. 戻り値を返却
    return len(equipment_list)


# ====================================================================================================
# 貸出申請・承認操作
# - create_loan_request : 貸出申請登録
# - get_loan_request_by_id : 申請取得（内部ID指定）
# - get_loan_request_detail_by_id : 申請詳細取得（内部ID指定）
# - cancel_loan_request : 申請取消
# - approve_loan_request : 申請承認
# - reject_loan_request : 申請却下
# - get_pending_loan_requests : 承認待ち申請一覧取得
# - get_active_admin_users : 有効管理者一覧取得
# - exists_overlapping_loan_request_by_equipment : 期間重複確認（備品指定）

# 設計書：CRUD/貸出申請・承認/
# ====================================================================================================


def create_loan_request(
    db: Session,
    equipment_internal_id: int,
    applicant_user_id: int,
    start_date: date,
    due_date: date,
    purpose: str,
) -> LoanRequest:
    """
    貸出申請登録

    設計書：CRUD/貸出申請・承認/貸出申請登録_v0.1.0.md

    【処理概要】
    - 備品内部ID・申請者ユーザー内部ID・開始日・返却予定日・用途を設定した申請レコードを新規作成し、DBに追加する。状態は「申請中」で初期化する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - equipment_internal_id (int) : 備品内部ID (必須)
    - applicant_user_id (int) : 申請者ユーザー内部ID (必須)
    - start_date (date) : 開始日 (必須)
    - due_date (date) : 返却予定日 (必須)
    - purpose (str) : 用途 (必須)

    【戻り値】
    - loan_request (LoanRequest) : 貸出申請情報

    【例外処理】
    - なし

    【処理フロー】
    1. 貸出申請レコードを新規作成してDBに追加
    2. 戻り値を返却
    """

    # 1. 貸出申請レコードを新規作成してDBに追加
    loan_request = LoanRequest(
        equipment_id=equipment_internal_id,
        applicant_user_id=applicant_user_id,
        start_date=start_date,
        due_date=due_date,
        purpose=purpose,
        status="pending",
        requested_at=datetime.now(),
    )
    db.add(loan_request)
    db.commit()
    db.refresh(loan_request)

    # 2. 戻り値を返却
    return loan_request


def get_loan_request_by_id(db: Session, loan_request_internal_id: int) -> LoanRequest | None:
    """
    申請取得（内部ID指定）

    設計書：CRUD/貸出申請・承認/申請取得（内部ID指定）_v0.1.0.md

    【処理概要】
    - 入力値の内部IDに一致する申請をLOAN_REQUESTテーブルから取得する。該当がない場合はNoneを返す。

    【パラメータ】
    - db (Session) : データベース (必須)
    - loan_request_internal_id (int) : 内部ID (必須)

    【戻り値】
    - loan_request (LoanRequest | None) : 貸出申請情報。該当がない場合はNone

    【例外処理】
    - なし

    【処理フロー】
    1. 申請取得
    2. 戻り値を返却
    """

    # 1. 申請取得
    # 2. 戻り値を返却
    return db.query(LoanRequest).filter(LoanRequest.id == loan_request_internal_id).first()


def get_loan_request_detail_by_id(db: Session, loan_request_internal_id: int) -> LoanRequestDetailRow | None:
    """
    申請詳細取得（内部ID指定）

    設計書：CRUD/貸出申請・承認/申請詳細取得（内部ID指定）_v0.1.0.md

    【処理概要】
    - 入力値の内部IDに一致する申請を、EQUIPMENTテーブル・USERテーブルと結合して取得する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - loan_request_internal_id (int) : 内部ID (必須)

    【戻り値】
    - loan_request_detail (LoanRequestDetailRow | None) : 貸出申請詳細情報。該当がない場合はNone

    【例外処理】
    - なし

    【処理フロー】
    1. 貸出申請の詳細を取得
    2. 戻り値を返却
    """

    # 1. 貸出申請の詳細を取得
    row = (
        db.query(LoanRequest, Equipment.asset_number, Equipment.name, User.name)
        .join(Equipment, LoanRequest.equipment_id == Equipment.id)
        .join(User, LoanRequest.applicant_user_id == User.id)
        .filter(LoanRequest.id == loan_request_internal_id)
        .first()
    )
    if row is None:
        return None
    loan_request, asset_number, equipment_name, applicant_name = row

    # 2. 戻り値を返却
    return LoanRequestDetailRow(
        id=loan_request.id,
        asset_number=asset_number,
        equipment_name=equipment_name,
        applicant_name=applicant_name,
        start_date=loan_request.start_date,
        due_date=loan_request.due_date,
        purpose=loan_request.purpose,
        status=loan_request.status,
        rejection_reason=loan_request.rejection_reason,
        requested_at=loan_request.requested_at,
        decided_at=loan_request.decided_at,
        lent_at=loan_request.lent_at,
        returned_at=loan_request.returned_at,
        cancelled_at=loan_request.cancelled_at,
        return_note=loan_request.return_note,
    )


def cancel_loan_request(
    db: Session,
    loan_request_internal_id: int,
    cancelled_by_user_id: int,
    cancellation_reason: str | None,
) -> LoanRequest:
    """
    申請取消

    設計書：CRUD/貸出申請・承認/申請取消_v0.1.0.md

    【処理概要】
    - 入力値の内部IDに一致する申請の状態を「取消」に更新する。
    - 申請者本人による取消（F06）・管理者による取消（F12）の双方から呼び出される。取消理由は、管理者取消時は入力値を設定し、申請者本人取消時はNoneを設定する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - loan_request_internal_id (int) : 内部ID (必須)
    - cancelled_by_user_id (int) : 取消した者ユーザー内部ID (必須)
    - cancellation_reason (str | None) : 取消理由 (申請者本人取消時はNone)

    【戻り値】
    - loan_request (LoanRequest) : 更新後の貸出申請情報

    【例外処理】
    - なし

    【処理フロー】
    1. 申請取消
    2. 戻り値を返却
    """

    # 1. 申請取消
    loan_request = db.query(LoanRequest).filter(LoanRequest.id == loan_request_internal_id).one()
    loan_request.status = "cancelled"
    loan_request.rejection_reason = cancellation_reason
    loan_request.cancelled_by_user_id = cancelled_by_user_id
    loan_request.cancelled_at = datetime.now()
    db.commit()
    db.refresh(loan_request)

    # 2. 戻り値を返却
    return loan_request


def approve_loan_request(db: Session, loan_request_internal_id: int, approved_by_user_id: int) -> LoanRequest:
    """
    申請承認

    設計書：CRUD/貸出申請・承認/申請承認_v0.1.0.md

    【処理概要】
    - 入力値の内部IDに一致する申請の状態を「承認済み」に更新する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - loan_request_internal_id (int) : 内部ID (必須)
    - approved_by_user_id (int) : 承認した管理者ユーザー内部ID (必須)

    【戻り値】
    - loan_request (LoanRequest) : 更新後の貸出申請情報

    【例外処理】
    - なし

    【処理フロー】
    1. 申請承認
    2. 戻り値を返却
    """

    # 1. 申請承認
    loan_request = db.query(LoanRequest).filter(LoanRequest.id == loan_request_internal_id).one()
    loan_request.status = "approved"
    loan_request.approved_by_user_id = approved_by_user_id
    loan_request.decided_at = datetime.now()
    db.commit()
    db.refresh(loan_request)

    # 2. 戻り値を返却
    return loan_request


def reject_loan_request(
    db: Session,
    loan_request_internal_id: int,
    approved_by_user_id: int,
    rejection_reason: str,
) -> LoanRequest:
    """
    申請却下

    設計書：CRUD/貸出申請・承認/申請却下_v0.1.0.md

    【処理概要】
    - 入力値の内部IDに一致する申請の状態を「却下」に更新する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - loan_request_internal_id (int) : 内部ID (必須)
    - approved_by_user_id (int) : 却下した管理者ユーザー内部ID (必須)
    - rejection_reason (str) : 却下理由 (必須)

    【戻り値】
    - loan_request (LoanRequest) : 更新後の貸出申請情報

    【例外処理】
    - なし

    【処理フロー】
    1. 申請却下
    2. 戻り値を返却
    """

    # 1. 申請却下
    loan_request = db.query(LoanRequest).filter(LoanRequest.id == loan_request_internal_id).one()
    loan_request.status = "rejected"
    loan_request.rejection_reason = rejection_reason
    loan_request.approved_by_user_id = approved_by_user_id
    loan_request.decided_at = datetime.now()
    db.commit()
    db.refresh(loan_request)

    # 2. 戻り値を返却
    return loan_request


def get_pending_loan_requests(db: Session) -> list[PendingLoanRequestRow]:
    """
    承認待ち申請一覧取得

    設計書：CRUD/貸出申請・承認/承認待ち申請一覧取得_v0.1.0.md

    【処理概要】
    - LOAN_REQUESTテーブルを、EQUIPMENTテーブル・USERテーブルと結合し、状態が「申請中」のレコードを申請日時の昇順で取得する。

    【パラメータ】
    - db (Session) : データベース (必須)

    【戻り値】
    - pending_loan_requests (list[PendingLoanRequestRow]) : 承認待ち申請一覧情報。該当がない場合は空リスト

    【例外処理】
    - なし

    【処理フロー】
    1. 承認待ち申請一覧を取得
    2. 戻り値を返却
    """

    # 1. 承認待ち申請一覧を取得
    rows = (
        db.query(LoanRequest, Equipment.asset_number, Equipment.name, User.name)
        .join(Equipment, LoanRequest.equipment_id == Equipment.id)
        .join(User, LoanRequest.applicant_user_id == User.id)
        .filter(LoanRequest.status == "pending")
        .order_by(LoanRequest.requested_at.asc())
        .all()
    )

    # 2. 戻り値を返却
    return [
        PendingLoanRequestRow(
            id=loan_request.id,
            asset_number=asset_number,
            equipment_name=equipment_name,
            applicant_name=applicant_name,
            start_date=loan_request.start_date,
            due_date=loan_request.due_date,
            purpose=loan_request.purpose,
            requested_at=loan_request.requested_at,
        )
        for loan_request, asset_number, equipment_name, applicant_name in rows
    ]


def get_active_admin_users(db: Session) -> list[User]:
    """
    有効管理者一覧取得

    設計書：CRUD/貸出申請・承認/有効管理者一覧取得_v0.1.0.md

    【処理概要】
    - USERテーブルから、権限が「管理者」かつ有効状態のレコードを取得する。

    【パラメータ】
    - db (Session) : データベース (必須)

    【戻り値】
    - active_admin_users (list[User]) : 有効管理者一覧情報。該当がない場合は空リスト

    【例外処理】
    - なし

    【処理フロー】
    1. 有効管理者一覧を取得
    2. 戻り値を返却
    """

    # 1. 有効管理者一覧を取得
    # 2. 戻り値を返却
    return db.query(User).filter(User.role == "admin", User.is_active.is_(True)).all()


def exists_overlapping_loan_request_by_equipment(
    db: Session,
    equipment_internal_id: int,
    start_date: date,
    due_date: date,
) -> bool:
    """
    期間重複確認（備品指定）

    設計書：CRUD/貸出申請・承認/期間重複確認（備品指定）_v0.1.0.md

    【処理概要】
    - 入力値の備品内部IDに一致し、状態が「承認済み」「貸出中」のいずれかであり、かつ入力値の開始日〜返却予定日と期間が重複する申請がLOAN_REQUESTテーブルに存在するかどうかを取得する。
    - 期間の重複判定は、開始日〜返却予定日の両端を含む日単位で行う。

    【パラメータ】
    - db (Session) : データベース (必須)
    - equipment_internal_id (int) : 備品内部ID (必須)
    - start_date (date) : 開始日 (必須)
    - due_date (date) : 返却予定日 (必須)

    【戻り値】
    - exists (bool) : 重複する申請が1件以上存在する場合True、存在しない場合False

    【例外処理】
    - なし

    【処理フロー】
    1. 期間重複確認
    2. 戻り値を返却
    """

    # 1. 期間重複確認
    overlapping_count = (
        db.query(func.count(LoanRequest.id))
        .filter(
            LoanRequest.equipment_id == equipment_internal_id,
            LoanRequest.status.in_(["approved", "lending"]),
            LoanRequest.start_date <= due_date,
            LoanRequest.due_date >= start_date,
        )
        .scalar()
    )

    # 2. 戻り値を返却
    return overlapping_count >= 1


# ====================================================================================================
# 貸出・返却操作
# - get_equipment_by_id : 備品取得（内部ID指定）
# - lend_loan_request : 貸出処理
# - return_loan_request : 返却処理
# - get_stale_loan_requests : 自動取消対象申請一覧取得
# - auto_cancel_loan_request : 自動取消（内部ID指定）
# - get_due_reminder_loan_requests : 期限通知対象申請一覧取得

# 設計書：CRUD/貸出・返却/
# ====================================================================================================


def get_equipment_by_id(db: Session, equipment_internal_id: int) -> Equipment | None:
    """
    備品取得（内部ID指定）

    設計書：CRUD/貸出・返却/備品取得（内部ID指定）_v0.1.0.md

    【処理概要】
    - 入力値の内部IDに一致する備品をEQUIPMENTテーブルから取得する。該当がない場合はNoneを返す。

    【パラメータ】
    - db (Session) : データベース (必須)
    - equipment_internal_id (int) : 内部ID (必須)

    【戻り値】
    - equipment (Equipment | None) : 備品情報。該当がない場合はNone

    【例外処理】
    - なし

    【処理フロー】
    1. 備品取得
    2. 戻り値を返却
    """

    # 1. 備品取得
    # 2. 戻り値を返却
    return db.query(Equipment).filter(Equipment.id == equipment_internal_id).first()


def lend_loan_request(db: Session, loan_request_internal_id: int, lent_by_user_id: int) -> LoanRequest:
    """
    貸出処理

    設計書：CRUD/貸出・返却/貸出処理_v0.1.0.md

    【処理概要】
    - 入力値の内部IDに一致する申請の状態を「貸出中」に更新する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - loan_request_internal_id (int) : 内部ID (必須)
    - lent_by_user_id (int) : 貸出処理した管理者ユーザー内部ID (必須)

    【戻り値】
    - loan_request (LoanRequest) : 貸出申請情報（貸出処理の更新後の内容）

    【例外処理】
    - なし

    【処理フロー】
    1. 貸出処理
    2. 戻り値を返却
    """

    # 1. 貸出処理
    loan_request = db.query(LoanRequest).filter(LoanRequest.id == loan_request_internal_id).first()
    assert loan_request is not None
    loan_request.status = "lending"
    loan_request.lent_by_user_id = lent_by_user_id
    loan_request.lent_at = datetime.now()
    db.add(loan_request)
    db.commit()
    db.refresh(loan_request)

    # 2. 戻り値を返却
    return loan_request


def return_loan_request(
    db: Session,
    loan_request_internal_id: int,
    returned_by_user_id: int,
    return_note: str | None = None,
) -> LoanRequest:
    """
    返却処理

    設計書：CRUD/貸出・返却/返却処理_v0.1.0.md

    【処理概要】
    - 入力値の内部IDに一致する申請の状態を「返却済み」に更新する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - loan_request_internal_id (int) : 内部ID (必須)
    - returned_by_user_id (int) : 返却処理した管理者ユーザー内部ID (必須)
    - return_note (str | None) : 状態メモ

    【戻り値】
    - loan_request (LoanRequest) : 貸出申請情報（返却処理の更新後の内容）

    【例外処理】
    - なし

    【処理フロー】
    1. 返却処理
    2. 戻り値を返却
    """

    # 1. 返却処理
    loan_request = db.query(LoanRequest).filter(LoanRequest.id == loan_request_internal_id).first()
    assert loan_request is not None
    loan_request.status = "returned"
    loan_request.returned_by_user_id = returned_by_user_id
    loan_request.returned_at = datetime.now()
    loan_request.return_note = return_note
    db.add(loan_request)
    db.commit()
    db.refresh(loan_request)

    # 2. 戻り値を返却
    return loan_request


def get_stale_loan_requests(db: Session, today: date) -> list[StaleLoanRequest]:
    """
    自動取消対象申請一覧取得

    設計書：CRUD/貸出・返却/自動取消対象申請一覧取得_v0.1.0.md

    【処理概要】
    - 「承認済みで返却予定日を過ぎている」または「申請中で開始日を過ぎている」申請をLOAN_REQUESTテーブルから取得する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - today (date) : 今日 (必須)

    【戻り値】
    - stale_loan_request_list (list[StaleLoanRequest]) : 自動取消対象申請一覧。該当がない場合は空リスト

    【例外処理】
    - なし

    【処理フロー】
    1. 自動取消対象申請一覧取得
    2. 戻り値を返却
    """

    # 1. 自動取消対象申請一覧取得
    rows = (
        db.query(LoanRequest.id, LoanRequest.applicant_user_id)
        .filter(
            or_(
                (LoanRequest.status == "approved") & (LoanRequest.due_date < today),
                (LoanRequest.status == "pending") & (LoanRequest.start_date < today),
            )
        )
        .all()
    )

    # 2. 戻り値を返却
    return [StaleLoanRequest(id=row.id, applicant_user_id=row.applicant_user_id) for row in rows]


def auto_cancel_loan_request(db: Session, loan_request_internal_id: int) -> LoanRequest:
    """
    自動取消（内部ID指定）

    設計書：CRUD/貸出・返却/自動取消（内部ID指定）_v0.1.0.md

    【処理概要】
    - 入力値の内部IDに一致する申請の状態を「取消」に更新する。取消した者ユーザーIDは設定しない（自動取消のため）。

    【パラメータ】
    - db (Session) : データベース (必須)
    - loan_request_internal_id (int) : 内部ID (必須)

    【戻り値】
    - loan_request (LoanRequest) : 貸出申請情報（自動取消の更新後の内容）

    【例外処理】
    - なし

    【処理フロー】
    1. 自動取消
    2. 戻り値を返却
    """

    # 1. 自動取消
    loan_request = db.query(LoanRequest).filter(LoanRequest.id == loan_request_internal_id).first()
    assert loan_request is not None
    loan_request.status = "cancelled"
    loan_request.cancelled_at = datetime.now()
    db.add(loan_request)
    db.commit()
    db.refresh(loan_request)

    # 2. 戻り値を返却
    return loan_request


def get_due_reminder_loan_requests(db: Session, today: date, tomorrow: date) -> list[DueReminderLoanRequest]:
    """
    期限通知対象申請一覧取得

    設計書：CRUD/貸出・返却/期限通知対象申請一覧取得_v0.1.0.md

    【処理概要】
    - 「貸出中で返却予定日が明日」または「貸出中で返却予定日を過ぎている（期限超過中）」申請をLOAN_REQUESTテーブルから取得する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - today (date) : 今日 (必須)
    - tomorrow (date) : 明日 (必須)

    【戻り値】
    - due_reminder_loan_request_list (list[DueReminderLoanRequest]) : 期限通知対象申請一覧。該当がない場合は空リスト

    【例外処理】
    - なし

    【処理フロー】
    1. 期限通知対象申請一覧取得
    2. 戻り値を返却
    """

    # 1. 期限通知対象申請一覧取得
    rows = (
        db.query(LoanRequest.id, LoanRequest.applicant_user_id)
        .filter(
            LoanRequest.status == "lending",
            or_(LoanRequest.due_date == tomorrow, LoanRequest.due_date < today),
        )
        .all()
    )

    # 2. 戻り値を返却
    return [DueReminderLoanRequest(id=row.id, applicant_user_id=row.applicant_user_id) for row in rows]
