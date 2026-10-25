"""
オーケストレーション処理（共通）

【概要】
通知一覧取得・通知既読化、ユーザー管理（登録・一覧取得・詳細取得・編集・無効化・再有効化・パスワード初期化）、
備品管理（検索・一覧取得、詳細取得、予約状況取得、登録、編集、無効化、再有効化、CSV一括登録）、
貸出申請・承認（貸出申請、申請取消、承認待ち申請一覧取得、申請承認、申請却下、管理者申請取消）のオーケストレーション処理を定義する。
貸出・返却機能群の日次バッチ本体（ノーショー自動取消・期限通知生成）は、貸出・返却機能群バックログで本ファイルに追加する。
"""

import csv
import io
import re
from dataclasses import dataclass
from datetime import date

from fastapi import HTTPException
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app import crud
from app.models import Equipment, Notification, User
from app.schemas import (
    EquipmentCreateRequest,
    EquipmentUpdateRequest,
    LoanRequestAdminCancelRequest,
    LoanRequestCreateRequest,
    LoanRequestRejectRequest,
    PasswordResetRequest,
    UserCreateRequest,
    UserUpdateRequest,
)

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
# - create_equipment : 備品登録
# - update_equipment : 備品編集
# - disable_equipment : 備品無効化
# - enable_equipment : 備品再有効化
# - bulk_import_equipment : 備品CSV一括登録

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


_ASSET_NUMBER_PATTERN = re.compile(r"^[A-Za-z0-9-]{1,32}$")
_EQUIPMENT_CSV_HEADER = ["資産番号", "備品名", "分類", "説明", "保管場所"]
_EQUIPMENT_CSV_MAX_SIZE = 5 * 1024 * 1024
_EQUIPMENT_CSV_MAX_ROWS = 1000


@dataclass
class EquipmentCsvRowError:
    """
    備品CSV行エラー

    【概要】
    備品CSV一括登録の検証エラー一覧の1要素（行番号とエラー内容）を保持する

    【属性】
    - row_number (int): 行番号（ヘッダー行を1行目とする）
    - error_message (str): エラー内容
    """

    row_number: int
    error_message: str


def create_equipment(db: Session, equipment_create_request: EquipmentCreateRequest) -> Equipment:
    """
    備品登録

    設計書：サーバー処理（main）/備品管理/備品登録_v0.1.0.md

    【処理概要】
    - 資産番号の重複がないことを確認し、備品を新規登録する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - equipment_create_request (EquipmentCreateRequest) : 備品作成リクエスト (必須)

    【戻り値】
    - equipment (Equipment) : 登録した備品情報

    【例外処理】
    - HTTPException(400) : 資産番号が既に使用されている場合

    【処理フロー】
    1. 資産番号重複を確認する
    2. 備品を登録する
    3. 戻り値を返却
    """

    # 1. 資産番号重複を確認する
    existing_equipment = crud.get_equipment_by_asset_number(db, equipment_create_request.asset_number)
    if existing_equipment is not None:
        raise HTTPException(status_code=400, detail="この資産番号は既に使用されています")

    # 2. 備品を登録する
    equipment = crud.create_equipment(
        db,
        equipment_create_request.asset_number,
        equipment_create_request.name,
        equipment_create_request.category,
        equipment_create_request.description,
        equipment_create_request.location,
    )

    # 3. 戻り値を返却
    return equipment


