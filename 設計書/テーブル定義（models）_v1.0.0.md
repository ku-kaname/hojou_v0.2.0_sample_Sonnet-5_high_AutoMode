# テーブル定義

- **工程**: 設計工程
- **作成者**: Claude Sonnet 5
- **作成日**: 2026-10-24
- **最終更新日**: 2026-10-24

---

## USER

| 項目 | 内容 |
|---|---|
| テーブル論理名 | ユーザー情報 |
| テーブル物理名 | USER |

### 説明

社員アカウント情報を管理する。

| 論理名 | 物理名 | 型 | 必須 | 最小値 | 最大値 | 最小桁 | 最大桁 | 主キー | 外部キー | 制約 | インデックス | 備考 |
|---|---|---|:---:|---:|---:|---:|---:|:---:|---|---|---|---|
| 内部ID | id | INTEGER | ○ | - | - | - | - | ○ | - | - | - | 自動採番 |
| ユーザーID | user_id | VARCHAR | ○ | - | - | 3 | 32 | - | - | uq_user_user_id | - | 半角英数字と`_`・`-`。無効化後も再利用不可（物理削除しないため一意制約で担保） |
| 氏名 | name | VARCHAR | ○ | - | - | 1 | 50 | - | - | - | - | - |
| 所属 | department | VARCHAR | - | - | - | 0 | 50 | - | - | - | - | 空文字許容 |
| パスワードハッシュ | hashed_password | VARCHAR | ○ | - | - | 1 | 255 | - | - | - | - | Argon2idハッシュ。平文は保存しない |
| ロール | role | VARCHAR | ○ | - | - | - | - | - | - | ck_user_role | - | 許容値：`general`（一般）／`admin`（管理者）。デフォルト`general` |
| 有効フラグ | is_active | BOOLEAN | ○ | - | - | - | - | - | - | - | - | デフォルト`true`。`false`＝無効化（論理削除） |
| 初回パスワード変更要否フラグ | must_change_password | BOOLEAN | ○ | - | - | - | - | - | - | - | - | デフォルト`true`（登録時・パスワード初期化時） |
| トークン世代 | token_version | INTEGER | ○ | 0 | - | - | - | - | - | - | - | デフォルト0。ログアウト・無効化・パスワード変更/初期化・ロール変更時に+1 |
| 連続認証失敗回数 | failed_login_count | INTEGER | ○ | 0 | - | - | - | - | - | - | - | デフォルト0。ログイン成功時・ロック解除時に0に戻す |
| ロック解除日時 | locked_until | DATETIME | - | - | - | - | - | - | - | - | - | 連続失敗5回で現在時刻+15分を設定。空＝ロックなし |
| 作成日時 | created_at | DATETIME | ○ | - | - | - | - | - | - | - | - | サーバー時刻 |
| 更新日時 | updated_at | DATETIME | ○ | - | - | - | - | - | - | - | - | サーバー時刻。更新しない限り作成日時と同じ値 |

### 補足

- パスワードは平文を保存しない。
- 無効化（`is_active`＝`false`）してもレコードは保持し、`user_id`は再利用しない。
- 最後の有効な管理者（`role`＝`admin`かつ`is_active`＝`true`）を無効化・ロール変更することはできない（業務ルールとしてオーケストレーション層で検証する。DB制約では表現しない）。

---

## EQUIPMENT

| 項目 | 内容 |
|---|---|
| テーブル論理名 | 備品情報 |
| テーブル物理名 | EQUIPMENT |

### 説明

貸出対象となる備品を1点単位で管理する。

