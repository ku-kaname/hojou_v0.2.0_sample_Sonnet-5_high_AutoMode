# 社内備品貸出管理システム

社内の備品貸出申請・承認・貸出・返却・履歴管理を行うWebアプリケーション。

## 構成

- フロントエンド：`frontend/`（React / TypeScript / Vite、Nginx配信）
- バックエンド：`backend/`（Python / FastAPI / SQLAlchemy / PostgreSQL）
- 設計書・開発プロセス成果物：`要件定義書/`・`設計書/`・`作業管理/`・`引継ぎ資料/`・`test_specification/`・`レビュー指摘表/`

## セットアップ

1. 環境変数を設定する（`.env`はGitに含めないため、各自のローカルで作成する）。

   | 変数名 | 内容 |
   |---|---|
   | `POSTGRES_USER` | PostgreSQLユーザー名 |
   | `POSTGRES_PASSWORD` | PostgreSQLパスワード |
   | `POSTGRES_DB` | PostgreSQLデータベース名 |
   | `JWT_SECRET_KEY` | アクセストークン署名用の秘密鍵 |
   | `ADMIN_USER_ID` | 初期管理者ユーザーID（3〜32文字） |
   | `ADMIN_NAME` | 初期管理者氏名 |
   | `ADMIN_PASSWORD` | 初期管理者初期パスワード（8文字以上。初回ログイン時に変更が必須） |

2. 起動する。

   ```
   docker compose up --build
   ```

3. 初回アクセス時は、`ADMIN_USER_ID`／`ADMIN_PASSWORD`でログインし、案内に従ってパスワードを変更する。

## データベースマイグレーション

バックエンドコンテナ内でAlembicを実行する。

```
docker compose exec backend alembic upgrade head
```

## テスト

```
docker compose exec backend pytest
```