def update_equipment(db: Session, asset_number: str, equipment_update_request: EquipmentUpdateRequest) -> Equipment:
    """
    備品編集

    設計書：サーバー処理（main）/備品管理/備品編集_v0.1.0.md

    【処理概要】
    - 対象備品の備品名・分類・説明・保管場所を更新する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - asset_number (str) : 資産番号 (必須)
    - equipment_update_request (EquipmentUpdateRequest) : 備品編集リクエスト (必須)

    【戻り値】
    - equipment (Equipment) : 更新した備品情報

    【例外処理】
    - HTTPException(404) : 備品が取得できない場合

    【処理フロー】
    1. 対象備品を取得する
    2. 備品を更新する
    3. 戻り値を返却
    """

    # 1. 対象備品を取得する
    target_equipment = crud.get_equipment_by_asset_number(db, asset_number)
    if target_equipment is None:
        raise HTTPException(status_code=404, detail="備品が見つかりません")

    # 2. 備品を更新する
    updated_equipment = crud.update_equipment(
        db,
        target_equipment.id,
        equipment_update_request.name,
        equipment_update_request.category,
        equipment_update_request.description,
        equipment_update_request.location,
    )

    # 3. 戻り値を返却
    return updated_equipment


def disable_equipment(db: Session, asset_number: str) -> Equipment:
    """
    備品無効化

    設計書：サーバー処理（main）/備品管理/備品無効化_v0.1.0.md

    【処理概要】
    - 対象備品に申請中・承認済み・貸出中の申請がないことを確認し、無効化する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - asset_number (str) : 資産番号 (必須)

    【戻り値】
    - equipment (Equipment) : 無効化した備品情報

    【例外処理】
    - HTTPException(404) : 備品が取得できない場合
    - HTTPException(400) : 備品が既に無効化されている場合
    - HTTPException(400) : 申請中・承認済み・貸出中の申請が存在する場合

    【処理フロー】
    1. 対象備品を取得する
    2. 無効化可能なことを確認する
    3. 備品を無効化する
    4. 戻り値を返却
    """

    # 1. 対象備品を取得する
    target_equipment = crud.get_equipment_by_asset_number(db, asset_number)
    if target_equipment is None:
        raise HTTPException(status_code=404, detail="備品が見つかりません")
    if not target_equipment.is_active:
        raise HTTPException(status_code=400, detail="既に無効化されています")

    # 2. 無効化可能なことを確認する
    has_active_loan_request = crud.exists_active_loan_request_by_equipment(db, target_equipment.id)
    if has_active_loan_request:
        raise HTTPException(status_code=400, detail="申請中・承認済み・貸出中の申請があるため無効化できません")

    # 3. 備品を無効化する
    disabled_equipment = crud.disable_equipment(db, target_equipment.id)

    # 4. 戻り値を返却
    return disabled_equipment


def enable_equipment(db: Session, asset_number: str) -> Equipment:
    """
    備品再有効化

    設計書：サーバー処理（main）/備品管理/備品再有効化_v0.1.0.md

    【処理概要】
    - 対象備品を再有効化する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - asset_number (str) : 資産番号 (必須)

    【戻り値】
    - equipment (Equipment) : 再有効化した備品情報

    【例外処理】
    - HTTPException(404) : 備品が取得できない場合
    - HTTPException(400) : 備品が既に有効化されている場合

    【処理フロー】
    1. 対象備品を取得する
    2. 備品を再有効化する
    3. 戻り値を返却
    """

    # 1. 対象備品を取得する
    target_equipment = crud.get_equipment_by_asset_number(db, asset_number)
    if target_equipment is None:
        raise HTTPException(status_code=404, detail="備品が見つかりません")
    if target_equipment.is_active:
        raise HTTPException(status_code=400, detail="既に有効化されています")

    # 2. 備品を再有効化する
    enabled_equipment = crud.enable_equipment(db, target_equipment.id)

    # 3. 戻り値を返却
    return enabled_equipment


