// 申請管理画面（S07、F09・F10・F11・F12）
//
// 【概要】
// 管理者が、承認待ちの貸出申請一覧を確認して承認・却下を行い、承認済みの申請を取消する画面。
// 承認済みの申請の貸出処理、貸出中の申請の返却処理も本画面から行う。

import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  adminCancelLoanRequest,
  approveLoanRequest,
  getPendingLoanRequests,
  lendLoanRequest,
  rejectLoanRequest,
  returnLoanRequest,
} from "../api/loanRequests";
import { ApiError } from "../api/client";
import type { LoanLendReturnResponse, LoanRequestResponse, PendingLoanRequestListItemResponse } from "../types/api";

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

  const [lendLoanRequestIdInput, setLendLoanRequestIdInput] = useState("");
  const [lentLoanRequest, setLentLoanRequest] = useState<LoanLendReturnResponse | null>(null);
  const [lendErrorMessage, setLendErrorMessage] = useState<string | null>(null);
  const [isLending, setIsLending] = useState(false);

  const [returnLoanRequestIdInput, setReturnLoanRequestIdInput] = useState("");
  const [returnNote, setReturnNote] = useState("");
  const [returnedLoanRequest, setReturnedLoanRequest] = useState<LoanLendReturnResponse | null>(null);
  const [returnErrorMessage, setReturnErrorMessage] = useState<string | null>(null);
  const [isReturning, setIsReturning] = useState(false);

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

  async function handleLendLoanRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const loanRequestId = Number(lendLoanRequestIdInput);
    setLendErrorMessage(null);
    setLentLoanRequest(null);
    setIsLending(true);
    try {
      const loanRequest = await lendLoanRequest(loanRequestId);
      setLentLoanRequest(loanRequest);
      setLendLoanRequestIdInput("");
    } catch (error) {
      setLendErrorMessage(error instanceof ApiError ? error.message : "貸出処理に失敗しました");
    } finally {
      setIsLending(false);
    }
  }

  async function handleReturnLoanRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const loanRequestId = Number(returnLoanRequestIdInput);
    setReturnErrorMessage(null);
    setReturnedLoanRequest(null);
    setIsReturning(true);
    try {
      const loanRequest = await returnLoanRequest(loanRequestId, { return_note: returnNote === "" ? null : returnNote });
      setReturnedLoanRequest(loanRequest);
      setReturnLoanRequestIdInput("");
      setReturnNote("");
    } catch (error) {
      setReturnErrorMessage(error instanceof ApiError ? error.message : "返却処理に失敗しました");
    } finally {
      setIsReturning(false);
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

      <section>
        <h2>貸出処理</h2>
        <p>貸出処理を行う申請のIDを入力してください。貸出処理できるのは承認済みの申請のみです。</p>
        <form onSubmit={handleLendLoanRequest}>
          <div>
            <label htmlFor="lend_loan_request_id">申請ID</label>
            <input
              id="lend_loan_request_id"
              type="number"
              min={1}
              value={lendLoanRequestIdInput}
              onChange={(event) => setLendLoanRequestIdInput(event.target.value)}
              required
            />
          </div>
          {lendErrorMessage !== null && <p className="error-message">{lendErrorMessage}</p>}
          <button type="submit" disabled={isLending}>
            貸出する
          </button>
        </form>
      </section>

      {lentLoanRequest !== null && (
        <section>
          <h2>貸出結果</h2>
          <p className="success-message">
            申請ID {lentLoanRequest.id}（{lentLoanRequest.equipment_name}）を貸出しました（貸出日時：
            {lentLoanRequest.lent_at}）。
          </p>
        </section>
      )}

      <section>
        <h2>返却処理</h2>
        <p>返却処理を行う申請のIDを入力してください。返却処理できるのは貸出中の申請のみです。</p>
        <form onSubmit={handleReturnLoanRequest}>
          <div>
            <label htmlFor="return_loan_request_id">申請ID</label>
            <input
              id="return_loan_request_id"
              type="number"
              min={1}
              value={returnLoanRequestIdInput}
              onChange={(event) => setReturnLoanRequestIdInput(event.target.value)}
              required
            />
          </div>
          <div>
            <label htmlFor="return_note">返却時メモ</label>
            <textarea
              id="return_note"
              value={returnNote}
              onChange={(event) => setReturnNote(event.target.value)}
              maxLength={200}
            />
          </div>
          {returnErrorMessage !== null && <p className="error-message">{returnErrorMessage}</p>}
          <button type="submit" disabled={isReturning}>
            返却する
          </button>
        </form>
      </section>

      {returnedLoanRequest !== null && (
        <section>
          <h2>返却結果</h2>
          <p className="success-message">
            申請ID {returnedLoanRequest.id}（{returnedLoanRequest.equipment_name}）を返却しました（返却日時：
            {returnedLoanRequest.returned_at}）。
          </p>
        </section>
      )}
    </div>
  );
}
