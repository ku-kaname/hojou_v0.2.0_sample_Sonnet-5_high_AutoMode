import assert from "node:assert/strict";
import { test } from "node:test";

import { isApiRowErrorList } from "./client.ts";

// ==================================================
// 行エラー一覧判定
// テスト対象ファイル：client.ts
// テスト対象クラス：-
// テスト対象メソッド：isApiRowErrorList
// テスト仕様書：テスト仕様書/単体テスト仕様書/フロントエンド（frontend）/共通/行エラー一覧判定_単体テスト仕様書.md
// ==================================================

// ========== 単体テストNo.1 ==========
// row_numberが数値、error_messageが文字列の要素のみからなる配列の場合、trueが返ること
test("test_isApiRowErrorList_001_valid_row_error_list", () => {
  const data = [
    { row_number: 1, error_message: "資産番号は既に登録されています" },
    { row_number: 2, error_message: "備品名は1〜100文字で入力してください" },
  ];

  assert.equal(isApiRowErrorList(data), true);
});

// ========== 単体テストNo.2 ==========
// 空配列の場合、要素の検証が行われずtrueが返ること
test("test_isApiRowErrorList_002_empty_array", () => {
  assert.equal(isApiRowErrorList([]), true);
});

// ========== 単体テストNo.3 ==========
// 配列でない値（オブジェクト）の場合、falseが返ること
test("test_isApiRowErrorList_003_not_array_object", () => {
  assert.equal(isApiRowErrorList({ detail: "エラーです" }), false);
});

// ========== 単体テストNo.4 ==========
// 配列でない値（文字列・null）の場合、いずれもfalseが返ること
test("test_isApiRowErrorList_004_not_array_string_or_null", () => {
  assert.equal(isApiRowErrorList("エラーです"), false);
  assert.equal(isApiRowErrorList(null), false);
});

// ========== 単体テストNo.5 ==========
// 配列だが、要素のrow_numberが数値でない場合、falseが返ること
test("test_isApiRowErrorList_005_row_number_not_number", () => {
  const data = [{ row_number: "1", error_message: "エラー" }];

  assert.equal(isApiRowErrorList(data), false);
});

// ========== 単体テストNo.6 ==========
// 配列の要素がnullまたはオブジェクトでない場合、いずれもfalseが返ること
test("test_isApiRowErrorList_006_element_not_object", () => {
  assert.equal(isApiRowErrorList([null]), false);
  assert.equal(isApiRowErrorList(["エラー"]), false);
});

// ========== 単体テストNo.7 ==========
// 配列中の一部の要素のみ形状が不正な場合、falseが返ること
test("test_isApiRowErrorList_007_partially_invalid_elements", () => {
  const data = [
    { row_number: 1, error_message: "正常" },
    { row_number: 2, error_message: 123 },
  ];

  assert.equal(isApiRowErrorList(data), false);
});