def _validate_equipment_csv_row(row_number: int, row: list[str]) -> list[EquipmentCsvRowError]:
    """
    備品CSV行形式検証

    【概要】
    備品CSV一括登録の1データ行について、項目の形式（文字数・パターン）を検証する

    【パラメータ】
    - row_number (int) : 行番号（ヘッダー行を1行目とする）
    - row (list[str]) : データ行の列値（資産番号・備品名・分類・説明・保管場所の順）

    【戻り値】
    - row_errors (list[EquipmentCsvRowError]) : 行エラー一覧。該当がない場合は空リスト
    """

    asset_number, name, category, description, location = row

    row_errors: list[EquipmentCsvRowError] = []
    if _ASSET_NUMBER_PATTERN.match(asset_number) is None:
        row_errors.append(
            EquipmentCsvRowError(row_number, "資産番号は32文字以内の半角英数字と`-`で入力してください")
        )
    if not (1 <= len(name) <= 100):
        row_errors.append(EquipmentCsvRowError(row_number, "備品名は1〜100文字で入力してください"))
    if not (1 <= len(category) <= 50):
        row_errors.append(EquipmentCsvRowError(row_number, "分類は1〜50文字で入力してください"))
    if len(description) > 500:
        row_errors.append(EquipmentCsvRowError(row_number, "説明は500文字以内で入力してください"))
    if len(location) > 100:
        row_errors.append(EquipmentCsvRowError(row_number, "保管場所は100文字以内で入力してください"))
    return row_errors


def bulk_import_equipment(db: Session, file_content: bytes) -> int:
    """
    備品CSV一括登録

    設計書：サーバー処理（main）/備品管理/備品CSV一括登録_v0.1.0.md

    【処理概要】
    - CSVファイルのサイズ・ヘッダー列・データ行数を検証する。
    - 全データ行について、項目の形式と資産番号の重複（ファイル内・DB内の双方）を検証する。
    - 1行でもエラーがある場合は全件登録せず、行番号付きのエラー一覧を返す。
    - 全行が検証OKの場合のみ、一括登録する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - file_content (bytes) : CSVファイル内容 (必須)

    【戻り値】
    - registered_count (int) : 登録件数

    【例外処理】
    - HTTPException(400) : ファイルサイズが5MBを超える場合
    - HTTPException(400) : CSVのヘッダー列が「資産番号・備品名・分類・説明・保管場所」の順と一致しない場合
    - HTTPException(400) : データ行数が1,000行を超える場合
    - HTTPException(400) : 検証エラーが存在する場合（行番号・エラー内容のリストを返す）

    【処理フロー】
    1. ファイルサイズを検証する
    2. CSVファイルを解析する
    3. 各データ行を検証する
    4. エラーがある場合、登録を中止する
    5. 備品を一括登録する
    6. 戻り値を返却
    """

    # 1. ファイルサイズを検証する
    if len(file_content) > _EQUIPMENT_CSV_MAX_SIZE:
        raise HTTPException(status_code=400, detail="ファイルサイズは5MB以内にしてください")

    # 2. CSVファイルを解析する
    decoded_content = file_content.decode("utf-8")
    csv_rows = list(csv.reader(io.StringIO(decoded_content)))
    header_row = csv_rows[0] if len(csv_rows) > 0 else []
    if header_row != _EQUIPMENT_CSV_HEADER:
        raise HTTPException(
            status_code=400,
            detail="CSVのヘッダー列が不正です（資産番号・備品名・分類・説明・保管場所の順で指定してください）",
        )
    data_rows = csv_rows[1:]
    if len(data_rows) > _EQUIPMENT_CSV_MAX_ROWS:
        raise HTTPException(status_code=400, detail="データ行数は1,000行以内にしてください")

    # 3. 各データ行を検証する
    # 3.(1) 項目の形式を検証する
    row_errors: list[EquipmentCsvRowError] = []
    import_rows: list[crud.EquipmentImportRow] = []
    row_numbers_by_asset_number: dict[str, list[int]] = {}
    for offset, data_row in enumerate(data_rows):
        row_number = offset + 2
        padded_row = data_row + [""] * (len(_EQUIPMENT_CSV_HEADER) - len(data_row))
        asset_number, name, category, description, location = padded_row[:5]
        row_errors.extend(_validate_equipment_csv_row(row_number, padded_row[:5]))
        row_numbers_by_asset_number.setdefault(asset_number, []).append(row_number)
        import_rows.append(
            crud.EquipmentImportRow(
                asset_number=asset_number,
                name=name,
                category=category,
                description=description or None,
                location=location or None,
            )
        )

    # 3.(2) ファイル内の資産番号重複を確認する
    for asset_number, row_numbers in row_numbers_by_asset_number.items():
        if len(row_numbers) > 1:
            for row_number in row_numbers:
                row_errors.append(EquipmentCsvRowError(row_number, "資産番号がファイル内で重複しています"))

    # 3.(3)〜(4) DB内の資産番号重複を確認する
    asset_number_list = [import_row.asset_number for import_row in import_rows]
    existing_asset_numbers = set(crud.get_existing_asset_numbers(db, asset_number_list))
    for asset_number, row_numbers in row_numbers_by_asset_number.items():
        if asset_number in existing_asset_numbers:
            for row_number in row_numbers:
                row_errors.append(EquipmentCsvRowError(row_number, "資産番号は既に登録されています"))

    # 4. エラーがある場合、登録を中止する
    if len(row_errors) > 0:
        error_list = [
            {"row_number": row_error.row_number, "error_message": row_error.error_message}
            for row_error in row_errors
        ]
        raise HTTPException(status_code=400, detail=error_list)

    # 5. 備品を一括登録する
    registered_count = crud.bulk_create_equipments(db, import_rows)

    # 6. 戻り値を返却
    return registered_count


