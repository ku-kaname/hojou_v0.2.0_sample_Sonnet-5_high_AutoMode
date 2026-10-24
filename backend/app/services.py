"""
オーケストレーション処理（共通）

【概要】
通知一覧取得・通知既読化、ユーザー管理（登録・一覧取得・詳細取得・編集・無効化・再有効化・パスワード初期化）、
備品管理（検索・一覧取得、詳細取得、予約状況取得）のオーケストレーション処理を定義する。
貸出・返却機能群の日次バッチ本体（ノーショー自動取消・期限通知生成）は、貸出・返却機能群バックログで本ファイルに追加する。
"""

from dataclasses import dataclass
from datetime import date

from fastapi import HTTPException
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app import crud
from app.models import Notification, User
from app.schemas import PasswordResetRequest, UserCreateRequest, UserUpdateRequest

_password_hash = PasswordHash.recommended()


@dataclass
class ReservationPeriodRow:
    """
    予約期間行

    【概要】
    予約期間一覧取得結果に、借用者氏名の可視性制御を適用した1行を保持する

    【属性】
    - start_date (date): 開始日
    - due_date (date): 返却予定日
    - status (str): 状態（`approved`／`lending`）
    - borrower_name (str | None): 借用者氏名
    """

    start_date: date
    due_date: date
    status: str
    borrower_name: str | None

# ====================================================================================================
# 通知操作
# - get_notifications : 通知一覧取得
# - mark_notification_read : 通知既読化

# 設計書：サーバー処理（main）/共通/
# ====================================================================================================


def get_notifications(db: Session, recipient_user_id: int) -> list[Notification]:
    """
    通知一覧取得

    設計書：サーバー処理（main）/共通/通知一覧取得_v0.1.0.md

    【処理概要】
    - ログインユーザーの内部IDに一致する通知情報を、作成日時の降順（新しい順）で取得する。

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
    return crud.get_notifications_by_recipient(db, recipient_user_id)


def mark_notification_read(db: Session, notification_id: int, recipient_user_id: int) -> Notification:
    """
    通知既読化

    設計書：サーバー処理（main）/共通/通知既読化_v0.1.0.md

    【処理概要】
    - 対象の通知情報を取得し、ログインユーザー自身の宛先であることを確認する。
    - 既読フラグを更新し、更新後の通知情報を返却する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - notification_id (int) : 通知ID (必須)
    - recipient_user_id (int) : 宛先ユーザーID (必須)

    【戻り値】
    - notification (Notification) : 通知情報

    【例外処理】
    - HTTPException(404) : 通知情報が取得できない場合
    - HTTPException(404) : 宛先ユーザーIDがログインユーザーの内部IDと一致しない場合

    【処理フロー】
    1. 通知取得
    2. 宛先検証
    3. 通知既読化
    4. 戻り値を返却
    """

    # 1. 通知取得
    notification = crud.get_notification_by_id(db, notification_id)
    if notification is None:
        raise HTTPException(status_code=404, detail="対象の通知が見つかりませんでした")

    # 2. 宛先検証
    if notification.recipient_user_id != recipient_user_id:
        raise HTTPException(status_code=404, detail="対象の通知が見つかりませんでした")

    # 3. 通知既読化
    updated_notification = crud.update_notification_read(db, notification_id)

    # 4. 戻り値を返却
    return updated_notification


# ====================================================================================================
# ユーザー管理操作
# - create_user : ユーザー登録
# - get_users : ユーザー一覧取得
# - get_user : ユーザー詳細取得
# - update_user : ユーザー編集
# - disable_user : ユーザー無効化
# - enable_user : ユーザー再有効化
# - reset_user_password : パスワード初期化

# 設計書：サーバー処理（main）/ユーザー管理/
# ====================================================================================================


def create_user(db: Session, user_create_request: UserCreateRequest) -> User:
    """
    ユーザー登録

    設計書：サーバー処理（main）/ユーザー管理/ユーザー登録_v0.2.0.md

    【処理概要】
    - ユーザーIDの重複を確認したうえで、初期パスワードをハッシュ化してユーザーを新規登録する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - user_create_request (UserCreateRequest) : ユーザー作成リクエスト (必須)

    【戻り値】
    - user (User) : ユーザー情報

    【例外処理】
    - HTTPException(400) : ユーザーIDが既に使用されている場合

    【処理フロー】
    1. ユーザーID重複を確認する
    2. 初期パスワードをハッシュ化する
    3. ユーザーを登録する
    4. 戻り値を返却
    """

    # 1. ユーザーID重複を確認する
    existing_user = crud.get_user_by_user_id(db, user_create_request.user_id)
    if existing_user is not None:
        raise HTTPException(status_code=400, detail="このユーザーIDは既に使用されています")

    # 2. 初期パスワードをハッシュ化する
    hashed_password = _password_hash.hash(user_create_request.password)

    # 3. ユーザーを登録する
    user = crud.create_user(
        db,
        user_create_request.user_id,
        user_create_request.name,
        user_create_request.department,
        hashed_password,
        user_create_request.role,
    )

    # 4. 戻り値を返却
    return user


def get_users(db: Session) -> list[User]:
    """
    ユーザー一覧取得

    設計書：サーバー処理（main）/ユーザー管理/ユーザー一覧取得_v0.2.0.md

    【処理概要】
    - 全ユーザー情報をユーザーID昇順で取得する。

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
    return crud.get_users(db)


