"""
日次バッチ起動定義

【概要】
ノーショー自動取消・期限通知生成の日次バッチを、毎日6:00（JST）に1回だけ実行するためのジョブ登録を行う。
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.database import SessionLocal

_scheduler = BackgroundScheduler(timezone="Asia/Tokyo")


def _run_daily_batch() -> None:
    """
    日次バッチ本体（ジョブ実行）

    設計書：起動時処理（startup）/日次バッチ起動定義_v0.1.0.md

    【処理概要】
    - ノーショー自動取消・期限通知生成の順にオーケストレーション層の処理を呼び出す。

    【パラメータ】
    - なし

    【戻り値】
    - なし

    【例外処理】
    - なし
    """

    # auto_cancel_stale_requests・generate_due_reminder_notificationsは貸出・返却機能群バックログで
    # services.pyに追加されるため、起動時の循環を避けジョブ実行時に遅延importする
    from app import services

    db = SessionLocal()
    try:
        services.auto_cancel_stale_requests(db)
        services.generate_due_reminder_notifications(db)
    finally:
        db.close()


# ====================================================================================================
# 起動時処理
# - start_daily_batch_scheduler : 日次バッチ起動定義

# 設計書：起動時処理（startup）/日次バッチ起動定義_v0.1.0.md
# ====================================================================================================


def start_daily_batch_scheduler() -> None:
    """
    日次バッチ起動定義

    設計書：起動時処理（startup）/日次バッチ起動定義_v0.1.0.md

    【処理概要】
    - アプリケーション起動時に、JSTタイムゾーンのcronトリガー（毎日6:00）でジョブを1件登録する。
    - ジョブ実行時は、ノーショー自動取消・期限通知生成の順にオーケストレーション層の処理を呼び出す。

    【パラメータ】
    - なし

    【戻り値】
    - なし

    【例外処理】
    - なし

    【処理フロー】
    1. スケジューラ起動（アプリケーション起動時、1回のみ）
    2. 戻り値を返却
    """

    # 1. スケジューラ起動（アプリケーション起動時、1回のみ）
    _scheduler.add_job(
        _run_daily_batch,
        trigger=CronTrigger(hour=6, minute=0),
        id="daily_batch",
        replace_existing=True,
    )
    if not _scheduler.running:
        _scheduler.start()

    # 2. 戻り値を返却
    return None