# ====================================================================================================
# 貸出申請・承認操作
# - create_loan_request : 貸出申請
# - cancel_loan_request : 申請取消
# - get_pending_loan_requests : 承認待ち申請一覧取得
# - approve_loan_request : 申請承認
# - reject_loan_request : 申請却下
# - admin_cancel_loan_request : 管理者申請取消

# 設計書：サーバー処理（main）/貸出申請・承認/
# ====================================================================================================


def create_loan_request(
    db: Session,
    loan_request_create_request: LoanRequestCreateRequest,
    applicant_user_id: int,
    applicant_name: str,
) -> crud.LoanRequestDetailRow:
    """
    貸出申請

    設計書：サーバー処理（main）/貸出申請・承認/貸出申請_v0.1.0.md

    【処理概要】
    - 入力値の資産番号に一致する有効な備品を取得する。
    - 指定した期間について、同一備品の承認済み・貸出中の申請と重複がないことを確認する。
    - 貸出申請を新規登録し、有効な管理者全員に通知を送信する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - loan_request_create_request (LoanRequestCreateRequest) : 貸出申請リクエスト (必須)
    - applicant_user_id (int) : 申請者ユーザー内部ID (必須)
    - applicant_name (str) : 申請者氏名 (必須)

    【戻り値】
    - loan_request_detail (LoanRequestDetailRow) : 貸出申請詳細行

    【例外処理】
    - HTTPException(400) : 返却予定日が開始日より前の場合
    - HTTPException(404) : 備品が取得できない、または無効化済みの場合
    - HTTPException(400) : 指定期間が既存の承認済み・貸出中の申請と重複する場合

    【処理フロー】
    1. リクエストの日付整合性を確認する
    2. 対象備品を取得する
    3. 期間の重複を確認する
    4. 貸出申請を登録する
    5. 有効な管理者全員に通知する
    6. 戻り値を返却
    """

    # 1. リクエストの日付整合性を確認する
    if loan_request_create_request.due_date < loan_request_create_request.start_date:
        raise HTTPException(status_code=400, detail="返却予定日は開始日以降の日付を指定してください")

    # 2. 対象備品を取得する
    target_equipment = crud.get_equipment_by_asset_number(db, loan_request_create_request.asset_number)
    if target_equipment is None or not target_equipment.is_active:
        raise HTTPException(status_code=404, detail="備品が見つかりません")

    # 3. 期間の重複を確認する
    has_overlapping_loan_request = crud.exists_overlapping_loan_request_by_equipment(
        db,
        target_equipment.id,
        loan_request_create_request.start_date,
        loan_request_create_request.due_date,
    )
    if has_overlapping_loan_request:
        raise HTTPException(status_code=400, detail="指定した期間は既に貸出予定があります")

    # 4. 貸出申請を登録する
    loan_request = crud.create_loan_request(
        db,
        target_equipment.id,
        applicant_user_id,
        loan_request_create_request.start_date,
        loan_request_create_request.due_date,
        loan_request_create_request.purpose,
    )

    # 5. 有効な管理者全員に通知する
    active_admin_users = crud.get_active_admin_users(db)
    for active_admin_user in active_admin_users:
        crud.create_notification(db, active_admin_user.id, "new_request", loan_request.id)

    # 6. 戻り値を返却
    return crud.LoanRequestDetailRow(
        id=loan_request.id,
        asset_number=target_equipment.asset_number,
        equipment_name=target_equipment.name,
        applicant_name=applicant_name,
        start_date=loan_request.start_date,
        due_date=loan_request.due_date,
        purpose=loan_request.purpose,
        status=loan_request.status,
        rejection_reason=loan_request.rejection_reason,
        requested_at=loan_request.requested_at,
        decided_at=loan_request.decided_at,
        cancelled_at=loan_request.cancelled_at,
    )


