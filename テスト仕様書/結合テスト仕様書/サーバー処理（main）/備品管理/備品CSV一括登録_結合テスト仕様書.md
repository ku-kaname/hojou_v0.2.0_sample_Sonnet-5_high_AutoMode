| 項目 | 内容 |
|---|---|
| HTTPメソッド | POST |
| エンドポイント | /equipment/bulk-import |
| 作成日 | 2026-10-26 |
| 最終更新日 | 2026-10-26 |

| 項番 | テスト項目 | 前提条件 | 入力値 | 想定結果 | エビデンス | 担当者 | 実施日 | 実施結果 | 再鑑者 | 再鑑日 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 正常系 - 全項目を指定した2行の正常なCSVで一括登録する | 管理者ユーザーが登録済み、未登録の資産番号2件を含むCSV（ヘッダー「資産番号,備品名,分類,説明,保管場所」＋データ2行、全項目指定） | POST /equipment/bulk-import（管理者トークン、multipart/form-data、CSVファイル） | HTTP 200<br>{"registered_count": 2}<br>DBに2件登録されること | - | - | - | - | - | - |
| 2 | 正常系 - 説明・保管場所を空欄にしたデータ行を含むCSVで一括登録する | 管理者ユーザーが登録済み、説明・保管場所列が空文字のデータ1行を含むCSV | POST /equipment/bulk-import（管理者トークン、multipart/form-data、CSVファイル） | HTTP 200<br>{"registered_count": 1}<br>登録された備品のdescription=null、location=nullであること | - | - | - | - | - | - |
| 3 | 異常系 - ファイルサイズが5MBを超えるCSVをアップロードする | 管理者ユーザーが登録済み | POST /equipment/bulk-import（管理者トークン、multipart/form-data、5MB超のCSVファイル） | HTTP 400<br>{"detail": "ファイルサイズは5MB以内にしてください"} | - | - | - | - | - | - |
| 4 | 異常系 - ヘッダー列が不正な（列名・順序が異なる）CSVをアップロードする | 管理者ユーザーが登録済み | POST /equipment/bulk-import（管理者トークン、multipart/form-data、ヘッダーが「資産番号,備品名,分類」のみのCSVファイル） | HTTP 400<br>{"detail": "CSVのヘッダー列が不正です（資産番号・備品名・分類・説明・保管場所の順で指定してください）"} | - | - | - | - | - | - |
| 5 | 異常系 - データ行数が1,000行を超えるCSVをアップロードする | 管理者ユーザーが登録済み | POST /equipment/bulk-import（管理者トークン、multipart/form-data、正しいヘッダー＋データ1,001行のCSVファイル） | HTTP 400<br>{"detail": "データ行数は1,000行以内にしてください"} | - | - | - | - | - | - |
| 6 | 異常系 - 資産番号が33文字（上限超過）のデータ行を含むCSVをアップロードする | 管理者ユーザーが登録済み | POST /equipment/bulk-import（管理者トークン、multipart/form-data、資産番号が33文字のデータ1行を含むCSVファイル） | HTTP 400<br>detail（リスト）に該当行番号・"資産番号は32文字以内の半角英数字と`-`で入力してください"を含むこと | - | - | - | - | - | - |
| 7 | 異常系 - 資産番号に許可されない文字（記号等）を含むデータ行を含むCSVをアップロードする | 管理者ユーザーが登録済み | POST /equipment/bulk-import（管理者トークン、multipart/form-data、資産番号が「AST#001」のデータ1行を含むCSVファイル） | HTTP 400<br>detail（リスト）に該当行番号・"資産番号は32文字以内の半角英数字と`-`で入力してください"を含むこと | - | - | - | - | - | - |
| 8 | 異常系 - 備品名が空のデータ行を含むCSVをアップロードする | 管理者ユーザーが登録済み | POST /equipment/bulk-import（管理者トークン、multipart/form-data、備品名列が空文字のデータ1行を含むCSVファイル） | HTTP 400<br>detail（リスト）に該当行番号・"備品名は1〜100文字で入力してください"を含むこと | - | - | - | - | - | - |
| 9 | 異常系 - 備品名が101文字（上限超過）のデータ行を含むCSVをアップロードする | 管理者ユーザーが登録済み | POST /equipment/bulk-import（管理者トークン、multipart/form-data、備品名が101文字のデータ1行を含むCSVファイル） | HTTP 400<br>detail（リスト）に該当行番号・"備品名は1〜100文字で入力してください"を含むこと | - | - | - | - | - | - |
| 10 | 異常系 - 分類が空のデータ行を含むCSVをアップロードする | 管理者ユーザーが登録済み | POST /equipment/bulk-import（管理者トークン、multipart/form-data、分類列が空文字のデータ1行を含むCSVファイル） | HTTP 400<br>detail（リスト）に該当行番号・"分類は1〜50文字で入力してください"を含むこと | - | - | - | - | - | - |
| 11 | 異常系 - 説明が501文字（上限超過）のデータ行を含むCSVをアップロードする | 管理者ユーザーが登録済み | POST /equipment/bulk-import（管理者トークン、multipart/form-data、説明が501文字のデータ1行を含むCSVファイル） | HTTP 400<br>detail（リスト）に該当行番号・"説明は500文字以内で入力してください"を含むこと | - | - | - | - | - | - |
| 12 | 異常系 - 保管場所が101文字（上限超過）のデータ行を含むCSVをアップロードする | 管理者ユーザーが登録済み | POST /equipment/bulk-import（管理者トークン、multipart/form-data、保管場所が101文字のデータ1行を含むCSVファイル） | HTTP 400<br>detail（リスト）に該当行番号・"保管場所は100文字以内で入力してください"を含むこと | - | - | - | - | - | - |
| 13 | 異常系 - ファイル内で資産番号が重複する2行を含むCSVをアップロードする | 管理者ユーザーが登録済み | POST /equipment/bulk-import（管理者トークン、multipart/form-data、同一資産番号のデータ2行を含むCSVファイル） | HTTP 400<br>detail（リスト）に両行の行番号・"資産番号がファイル内で重複しています"を含むこと | - | - | - | - | - | - |
| 14 | 異常系 - DB内に既に存在する資産番号のデータ行を含むCSVをアップロードする | 管理者ユーザーおよび登録済みの備品（資産番号「AST-001」）が登録済み | POST /equipment/bulk-import（管理者トークン、multipart/form-data、資産番号が「AST-001」のデータ1行を含むCSVファイル） | HTTP 400<br>detail（リスト）に該当行番号・"資産番号は既に登録されています"を含むこと | - | - | - | - | - | - |
| 15 | 異常系 - 1行でもエラーがある場合、他の正常行も含め全件登録されないことを確認する | 管理者ユーザーおよび登録済みの備品（資産番号「AST-002」）が登録済み、未登録の資産番号1件（正常行）＋「AST-002」（DB重複エラー行）の2行を含むCSV | POST /equipment/bulk-import（管理者トークン、multipart/form-data、CSVファイル） | HTTP 400<br>正常行側の資産番号がDBに登録されていないこと（全件登録されないこと） | - | - | - | - | - | - |
| 16 | 異常系 - 管理者権限でないユーザーがアップロードする | 一般ユーザーが登録済み | POST /equipment/bulk-import（一般ユーザートークン、multipart/form-data、正常なCSVファイル） | HTTP 403<br>{"detail": "この操作には管理者権限が必要です"} | - | - | - | - | - | - |
| 17 | 異常系 - 初回パスワード変更未完了の管理者がアップロードする | 管理者ユーザー（must_change_password=true）が登録済み | POST /equipment/bulk-import（当該管理者トークン、multipart/form-data、正常なCSVファイル） | HTTP 403<br>{"detail": "初回パスワードの変更が完了していません。パスワードを変更してください"} | - | - | - | - | - | - |
| 18 | 異常系 - トークン未指定でアップロードする | - | POST /equipment/bulk-import（Authorizationヘッダーなし、multipart/form-data、正常なCSVファイル） | HTTP 401 | - | - | - | - | - | - |
| 19 | 異常系 - CSVファイル（file）を指定せずにアップロードする | 管理者ユーザーが登録済み | POST /equipment/bulk-import（管理者トークン、multipart/form-data、fileフィールドなし） | HTTP 422（FastAPI標準の必須パラメータエラー） | - | - | - | - | - | - |
