// 期限超過一覧画面（S08、F13）
//
// 【概要】
// 管理者が、返却予定日を過ぎた貸出（貸出中かつ返却予定日が本日より前）の一覧を確認する画面。

import { useCallback, useEffect, useState } from "react";
import { getOverdueLoanRequests } from "../api/loanRequests";
import { ApiError } from "../api/client";
import type { OverdueLoanRequestListItemResponse } from "../types/api";

export function OverdueLoanRequestsPage() {
  const [overdueLoanRequests, setOverdueLoanRequests] = useState<OverdueLoanRequestListItemResponse[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const loadOverdueLoanRequests = useCallback(async () => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const fetchedOverdueLoanRequests = await getOverdueLoanRequests();
      setOverdueLoanRequests(fetchedOverdueLoanRequests);
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "期限超過一覧の取得に失敗しました");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadOverdueLoanRequests();
  }, [loadOverdueLoanRequests]);

  return (
    <div className="overdue-loan-requests-page">
      <h1>期限超過一覧</h1>

      {isLoading && <p>読み込み中...</p>}
      {errorMessage !== null && <p className="error-message">{errorMessage}</p>}
      {!isLoading && overdueLoanRequests.length === 0 && <p>期限超過の貸出はありません</p>}
      {overdueLoanRequests.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>申請ID</th>
              <th>資産番号</th>
              <th>備品名</th>
              <th>申請者</th>
              <th>開始日</th>
              <th>返却予定日</th>
              <th>用途</th>
              <th>貸出日時</th>
              <th>超過日数</th>
            </tr>
          </thead>
          <tbody>
            {overdueLoanRequests.map((overdueLoanRequest) => (
              <tr key={overdueLoanRequest.id}>
                <td>{overdueLoanRequest.id}</td>
                <td>{overdueLoanRequest.asset_number}</td>
                <td>{overdueLoanRequest.equipment_name}</td>
                <td>{overdueLoanRequest.applicant_name}</td>
                <td>{overdueLoanRequest.start_date}</td>
                <td>{overdueLoanRequest.due_date}</td>
                <td>{overdueLoanRequest.purpose}</td>
                <td>{overdueLoanRequest.lent_at}</td>
                <td>{overdueLoanRequest.overdue_days}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
