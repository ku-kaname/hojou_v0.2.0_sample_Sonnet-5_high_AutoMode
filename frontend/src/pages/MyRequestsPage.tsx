// 自分の申請一覧画面（S05、F06・F07）
//
// 【概要】
// 自分の貸出申請の状態・履歴の一覧表示（F07）と、自分の貸出申請の取消（F06）を行う画面。
// 取消対象は、備品詳細画面（F05）での申請時、または通知で知らされた申請IDを指定する。

import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { cancelLoanRequest, getMyLoanRequests } from "../api/loanRequests";
import { ApiError } from "../api/client";
import type { LoanRequestResponse, MyLoanRequestListItemResponse } from "../types/api";

const STATUS_LABELS: Record<string, string> = {
  pending: "申請中",
  approved: "承認済み",
  lending: "貸出中",
  returned: "返却済み",
  rejected: "却下",
  cancelled: "取消済み",
};

export function MyRequestsPage() {
  const [myLoanRequests, setMyLoanRequests] = useState<MyLoanRequestListItemResponse[]>([]);
  const [listErrorMessage, setListErrorMessage] = useState<string | null>(null);
  const [isLoadingList, setIsLoadingList] = useState(true);

  const [loanRequestIdInput, setLoanRequestIdInput] = useState("");
  const [cancelledLoanRequest, setCancelledLoanRequest] = useState<LoanRequestResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isCancelling, setIsCancelling] = useState(false);

  const loadMyLoanRequests = useCallback(async () => {
    setIsLoadingList(true);
    setListErrorMessage(null);
    try {
      const fetchedMyLoanRequests = await getMyLoanRequests();
      setMyLoanRequests(fetchedMyLoanRequests);
    } catch (error) {
      setListErrorMessage(error instanceof ApiError ? error.message : "自分の申請一覧の取得に失敗しました");
    } finally {
      setIsLoadingList(false);
    }
  }, []);

  useEffect(() => {
    void loadMyLoanRequests();
  }, [loadMyLoanRequests]);

  async function handleCancelLoanRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const loanRequestId = Number(loanRequestIdInput);
    setErrorMessage(null);
    setCancelledLoanRequest(null);
    setIsCancelling(true);
    try {
      const loanRequest = await cancelLoanRequest(loanRequestId);
      setCancelledLoanRequest(loanRequest);
      setLoanRequestIdInput("");
      await loadMyLoanRequests();
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "貸出申請の取消に失敗しました");
    } finally {
      setIsCancelling(false);
    }
  }

  return (
    <div className="my-requests-page">
      <h1>自分の申請一覧</h1>

      <section>
        <h2>申請状況一覧</h2>
        {isLoadingList && <p>読み込み中...</p>}
        {listErrorMessage !== null && <p className="error-message">{listErrorMessage}</p>}
        {!isLoadingList && myLoanRequests.length === 0 && <p>申請はありません</p>}
        {myLoanRequests.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>申請ID</th>
                <th>資産番号</th>
                <th>備品名</th>
                <th>開始日</th>
                <th>返却予定日</th>
                <th>用途</th>
                <th>状態</th>
                <th>却下・取消理由</th>
                <th>申請日時</th>
              </tr>
            </thead>
            <tbody>
              {myLoanRequests.map((myLoanRequest) => (
                <tr key={myLoanRequest.id}>
                  <td>{myLoanRequest.id}</td>
                  <td>{myLoanRequest.asset_number}</td>
                  <td>{myLoanRequest.equipment_name}</td>
                  <td>{myLoanRequest.start_date}</td>
                  <td>{myLoanRequest.due_date}</td>
                  <td>{myLoanRequest.purpose}</td>
                  <td>{STATUS_LABELS[myLoanRequest.status]}</td>
                  <td>{myLoanRequest.rejection_reason ?? ""}</td>
                  <td>{myLoanRequest.requested_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section>
        <h2>申請取消</h2>
        <p>取消する申請のIDを入力してください（申請時または通知に表示された申請IDです）。</p>
        <form onSubmit={handleCancelLoanRequest}>
          <div>
            <label htmlFor="cancel_loan_request_id">申請ID</label>
            <input
              id="cancel_loan_request_id"
              type="number"
              min={1}
              value={loanRequestIdInput}
              onChange={(event) => setLoanRequestIdInput(event.target.value)}
              required
            />
          </div>
          {errorMessage !== null && <p className="error-message">{errorMessage}</p>}
          <button type="submit" disabled={isCancelling}>
            取消する
          </button>
        </form>
      </section>

      {cancelledLoanRequest !== null && (
        <section>
          <h2>取消結果</h2>
          <table>
            <tbody>
              <tr>
                <th>申請ID</th>
                <td>{cancelledLoanRequest.id}</td>
              </tr>
              <tr>
                <th>資産番号</th>
                <td>{cancelledLoanRequest.asset_number}</td>
              </tr>
              <tr>
                <th>備品名</th>
                <td>{cancelledLoanRequest.equipment_name}</td>
              </tr>
              <tr>
                <th>開始日</th>
                <td>{cancelledLoanRequest.start_date}</td>
              </tr>
              <tr>
                <th>返却予定日</th>
                <td>{cancelledLoanRequest.due_date}</td>
              </tr>
              <tr>
                <th>状態</th>
                <td>{STATUS_LABELS[cancelledLoanRequest.status]}</td>
              </tr>
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