def cancel_loan_request(db: Session, loan_request_id: int, current_user_id: int) -> crud.LoanRequestDetailRow:
    """
    申請取消

    設計書：サーバー処理（main）/貸出申請・承認/申請取消_v0.1.0.md

    【処理概要】
    - 申請者本人が、自身の貸出申請を取消する。
    - 対象の貸出申請を取得し、申請者が自分自身であること、状態が「申請中」または「承認済み」であることを確認する。
    - 申請を取消状態に更新する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - loan_request_id (int) : 内部ID (必須)
    - current_user_id (int) : ログインユーザー内部ID (必須)

    【戻り値】
    - loan_request_detail (LoanRequestDetailRow) : 貸出申請詳細行

    【例外処理】
    - HTTPException(404) : 貸出申請が取得できない場合
    - HTTPException(404) : 自分以外の申請を取消しようとしている場合（存在有無を判別できないよう、取得できない場合と同様に扱う）
    - HTTPException(400) : 取消可能な状態ではない場合

    【処理フロー】
    1. 対象の貸出申請を取得する
    2. 貸出申請を取消する
    3. 貸出申請の詳細を取得する
    4. 戻り値を返却
    """

    # 1. 対象の貸出申請を取得する
    target_loan_request = crud.get_loan_request_by_id(db, loan_request_id)
    if target_loan_request is None:
        raise HTTPException(status_code=404, detail="貸出申請が見つかりません")
    if target_loan_request.applicant_user_id != current_user_id:
        raise HTTPException(status_code=404, detail="貸出申請が見つかりません")
    if target_loan_request.status not in ("pending", "approved"):
        raise HTTPException(status_code=400, detail="この申請は取消できません")

    # 2. 貸出申請を取消する
    crud.cancel_loan_request(db, loan_request_id, current_user_id, None)

    # 3. 貸出申請の詳細を取得する
    loan_request_detail = crud.get_loan_request_detail_by_id(db, loan_request_id)
    assert loan_request_detail is not None

    # 4. 戻り値を返却
    return loan_request_detail


def get_pending_loan_requests(db: Session) -> list[crud.PendingLoanRequestRow]:
    """
    承認待ち申請一覧取得

    設計書：サーバー処理（main）/貸出申請・承認/承認待ち申請一覧取得_v0.1.0.md

    【処理概要】
    - 状態が「申請中」の貸出申請を、申請日時の昇順で一覧取得する。

    【パラメータ】
    - db (Session) : データベース (必須)

    【戻り値】
    - pending_loan_request_list (list[PendingLoanRequestRow]) : 承認待ち申請一覧行リスト。該当がない場合は空リスト

    【例外処理】
    - なし

    【処理フロー】
    1. 承認待ち申請一覧を取得する
    2. 戻り値を返却
    """

    # 1〜2. 承認待ち申請一覧取得・戻り値を返却
    return crud.get_pending_loan_requests(db)


