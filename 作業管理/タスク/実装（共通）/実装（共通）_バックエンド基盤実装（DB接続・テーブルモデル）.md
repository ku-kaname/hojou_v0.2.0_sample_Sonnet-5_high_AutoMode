# バックエンド基盤実装（DB接続・テーブルモデル）

## スコープ

[テーブル定義（models）_v0.1.0.md](../../../設計書/テーブル定義（models）_v0.1.0.md)に基づき、DB接続（SQLAlchemyのEngine・Session生成）とテーブルモデル（ORM）を実装する。加えて、Alembicによるマイグレーション環境（初期スキーマ作成）とPythonパッケージの依存関係定義を行う。

## 修正対象資材

### 修正対象

- `backend/app/database.py`（新規）
- `backend/app/models.py`（新規）
- `backend/app/__init__.py`、`backend/app/tests/__init__.py`（新規）
- `backend/pyproject.toml`（新規）
- `backend/alembic.ini`（新規）
- `backend/migrations/env.py`、`backend/migrations/script.py.mako`（新規）
- `backend/migrations/versions/0001_initial_schema.py`（新規）

## 引継ぎ資料

[引継ぎ資料/タスク毎/実装（共通）_バックエンド基盤実装（DB接続・テーブルモデル）_引継書.md](../../../引継ぎ資料/タスク毎/実装（共通）_バックエンド基盤実装（DB接続・テーブルモデル）_引継書.md)
