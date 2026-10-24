// 備品一覧画面（S03、F03）
//
// 【概要】
// 認証済みユーザーが、分類・キーワードで備品を検索し、一覧（現在の貸出状況を含む）を確認する画面。
// 管理者のみ、有効フラグによる絞り込みと無効化済み備品の表示が可能。

import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link } from "react-router-dom";
import { searchEquipment } from "../api/equipment";
import { ApiError } from "../api/client";
import { useAuth } from "../context/useAuth";
import type { EquipmentListItemResponse } from "../types/api";

type ActiveFilter = "all" | "active" | "inactive";

export function EquipmentListPage() {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";

  const [equipmentList, setEquipmentList] = useState<EquipmentListItemResponse[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const [category, setCategory] = useState("");
  const [keyword, setKeyword] = useState("");
  const [activeFilter, setActiveFilter] = useState<ActiveFilter>("all");

  const loadEquipmentList = useCallback(
    async (searchCategory: string, searchKeyword: string, searchActiveFilter: ActiveFilter) => {
      setIsLoading(true);
      setErrorMessage(null);
      try {
        const fetchedEquipmentList = await searchEquipment({
          category: searchCategory === "" ? undefined : searchCategory,
          keyword: searchKeyword === "" ? undefined : searchKeyword,
          is_active:
            searchActiveFilter === "all" ? undefined : searchActiveFilter === "active",
        });
        setEquipmentList(fetchedEquipmentList);
      } catch (error) {
        setErrorMessage(error instanceof ApiError ? error.message : "備品一覧の取得に失敗しました");
      } finally {
        setIsLoading(false);
      }
    },
    [],
  );

  useEffect(() => {
    void loadEquipmentList("", "", "all");
  }, [loadEquipmentList]);

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void loadEquipmentList(category, keyword, activeFilter);
  }

  return (
    <div className="equipment-list-page">
      <h1>備品一覧</h1>

      <form onSubmit={handleSearch}>
        <div>
          <label htmlFor="search_category">分類</label>
          <input
            id="search_category"
            type="text"
            value={category}
            onChange={(event) => setCategory(event.target.value)}
            maxLength={50}
          />
        </div>
        <div>
          <label htmlFor="search_keyword">キーワード</label>
          <input
            id="search_keyword"
            type="text"
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            maxLength={100}
          />
        </div>
        {isAdmin && (
          <div>
            <label htmlFor="search_active_filter">状態</label>
            <select
              id="search_active_filter"
              value={activeFilter}
              onChange={(event) => setActiveFilter(event.target.value as ActiveFilter)}
            >
              <option value="all">すべて</option>
              <option value="active">有効</option>
              <option value="inactive">無効</option>
            </select>
          </div>
        )}
        <button type="submit">検索する</button>
      </form>

      {isLoading && <p>読み込み中...</p>}
      {errorMessage !== null && <p className="error-message">{errorMessage}</p>}
      {!isLoading && equipmentList.length === 0 && <p>該当する備品がありません</p>}
      {equipmentList.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>資産番号</th>
              <th>名称</th>
              <th>分類</th>
              <th>保管場所</th>
              {isAdmin && <th>状態</th>}
              <th>貸出状況</th>
              <th>返却期限</th>
            </tr>
          </thead>
          <tbody>
            {equipmentList.map((equipment) => (
              <tr key={equipment.asset_number}>
                <td>
                  <Link to={`/equipment/${equipment.asset_number}`}>{equipment.asset_number}</Link>
                </td>
                <td>{equipment.name}</td>
                <td>{equipment.category}</td>
                <td>{equipment.location ?? "-"}</td>
                {isAdmin && <td>{equipment.is_active ? "有効" : "無効"}</td>}
                <td>{equipment.lending_status === "lending" ? "貸出中" : "貸出可能"}</td>
                <td>{equipment.due_date ?? "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
