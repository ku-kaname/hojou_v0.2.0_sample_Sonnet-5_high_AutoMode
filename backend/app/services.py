"""
オーケストレーション処理（共通）

【概要】
通知一覧取得・通知既読化のオーケストレーション処理を定義する。貸出・返却機能群の日次バッチ本体
（ノーショー自動取消・期限通知生成）は、貸出・返却機能群バックログで本ファイルに追加する。
"""

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app import crud
from app.models import Notification

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
