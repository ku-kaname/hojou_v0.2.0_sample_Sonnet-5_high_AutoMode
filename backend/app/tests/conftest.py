"""
pytest共通設定・フィクスチャ

【概要】
テスト実行前に、app.database・app.authがインポート時に参照する環境変数（DATABASE_URL・JWT_SECRET_KEY）を
設定する。また、CRUD層（インメモリSQLiteを用いて実データで検証するテスト）で使用する、テーブル作成済みの
DBセッションのフィクスチャを提供する。
"""

import os
from collections.abc import Generator

# app.database（DATABASE_URL）・app.auth（JWT_SECRET_KEY）はインポート時に環境変数を読み込むため、
# それらをインポートする前に設定する必要がある。
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-unit-tests")

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base


@pytest.fixture
def db_session() -> Generator[Session]:
    """
    インメモリSQLiteセッション

    【概要】
    テーブル作成済みのインメモリSQLite上のDBセッションを提供する。CRUD層のテストで、
    ORMクエリ（ソート・結合・計算等）をモック化せず実データで検証するために使用する。
    """

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = session_local()
    try:
        yield session
    finally:
        session.close()