| 論理名 | 物理名 | 型 | 必須 | 最小値 | 最大値 | 最小桁 | 最大桁 | 主キー | 外部キー | 制約 | インデックス | 備考 |
|---|---|---|:---:|---:|---:|---:|---:|:---:|---|---|---|---|
| 内部ID | id | INTEGER | ○ | - | - | - | - | ○ | - | - | - | 自動採番 |
| 資産番号 | asset_number | VARCHAR | ○ | - | - | 1 | 32 | - | - | uq_equipment_asset_number | - | 半角英数字と`-` |
| 備品名 | name | VARCHAR | ○ | - | - | 1 | 100 | - | - | - | - | - |
| 分類 | category | VARCHAR | ○ | - | - | 1 | 50 | - | - | - | - | 自由入力（分類マスタは設けない） |
| 説明 | description | VARCHAR | - | - | - | 0 | 500 | - | - | - | - | 空文字許容 |
| 保管場所 | location | VARCHAR | - | - | - | 0 | 100 | - | - | - | - | 空文字許容 |
| 有効フラグ | is_active | BOOLEAN | ○ | - | - | - | - | - | - | - | - | デフォルト`true`。`false`＝無効化（論理削除） |
| 作成日時 | created_at | DATETIME | ○ | - | - | - | - | - | - | - | - | サーバー時刻 |
| 更新日時 | updated_at | DATETIME | ○ | - | - | - | - | - | - | - | - | サーバー時刻。更新しない限り作成日時と同じ値 |

### 補足

- 無効化（`is_active`＝`false`）しても過去の`LOAN_REQUEST`レコードからは参照され続ける。
- 無効化済み備品は新規の貸出申請の対象外とする（オーケストレーション層で検証する）。

---

## LOAN_REQUEST

| 項目 | 内容 |
|---|---|
| テーブル論理名 | 貸出申請情報 |
| テーブル物理名 | LOAN_REQUEST |

### 説明

備品の貸出申請を管理する。貸出履歴（返却済み・却下・取消を含む）も本テーブルで兼ねる。

| 論理名 | 物理名 | 型 | 必須 | 最小値 | 最大値 | 最小桁 | 最大桁 | 主キー | 外部キー | 制約 | インデックス | 備考 |
|---|---|---|:---:|---:|---:|---:|---:|:---:|---|---|---|---|
| 内部ID | id | INTEGER | ○ | - | - | - | - | ○ | - | - | - | 自動採番 |
| 備品ID | equipment_id | INTEGER | ○ | - | - | - | - | - | `foreign_key.constraint_name`: fk_loan_request_equipment_id<br>参照先: EQUIPMENT.id<br>ON UPDATE: CASCADE / ON DELETE: RESTRICT<br>カーディナリティ: 多:1 | - | - | - |
| 申請者ユーザーID | applicant_user_id | INTEGER | ○ | - | - | - | - | - | `foreign_key.constraint_name`: fk_loan_request_applicant_user_id<br>参照先: USER.id<br>ON UPDATE: CASCADE / ON DELETE: RESTRICT<br>カーディナリティ: 多:1 | - | - | - |
| 開始日 | start_date | DATE | ○ | - | - | - | - | - | - | - | - | - |
| 返却予定日 | due_date | DATE | ○ | - | - | - | - | - | - | - | - | 開始日以降 |
| 用途 | purpose | VARCHAR | ○ | - | - | 1 | 200 | - | - | - | - | - |
| 状態 | status | VARCHAR | ○ | - | - | - | - | - | - | ck_loan_request_status | - | 許容値：`pending`（申請中）／`approved`（承認済み）／`lending`（貸出中）／`returned`（返却済み）／`rejected`（却下）／`cancelled`（取消）。デフォルト`pending` |
| 却下・取消理由 | rejection_reason | VARCHAR | - | - | - | 0 | 200 | - | - | - | - | 却下・管理者取消時は必須（アプリ側で検証）。空＝未設定 |
| 承認・却下した管理者ユーザーID | approved_by_user_id | INTEGER | - | - | - | - | - | - | `foreign_key.constraint_name`: fk_loan_request_approved_by_user_id<br>参照先: USER.id<br>ON UPDATE: CASCADE / ON DELETE: RESTRICT<br>カーディナリティ: 多:1 | - | - | 承認・却下時は必須（アプリ側で検証）。空＝未設定 |
| 貸出処理した管理者ユーザーID | lent_by_user_id | INTEGER | - | - | - | - | - | - | `foreign_key.constraint_name`: fk_loan_request_lent_by_user_id<br>参照先: USER.id<br>ON UPDATE: CASCADE / ON DELETE: RESTRICT<br>カーディナリティ: 多:1 | - | - | 貸出時は必須（アプリ側で検証）。空＝未設定 |
| 返却処理した管理者ユーザーID | returned_by_user_id | INTEGER | - | - | - | - | - | - | `foreign_key.constraint_name`: fk_loan_request_returned_by_user_id<br>参照先: USER.id<br>ON UPDATE: CASCADE / ON DELETE: RESTRICT<br>カーディナリティ: 多:1 | - | - | 返却時は必須（アプリ側で検証）。空＝未設定 |
| 取消した者ユーザーID | cancelled_by_user_id | INTEGER | - | - | - | - | - | - | `foreign_key.constraint_name`: fk_loan_request_cancelled_by_user_id<br>参照先: USER.id<br>ON UPDATE: CASCADE / ON DELETE: RESTRICT<br>カーディナリティ: 多:1 | - | - | 取消時は必須（アプリ側で検証）。自動取消（ノーショー）時は空 |
| 申請日時 | requested_at | DATETIME | ○ | - | - | - | - | - | - | - | - | サーバー時刻 |
| 承認・却下日時 | decided_at | DATETIME | - | - | - | - | - | - | - | - | - | 空＝未到達 |
| 貸出日時 | lent_at | DATETIME | - | - | - | - | - | - | - | - | - | 空＝未到達 |
| 返却日時 | returned_at | DATETIME | - | - | - | - | - | - | - | - | - | 空＝未到達 |
| 取消日時 | cancelled_at | DATETIME | - | - | - | - | - | - | - | - | - | 空＝未到達 |
| 返却時状態メモ | return_note | VARCHAR | - | - | - | 0 | 200 | - | - | - | - | 空文字許容（故障・破損等） |

