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
import uuid
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


@pytest.fixture
def make_loan_request(db: Session):
    """
    貸出申請作成ヘルパー（状態指定）

    【概要】
    貸出申請レコードを作成し、指定した状態（status）に更新したうえで貸出申請を返却する。
    ユーザー無効化テスト等、申請中（pending）以外の状態（承認済み・貸出中等）が必要な場合に使用する。
    equipment_internal_idを指定しない場合は、新規の備品（資産番号は呼び出しごとに一意な値を発行）を
    作成したうえで申請を作成する。既存の備品に対して複数件の申請を作成したい場合（予約状況取得テスト等）は、
    equipment_internal_idに対象備品の内部IDを指定する。
    """

    def _make_loan_request(
        applicant_user_internal_id: int,
        status: str = "pending",
        equipment_internal_id: int | None = None,
        start_date: date = date(2026, 11, 1),
        due_date: date = date(2026, 11, 10),
    ):
        if equipment_internal_id is None:
            asset_number = f"AST-TEST-{uuid.uuid4().hex[:8]}"
            equipment = crud.create_equipment(db, asset_number, "結合テスト用備品", "結合テスト", None, None)
            equipment_internal_id = equipment.id
        loan_request = crud.create_loan_request(
            db,
            equipment_internal_id,
            applicant_user_internal_id,
            start_date,
            due_date,
            "結合テスト用",
        )
        loan_request.status = status
        db.commit()
        db.refresh(loan_request)
        return loan_request

    return _make_loan_request


@pytest.fixture
def make_equipment(db: Session):
    """
    テスト備品作成ヘルパー

    【概要】
    資産番号・備品名・分類・説明・保管場所を指定して備品を作成する。無効化済み状態（is_active=False）も
    指定できる。資産番号を指定しない場合は、呼び出しごとに一意な値を発行する。
    """

    def _make_equipment(
        name: str = "結合テスト用備品",
        category: str = "結合テスト",
        description: str | None = None,
        location: str | None = None,
        is_active: bool = True,
        asset_number: str | None = None,
    ):
        resolved_asset_number = asset_number or f"AST-TEST-{uuid.uuid4().hex[:8]}"
        equipment = crud.create_equipment(db, resolved_asset_number, name, category, description, location)
        equipment.is_active = is_active
        db.commit()
        db.refresh(equipment)
        return equipment

    return _make_equipment