def approve_loan_request(db: Session, loan_request_id: int, approved_by_user_id: int) -> crud.LoanRequestDetailRow:
    """
    申請承認

    設計書：サーバー処理（main）/貸出申請・承認/申請承認_v0.1.0.md

    【処理概要】
    - 管理者が、申請中の貸出申請を承認する。
    - 対象の貸出申請を取得し、状態が「申請中」であること、開始日が今日以降であることを確認する。
    - 指定期間について、同一備品の承認済み・貸出中の申請と重複がないことを確認する。
    - 申請を承認済み状態に更新し、申請者へ通知を送信する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - loan_request_id (int) : 内部ID (必須)
    - approved_by_user_id (int) : 承認した管理者ユーザー内部ID (必須)

    【戻り値】
    - loan_request_detail (LoanRequestDetailRow) : 貸出申請詳細行

    【例外処理】
    - HTTPException(404) : 貸出申請が取得できない場合
    - HTTPException(400) : 承認可能な状態ではない場合
    - HTTPException(400) : 開始日を過ぎている場合
    - HTTPException(400) : 指定期間が既存の承認済み・貸出中の申請と重複する場合

    【処理フロー】
    1. 対象の貸出申請を取得する
    2. 期間の重複を確認する
    3. 貸出申請を承認する
    4. 貸出申請の詳細を取得する
    5. 申請者へ通知する
    6. 戻り値を返却
    """

    # 1. 対象の貸出申請を取得する
    target_loan_request = crud.get_loan_request_by_id(db, loan_request_id)
    if target_loan_request is None:
        raise HTTPException(status_code=404, detail="貸出申請が見つかりません")
    if target_loan_request.status != "pending":
        raise HTTPException(status_code=400, detail="この申請は承認できません")
    if target_loan_request.start_date < date.today():
        raise HTTPException(status_code=400, detail="開始日を過ぎた申請は承認できません")

    # 2. 期間の重複を確認する
    has_overlapping_loan_request = crud.exists_overlapping_loan_request_by_equipment(
        db,
        target_loan_request.equipment_id,
        target_loan_request.start_date,
        target_loan_request.due_date,
    )
    if has_overlapping_loan_request:
        raise HTTPException(status_code=400, detail="指定した期間は既に貸出予定があります")

    # 3. 貸出申請を承認する
    crud.approve_loan_request(db, loan_request_id, approved_by_user_id)

    # 4. 貸出申請の詳細を取得する
    loan_request_detail = crud.get_loan_request_detail_by_id(db, loan_request_id)
    assert loan_request_detail is not None

    # 5. 申請者へ通知する
    crud.create_notification(db, target_loan_request.applicant_user_id, "approved", loan_request_id)

    # 6. 戻り値を返却
    return loan_request_detail