def get_user(db: Session, user_id: str) -> User:
    """
    ユーザー詳細取得

    設計書：サーバー処理（main）/ユーザー管理/ユーザー詳細取得_v0.2.0.md

    【処理概要】
    - パスパラメータのユーザーIDに一致するユーザー情報を取得する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - user_id (str) : ユーザーID (必須)

    【戻り値】
    - user (User) : ユーザー情報

    【例外処理】
    - HTTPException(404) : ユーザーが取得できない場合

    【処理フロー】
    1. ユーザーを取得する
    2. 戻り値を返却
    """

    # 1. ユーザーを取得する
    user = crud.get_user_by_user_id(db, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    # 2. 戻り値を返却
    return user


def update_user(db: Session, user_id: str, user_update_request: UserUpdateRequest) -> User:
    """
    ユーザー編集

    設計書：サーバー処理（main）/ユーザー管理/ユーザー編集_v0.2.0.md

    【処理概要】
    - 最後の有効な管理者を一般ユーザーに変更しようとしていないかを確認したうえで、ユーザー情報を更新する。
    - ロールを変更した場合、既発行のトークンを失効させる。

    【パラメータ】
    - db (Session) : データベース (必須)
    - user_id (str) : ユーザーID (必須)
    - user_update_request (UserUpdateRequest) : ユーザー編集リクエスト (必須)

    【戻り値】
    - user (User) : ユーザー情報

    【例外処理】
    - HTTPException(404) : ユーザーが取得できない場合
    - HTTPException(400) : 最後の有効な管理者を一般ユーザーに変更しようとしている場合

    【処理フロー】
    1. 対象ユーザーを取得する
    2. 最後の管理者の変更でないことを確認する
    3. トークン世代を算定する
    4. ユーザーを更新する
    5. 戻り値を返却
    """

    # 1. 対象ユーザーを取得する
    target_user = crud.get_user_by_user_id(db, user_id)
    if target_user is None:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    # 2. 最後の管理者の変更でないことを確認する
    is_demoting_last_active_admin = (
        target_user.role == "admin" and target_user.is_active and user_update_request.role == "general"
    )
    if is_demoting_last_active_admin:
        active_admin_count = crud.count_active_admins(db)
        if active_admin_count <= 1:
            raise HTTPException(status_code=400, detail="最後の管理者を一般ユーザーに変更することはできません")

    # 3. トークン世代を算定する
    is_role_changed = target_user.role != user_update_request.role
    token_version = target_user.token_version + 1 if is_role_changed else target_user.token_version

    # 4. ユーザーを更新する
    updated_user = crud.update_user(
        db,
        target_user.id,
        user_update_request.name,
        user_update_request.department,
        user_update_request.role,
        token_version,
    )

    # 5. 戻り値を返却
    return updated_user


def disable_user(db: Session, user_id: str) -> User:
    """
    ユーザー無効化

    設計書：サーバー処理（main）/ユーザー管理/ユーザー無効化_v0.2.0.md

    【処理概要】
    - 最後の有効な管理者でないこと、貸出中の申請がないことを確認したうえで無効化する。
    - 無効化に伴い、申請中・承認済みの申請を自動的に取消する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - user_id (str) : ユーザーID (必須)

    【戻り値】
    - user (User) : ユーザー情報

    【例外処理】
    - HTTPException(404) : ユーザーが取得できない場合
    - HTTPException(400) : 既に無効化済みの場合
    - HTTPException(400) : 最後の有効な管理者を無効化しようとしている場合
    - HTTPException(400) : 貸出中の申請が存在する場合

    【処理フロー】
    1. 対象ユーザーを取得する
    2. 最後の管理者の無効化でないことを確認する
    3. 貸出中の申請がないことを確認する
    4. 申請中・承認済みの申請を自動取消する
    5. ユーザーを無効化する
    6. 戻り値を返却
    """

    # 1. 対象ユーザーを取得する
    target_user = crud.get_user_by_user_id(db, user_id)
    if target_user is None:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    if not target_user.is_active:
        raise HTTPException(status_code=400, detail="既に無効化されています")

    # 2. 最後の管理者の無効化でないことを確認する
    if target_user.role == "admin":
        active_admin_count = crud.count_active_admins(db)
        if active_admin_count <= 1:
            raise HTTPException(status_code=400, detail="最後の管理者を無効化することはできません")

    # 3. 貸出中の申請がないことを確認する
    has_lending_loan_request = crud.exists_lending_loan_request_by_applicant(db, target_user.id)
    if has_lending_loan_request:
        raise HTTPException(status_code=400, detail="貸出中の備品があるため無効化できません")

    # 4. 申請中・承認済みの申請を自動取消する
    crud.cancel_pending_and_approved_loan_requests_by_applicant(db, target_user.id)

    # 5. ユーザーを無効化する
    disabled_user = crud.disable_user(db, target_user.id, target_user.token_version + 1)

    # 6. 戻り値を返却
    return disabled_user


def enable_user(db: Session, user_id: str) -> User:
    """
    ユーザー再有効化

    設計書：サーバー処理（main）/ユーザー管理/ユーザー再有効化_v0.2.0.md

    【処理概要】
    - 対象ユーザーが無効化済みであることを確認したうえで再有効化する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - user_id (str) : ユーザーID (必須)

    【戻り値】
    - user (User) : ユーザー情報

    【例外処理】
    - HTTPException(404) : ユーザーが取得できない場合
    - HTTPException(400) : 既に有効化済みの場合

    【処理フロー】
    1. 対象ユーザーを取得する
    2. ユーザーを再有効化する
    3. 戻り値を返却
    """

    # 1. 対象ユーザーを取得する
    target_user = crud.get_user_by_user_id(db, user_id)
    if target_user is None:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")
    if target_user.is_active:
        raise HTTPException(status_code=400, detail="既に有効化されています")

    # 2. ユーザーを再有効化する
    enabled_user = crud.enable_user(db, target_user.id)

    # 3. 戻り値を返却
    return enabled_user


def reset_user_password(db: Session, user_id: str, password_reset_request: PasswordResetRequest) -> User:
    """
    パスワード初期化

    設計書：サーバー処理（main）/ユーザー管理/パスワード初期化_v0.2.0.md

    【処理概要】
    - 初期パスワードをハッシュ化し、次回ログイン時の変更を必須としたうえで更新する。
    - 既発行のトークンを失効させる。

    【パラメータ】
    - db (Session) : データベース (必須)
    - user_id (str) : ユーザーID (必須)
    - password_reset_request (PasswordResetRequest) : パスワード初期化リクエスト (必須)

    【戻り値】
    - user (User) : ユーザー情報

    【例外処理】
    - HTTPException(404) : ユーザーが取得できない場合

    【処理フロー】
    1. 対象ユーザーを取得する
    2. 初期パスワードをハッシュ化する
    3. パスワードを初期化する
    4. 戻り値を返却
    """

    # 1. 対象ユーザーを取得する
    target_user = crud.get_user_by_user_id(db, user_id)
    if target_user is None:
        raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

    # 2. 初期パスワードをハッシュ化する
    hashed_password = _password_hash.hash(password_reset_request.password)

    # 3. パスワードを初期化する
    updated_user = crud.reset_user_password(db, target_user.id, hashed_password, target_user.token_version + 1)

    # 4. 戻り値を返却
    return updated_user


# ====================================================================================================
# 備品管理操作
# - search_equipment : 備品検索・一覧取得
# - get_equipment : 備品詳細取得
# - get_equipment_reservations : 備品予約状況取得

# 設計書：サーバー処理（main）/備品管理/
# ====================================================================================================


def search_equipment(
    db: Session,
    role: str,
    category: str | None,
    keyword: str | None,
    is_active: bool | None,
) -> list[crud.EquipmentListRow]:
    """
    備品検索・一覧取得

    設計書：サーバー処理（main）/備品管理/備品検索・一覧取得_v0.1.0.md

    【処理概要】
    - 要求元が一般ユーザーの場合は有効な備品のみに絞り込み、管理者の場合は有効フラグの指定に応じて絞り込みを行い、一覧取得する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - role (str) : ログインユーザーのロール (必須)
    - category (str | None) : 分類検索条件
    - keyword (str | None) : キーワード検索条件
    - is_active (bool | None) : 有効フラグ検索条件（管理者のみ有効。一般ユーザーが指定した場合は無視する）

    【戻り値】
    - equipment_list (list[crud.EquipmentListRow]) : 備品一覧情報リスト。該当がない場合は空リスト

    【例外処理】
    - なし

    【処理フロー】
    1. 有効フラグ検索条件を算定する
    2. 備品一覧を取得する
    3. 戻り値を返却
    """

    # 1. 有効フラグ検索条件を算定する
    active_filter: bool | None
    if role != "admin":
        active_filter = True
    else:
        active_filter = is_active

    # 2. 備品一覧を取得する
    equipment_list = crud.get_equipments(db, category, keyword, active_filter)

    # 3. 戻り値を返却
    return equipment_list


def get_equipment(db: Session, role: str, asset_number: str) -> crud.EquipmentListRow:
    """
    備品詳細取得

    設計書：サーバー処理（main）/備品管理/備品詳細取得_v0.1.0.md

    【処理概要】
    - 対象備品の情報と現在の貸出状況を取得する。
    - 要求元が一般ユーザーの場合、無効化済みの備品は取得できない。

    【パラメータ】
    - db (Session) : データベース (必須)
    - role (str) : ログインユーザーのロール (必須)
    - asset_number (str) : 資産番号 (必須)

    【戻り値】
    - equipment (crud.EquipmentListRow) : 備品情報（貸出状況を含む）

    【例外処理】
    - HTTPException(404) : 備品が取得できない場合
    - HTTPException(404) : 一般ユーザーが無効化済み備品を取得しようとしている場合（存在有無を判別できないよう、取得できない場合と同様に扱う）

    【処理フロー】
    1. 対象備品を取得する
    2. 現在の貸出状況を取得する
    3. 戻り値を返却
    """

    # 1. 対象備品を取得する
    target_equipment = crud.get_equipment_by_asset_number(db, asset_number)
    if target_equipment is None:
        raise HTTPException(status_code=404, detail="備品が見つかりません")
    if role != "admin" and not target_equipment.is_active:
        raise HTTPException(status_code=404, detail="備品が見つかりません")

    # 2. 現在の貸出状況を取得する
    lending_loan_request = crud.get_lending_loan_request_by_equipment(db, target_equipment.id)
    if lending_loan_request is not None:
        lending_status = "lending"
        due_date = lending_loan_request.due_date
    else:
        lending_status = "available"
        due_date = None

    # 3. 戻り値を返却
    return crud.EquipmentListRow(
        asset_number=target_equipment.asset_number,
        name=target_equipment.name,
        category=target_equipment.category,
        description=target_equipment.description,
        location=target_equipment.location,
        is_active=target_equipment.is_active,
        lending_status=lending_status,
        due_date=due_date,
    )


def get_equipment_reservations(db: Session, role: str, asset_number: str) -> list[ReservationPeriodRow]:
    """
    備品予約状況取得

    設計書：サーバー処理（main）/備品管理/備品予約状況取得_v0.1.0.md

    【処理概要】
    - 対象備品の、状態が「承認済み」「貸出中」の申請を開始日昇順で取得する。
    - 借用者氏名は、要求元が管理者の場合のみ設定する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - role (str) : ログインユーザーのロール (必須)
    - asset_number (str) : 資産番号 (必須)

    【戻り値】
    - reservation_list (list[ReservationPeriodRow]) : 予約期間情報リスト。該当がない場合は空リスト

    【例外処理】
    - HTTPException(404) : 備品が取得できない場合
    - HTTPException(404) : 一般ユーザーが無効化済み備品の予約状況を取得しようとしている場合（存在有無を判別できないよう、取得できない場合と同様に扱う）

    【処理フロー】
    1. 対象備品を取得する
    2. 予約期間一覧を取得する
    3. 借用者氏名を設定する
    4. 戻り値を返却
    """

    # 1. 対象備品を取得する
    target_equipment = crud.get_equipment_by_asset_number(db, asset_number)
    if target_equipment is None:
        raise HTTPException(status_code=404, detail="備品が見つかりません")
    if role != "admin" and not target_equipment.is_active:
        raise HTTPException(status_code=404, detail="備品が見つかりません")

    # 2. 予約期間一覧を取得する
    reservation_rows = crud.get_approved_or_lending_loan_requests_by_equipment(db, target_equipment.id)

    # 3. 借用者氏名を設定する
    reservation_list = []
    for reservation_row in reservation_rows:
        if role == "admin":
            borrower_name = reservation_row.applicant_name
        else:
            borrower_name = None
        reservation_list.append(
            ReservationPeriodRow(
                start_date=reservation_row.start_date,
                due_date=reservation_row.due_date,
                status=reservation_row.status,
                borrower_name=borrower_name,
            )
        )

    # 4. 戻り値を返却
    return reservation_list
