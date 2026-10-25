// 申請管理画面（S07、F09・F12）
//
// 【概要】
// 管理者が、承認待ちの貸出申請一覧を確認して承認・却下を行い、承認済みの申請を取消する画面。
// 貸出処理・返却処理（F10・F11）は実装（貸出・返却）バックログで本画面に追加する。

import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  adminCancelLoanRequest,
  approveLoanRequest,
  getPendingLoanRequests,
  rejectLoanRequest,
} from "../api/loanRequests";
import { ApiError } from "../api/client";
import type { LoanRequestResponse, PendingLoanRequestListItemResponse } from "../types/api";

export function RequestManagementPage() {
  const [pendingLoanRequests, setPendingLoanRequests] = useState<PendingLoanRequestListItemResponse[]>([]);
  const [listErrorMessage, setListErrorMessage] = useState<string | null>(null);
  const [isLoadingList, setIsLoadingList] = useState(true);

  const [rejectingLoanRequestId, setRejectingLoanRequestId] = useState<number | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");
  const [actionErrorMessage, setActionErrorMessage] = useState<string | null>(null);

  const [adminCancelLoanRequestIdInput, setAdminCancelLoanRequestIdInput] = useState("");
  const [cancellationReason, setCancellationReason] = useState("");
  const [cancelledLoanRequest, setCancelledLoanRequest] = useState<LoanRequestResponse | null>(null);
  const [cancelErrorMessage, setCancelErrorMessage] = useState<string | null>(null);
  const [isCancelling, setIsCancelling] = useState(false);

  const loadPendingLoanRequests = useCallback(async () => {
    setIsLoadingList(true);
    setListErrorMessage(null);
    try {
      const fetchedPendingLoanRequests = await getPendingLoanRequests();
      setPendingLoanRequests(fetchedPendingLoanRequests);
    } catch (error) {
      setListErrorMessage(error instanceof ApiError ? error.message : "承認待ち申請一覧の取得に失敗しました");
    } finally {
      setIsLoadingList(false);
    }
  }, []);

  useEffect(() => {
    void loadPendingLoanRequests();
  }, [loadPendingLoanRequests]);

  async function handleApprove(loanRequestId: number) {
    setActionErrorMessage(null);
    try {
      await approveLoanRequest(loanRequestId);
      await loadPendingLoanRequests();
    } catch (error) {
      setActionErrorMessage(error instanceof ApiError ? error.message : "申請の承認に失敗しました");
    }
  }

  function handleStartReject(loanRequestId: number) {
    setRejectingLoanRequestId(loanRequestId);
    setRejectionReason("");
    setActionErrorMessage(null);
  }

  async function handleConfirmReject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (rejectingLoanRequestId === null) {
      return;
    }
    setActionErrorMessage(null);
    try {
      await rejectLoanRequest(rejectingLoanRequestId, { rejection_reason: rejectionReason });
      setRejectingLoanRequestId(null);
      setRejectionReason("");
      await loadPendingLoanRequests();
    } catch (error) {
      setActionErrorMessage(error instanceof ApiError ? error.message : "申請の却下に失敗しました");
    }
  }

  async function handleAdminCancelLoanRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const loanRequestId = Number(adminCancelLoanRequestIdInput);
    setCancelErrorMessage(null);
    setCancelledLoanRequest(null);
    setIsCancelling(true);
    try {
      const loanRequest = await adminCancelLoanRequest(loanRequestId, { cancellation_reason: cancellationReason });
      setCancelledLoanRequest(loanRequest);
      setAdminCancelLoanRequestIdInput("");
      setCancellationReason("");
    } catch (error) {
      setCancelErrorMessage(error instanceof ApiError ? error.message : "申請の取消に失敗しました");
    } finally {
      setIsCancelling(false);
    }
  }

  return (
    <div className="request-management-page">
      <h1>申請管理</h1>

      <section>
        <h2>承認待ち申請一覧</h2>
        {isLoadingList && <p>読み込み中...</p>}
        {listErrorMessage !== null && <p className="error-message">{listErrorMessage}</p>}
        {actionErrorMessage !== null && <p className="error-message">{actionErrorMessage}</p>}
        {!isLoadingList && pendingLoanRequests.length === 0 && <p>承認待ちの申請はありません</p>}
        {pendingLoanRequests.length > 0 && (
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
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {pendingLoanRequests.map((pendingLoanRequest) => (
                <tr key={pendingLoanRequest.id}>
                  <td>{pendingLoanRequest.id}</td>
                  <td>{pendingLoanRequest.asset_number}</td>
                  <td>{pendingLoanRequest.equipment_name}</td>
                  <td>{pendingLoanRequest.applicant_name}</td>
                  <td>{pendingLoanRequest.start_date}</td>
                  <td>{pendingLoanRequest.due_date}</td>
                  <td>{pendingLoanRequest.purpose}</td>
                  <td>
                    <button type="button" onClick={() => void handleApprove(pendingLoanRequest.id)}>
                      承認
                    </button>
                    <button type="button" onClick={() => handleStartReject(pendingLoanRequest.id)}>
                      却下
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      {rejectingLoanRequestId !== null && (
        <section>
          <h2>申請却下（申請ID：{rejectingLoanRequestId}）</h2>
          <form onSubmit={handleConfirmReject}>
            <div>
              <label htmlFor="rejection_reason">却下理由</label>
              <input
                id="rejection_reason"
                type="text"
                value={rejectionReason}
                onChange={(event) => setRejectionReason(event.target.value)}
                maxLength={200}
                required
              />
            </div>
            <button type="submit">却下する</button>
            <button type="button" onClick={() => setRejectingLoanRequestId(null)}>
              キャンセル
            </button>
          </form>
        </section>
      )}

      <section>
        <h2>承認済み申請の取消</h2>
        <p>取消する申請のIDを入力してください。取消できるのは承認済みの申請のみです。</p>
        <form onSubmit={handleAdminCancelLoanRequest}>
          <div>
            <label htmlFor="admin_cancel_loan_request_id">申請ID</label>
            <input
              id="admin_cancel_loan_request_id"
              type="number"
              min={1}
              value={adminCancelLoanRequestIdInput}
              onChange={(event) => setAdminCancelLoanRequestIdInput(event.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="cancellation_reason">取消理由</label>
            <input
              id="cancellation_reason"
              type="text"
              value={cancellationReason}
              onChange={(event) => setCancellationReason(event.target.value)}
              maxLength={200}
              required
            />
          </div>
          {cancelErrorMessage !== null && <p className="error-message">{cancelErrorMessage}</p>}
          <button type="submit" disabled={isCancelling}>
            取消する
          </button>
        </form>
      </section>

      {cancelledLoanRequest !== null && (
        <section>
          <h2>取消結果</h2>
          <p className="success-message">
            申請ID {cancelledLoanRequest.id}（{cancelledLoanRequest.equipment_name}）を取消しました。
          </p>
        </section>
      )}
    </div>
  );
}