def reject_loan_request(
    db: Session,
    loan_request_id: int,
    rejected_by_user_id: int,
    loan_request_reject_request: LoanRequestRejectRequest,
) -> crud.LoanRequestDetailRow:
    """
    申請却下

    設計書：サーバー処理（main）/貸出申請・承認/申請却下_v0.1.0.md

    【処理概要】
    - 管理者が、申請中の貸出申請を却下する。
    - 対象の貸出申請を取得し、状態が「申請中」であることを確認する。
    - 申請を却下状態に更新し、申請者へ通知を送信する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - loan_request_id (int) : 内部ID (必須)
    - rejected_by_user_id (int) : 却下した管理者ユーザー内部ID (必須)
    - loan_request_reject_request (LoanRequestRejectRequest) : 申請却下リクエスト (必須)

    【戻り値】
    - loan_request_detail (LoanRequestDetailRow) : 貸出申請詳細行

    【例外処理】
    - HTTPException(404) : 貸出申請が取得できない場合
    - HTTPException(400) : 却下可能な状態ではない場合

    【処理フロー】
    1. 対象の貸出申請を取得する
    2. 貸出申請を却下する
    3. 貸出申請の詳細を取得する
    4. 申請者へ通知する
    5. 戻り値を返却
    """

    # 1. 対象の貸出申請を取得する
    target_loan_request = crud.get_loan_request_by_id(db, loan_request_id)
    if target_loan_request is None:
        raise HTTPException(status_code=404, detail="貸出申請が見つかりません")
    if target_loan_request.status != "pending":
        raise HTTPException(status_code=400, detail="この申請は却下できません")

    # 2. 貸出申請を却下する
    crud.reject_loan_request(db, loan_request_id, rejected_by_user_id, loan_request_reject_request.rejection_reason)

    # 3. 貸出申請の詳細を取得する
    loan_request_detail = crud.get_loan_request_detail_by_id(db, loan_request_id)
    assert loan_request_detail is not None

    # 4. 申請者へ通知する
    crud.create_notification(db, target_loan_request.applicant_user_id, "rejected", loan_request_id)

    # 5. 戻り値を返却
    return loan_request_detail


def admin_cancel_loan_request(
    db: Session,
    loan_request_id: int,
    cancelled_by_user_id: int,
    loan_request_admin_cancel_request: LoanRequestAdminCancelRequest,
) -> crud.LoanRequestDetailRow:
    """
    管理者申請取消

    設計書：サーバー処理（main）/貸出申請・承認/管理者申請取消_v0.1.0.md

    【処理概要】
    - 管理者が、承認済みの貸出申請を取消する。
    - 対象の貸出申請を取得し、状態が「承認済み」であることを確認する。
    - 申請を取消状態に更新し、申請者へ通知を送信する。

    【パラメータ】
    - db (Session) : データベース (必須)
    - loan_request_id (int) : 内部ID (必須)
    - cancelled_by_user_id (int) : 取消した管理者ユーザー内部ID (必須)
    - loan_request_admin_cancel_request (LoanRequestAdminCancelRequest) : 管理者申請取消リクエスト (必須)

    【戻り値】
    - loan_request_detail (LoanRequestDetailRow) : 貸出申請詳細行

    【例外処理】
    - HTTPException(404) : 貸出申請が取得できない場合
    - HTTPException(400) : 取消可能な状態ではない場合（「申請中」の申請は却下（F09）で取消する対象のため、本機能の対象は「承認済み」のみ）

    【処理フロー】
    1. 対象の貸出申請を取得する
    2. 貸出申請を取消する
    3. 貸出申請の詳細を取得する
    4. 申請者へ通知する
    5. 戻り値を返却
    """

    # 1. 対象の貸出申請を取得する
    target_loan_request = crud.get_loan_request_by_id(db, loan_request_id)
    if target_loan_request is None:
        raise HTTPException(status_code=404, detail="貸出申請が見つかりません")
    if target_loan_request.status != "approved":
        raise HTTPException(status_code=400, detail="この申請は取消できません")

    # 2. 貸出申請を取消する
    crud.cancel_loan_request(
        db, loan_request_id, cancelled_by_user_id, loan_request_admin_cancel_request.cancellation_reason
    )

    # 3. 貸出申請の詳細を取得する
    loan_request_detail = crud.get_loan_request_detail_by_id(db, loan_request_id)
    assert loan_request_detail is not None

    # 4. 申請者へ通知する
    crud.create_notification(db, target_loan_request.applicant_user_id, "cancelled", loan_request_id)

    # 5. 戻り値を返却
    return loan_request_detail