### 補足

- 物理削除は行わない。履歴は本テーブルに保持し、`status`で状態（申請中／承認済み／貸出中／返却済み／却下／取消）を区別する。
- 「期限超過」は列として持たず、`status`＝`lending`かつ`due_date`＜今日（JST）であることから算出する。
- 同一`equipment_id`について、`status`が`approved`または`lending`の申請の`start_date`〜`due_date`が重複する申請の承認は不可とする（オーケストレーション層で検証する。DB制約では表現しない）。

---

## NOTIFICATION

| 項目 | 内容 |
|---|---|
| テーブル論理名 | 通知情報 |
| テーブル物理名 | NOTIFICATION |

### 説明

アプリ内通知（承認・却下・取消・新規申請・返却期限）を管理する。

| 論理名 | 物理名 | 型 | 必須 | 最小値 | 最大値 | 最小桁 | 最大桁 | 主キー | 外部キー | 制約 | インデックス | 備考 |
|---|---|---|:---:|---:|---:|---:|---:|:---:|---|---|---|---|
| 内部ID | id | INTEGER | ○ | - | - | - | - | ○ | - | - | - | 自動採番 |
| 宛先ユーザーID | recipient_user_id | INTEGER | ○ | - | - | - | - | - | `foreign_key.constraint_name`: fk_notification_recipient_user_id<br>参照先: USER.id<br>ON UPDATE: CASCADE / ON DELETE: RESTRICT<br>カーディナリティ: 多:1 | - | - | - |
| 種別 | notification_type | VARCHAR | ○ | - | - | - | - | - | - | ck_notification_notification_type | - | 許容値：`approved`（承認）／`rejected`（却下）／`cancelled`（取消）／`new_request`（新規申請）／`due_reminder`（返却期限） |
| 関連申請ID | loan_request_id | INTEGER | ○ | - | - | - | - | - | `foreign_key.constraint_name`: fk_notification_loan_request_id<br>参照先: LOAN_REQUEST.id<br>ON UPDATE: CASCADE / ON DELETE: RESTRICT<br>カーディナリティ: 多:1 | - | - | - |
| 既読フラグ | is_read | BOOLEAN | ○ | - | - | - | - | - | - | - | - | デフォルト`false`（未読） |
| 作成日時 | created_at | DATETIME | ○ | - | - | - | - | - | - | - | - | サーバー時刻 |

### 補足

- 既読化（`is_read`の更新）のみを行い、更新日時列は設けない。
- 物理削除は行わない。

