"""
データアクセス処理（共通）

【概要】
ユーザー情報・通知情報に対するDBアクセス処理（データアクセス層）を定義する。他機能群のデータアクセス処理は各機能群バックログで追加する。
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Notification, User

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
