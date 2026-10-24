"""
DB接続管理

【概要】
PostgreSQLへの同期SQLAlchemy接続（エンジン・セッション）を管理する。
接続情報は環境変数`DATABASE_URL`から取得する（秘密情報をソースコードに記載しないため）。
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# ====================================================================================================
# DB接続定義
# - Base : 業務コンテンツモデル（models.py）の宣言的ベースクラス
# - engine : SQLAlchemyエンジン
# - SessionLocal : セッションファクトリ
# - get_db : FastAPIの依存性注入用セッションジェネレータ
# ====================================================================================================


class Base(DeclarativeBase):
    """
    業務コンテンツモデル宣言的ベース

    【概要】
    models.pyの各テーブルモデルが継承する、SQLAlchemy宣言的マッピングのベースクラス
    """


DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Session:
    """
    DBセッション取得（依存性注入）

    【処理概要】
    - リクエスト単位でDBセッションを生成し、エンドポイント処理完了後に確実にクローズする。

    【パラメータ】
    - なし

    【戻り値】
    - db (Session) : DBセッション

    【例外処理】
    - なし

    【処理フロー】
    1. セッションを生成して呼び出し元へ渡す
    2. 呼び出し元の処理完了後、セッションをクローズする
    """

    # 1. セッションを生成して呼び出し元へ渡す
    db = SessionLocal()
    try:
        yield db
    finally:
        # 2. 呼び出し元の処理完了後、セッションをクローズする
        db.close()
