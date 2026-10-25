"""
結合テスト共通設定・フィクスチャ

【概要】
テスト対象アプリケーション（FastAPI）を、モックを用いず実際のHTTPエンドポイント経由で検証するための
結合テスト基盤を提供する。テストごとに独立したインメモリSQLiteデータベース（単一接続共有）を用意し、
app.database.SessionLocal・app.main.SessionLocalの両方をこのDBに向けて差し替えたうえで、
アプリケーション起動処理（lifespan）を経由するTestClientを提供する。
"""

import itertools
import os
from collections.abc import Generator
from datetime import date, datetime

import pytest
from fastapi.testclient import TestClient
from pwdlib import PasswordHash
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import crud, database, main

# app.main.lifespan内の初期管理者アカウント自動作成処理が参照する環境変数。
# テスト全体で固定値を使うため、モジュール読み込み時に一度だけ設定する
# （app/tests/conftest.pyでDATABASE_URL・JWT_SECRET_KEYが先に設定済みであることを前提とする）。
os.environ.setdefault("ADMIN_USER_ID", "admin")
os.environ.setdefault("ADMIN_NAME", "システム管理者")
os.environ.setdefault("ADMIN_PASSWORD", "AdminInitPass1")

_password_hash = PasswordHash.recommended()


@pytest.fixture
def db(monkeypatch: pytest.MonkeyPatch) -> Generator[Session]:
    """
    結合テスト用DBセッション

    【概要】
    テストごとに新規のインメモリSQLite（StaticPoolによる単一接続共有）を用意し、テーブルを作成したうえで、
    app.database.SessionLocal・app.main.SessionLocalの両方をこのDBに向けて差し替える。
    （app.database.get_dbは自モジュールのSessionLocalを参照するため差し替えが反映されるが、
    app.main.lifespan内の初期管理者アカウント作成処理は、インポート時に別名束縛されたapp.main.SessionLocalを
    参照するため、app.database.SessionLocalの差し替えだけでは反映されない）
    フィクスチャ自体は、テストコードから直接DB操作・検証を行うためのセッションを返却する。
    """

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    database.Base.metadata.create_all(bind=engine)
    test_session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    monkeypatch.setattr(database, "SessionLocal", test_session_local)
    monkeypatch.setattr(main, "SessionLocal", test_session_local)

    session = test_session_local()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db: Session) -> Generator[TestClient]:
    """
    結合テスト用HTTPクライアント

    【概要】
    dbフィクスチャで差し替え済みのテスト用DBに向けて、アプリケーション起動処理（lifespanによる
    初期管理者アカウント自動作成・日次バッチ起動定義）を実行したうえで、実際のHTTPエンドポイント
    経由でリクエストを送信するTestClientを提供する。
    """

    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture
def make_user(db: Session):
    """
    テストユーザー作成ヘルパー

    【概要】
    ユーザーID・氏名・パスワード（平文）を指定してユーザーを作成する。
    必要に応じて、初回パスワード変更完了済み・無効化済み・連続ログイン失敗状態を設定できる。
    """

    def _make_user(
        user_id: str,
        name: str,
        password: str,
        role: str = "general",
        must_change_password: bool = False,
        is_active: bool = True,
        failed_login_count: int = 0,
        locked_until: datetime | None = None,
    ):
        hashed_password = _password_hash.hash(password)
        user = crud.create_user(db, user_id, name, None, hashed_password, role)
        user.must_change_password = must_change_password
        user.is_active = is_active
        user.failed_login_count = failed_login_count
        user.locked_until = locked_until
        db.commit()
        db.refresh(user)
        return user

    return _make_user


@pytest.fixture
def login(client: TestClient):
    """
    ログインヘルパー

    【概要】
    指定したユーザーID・パスワードでPOST /tokenを実行し、取得したアクセストークンを返却する。
    """

    def _login(user_id: str, password: str) -> str:
        response = client.post("/token", json={"user_id": user_id, "password": password})
        return response.json()["access_token"]

    return _login


@pytest.fixture
def make_notification_target(db: Session):
    """
    通知テスト用の貸出申請作成ヘルパー

    【概要】
    通知情報は貸出申請IDに外部キー制約（NOT NULL）を持つため、通知テストで最小限必要な
    備品・貸出申請レコードを作成し、貸出申請の内部IDを返却する。
    """

    asset_number_counter = itertools.count(1)

    def _make_notification_target(applicant_user_internal_id: int) -> int:
        asset_number = f"AST-TEST-{next(asset_number_counter):04d}"
        equipment = crud.create_equipment(db, asset_number, "結合テスト用備品", "結合テスト", None, None)
        loan_request = crud.create_loan_request(
            db,
            equipment.id,
            applicant_user_internal_id,
            date(2026, 11, 1),
            date(2026, 11, 10),
            "結合テスト用",
        )
        return loan_request.id

    return _make_notification_target
