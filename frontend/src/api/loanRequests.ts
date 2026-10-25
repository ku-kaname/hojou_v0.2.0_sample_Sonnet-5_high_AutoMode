// 貸出申請・承認API呼び出し（貸出申請・承認）
//
// 【概要】
// backend/app/main.pyが公開する貸出申請、申請取消、承認待ち申請一覧取得、申請承認、
// 申請却下、管理者申請取消エンドポイントを呼び出す。

import { apiRequest } from "./client";
import type {
  LoanRequestAdminCancelRequest,
  LoanRequestCreateRequest,
  LoanRequestRejectRequest,
  LoanRequestResponse,
  PendingLoanRequestListItemResponse,
} from "../types/api";

export function createLoanRequest(loanRequestCreateRequest: LoanRequestCreateRequest): Promise<LoanRequestResponse> {
  return apiRequest<LoanRequestResponse>("/loan-requests", { method: "POST", body: loanRequestCreateRequest });
}

export function cancelLoanRequest(loanRequestId: number): Promise<LoanRequestResponse> {
  return apiRequest<LoanRequestResponse>(`/loan-requests/${loanRequestId}/cancel`, { method: "PUT" });
}

export function getPendingLoanRequests(): Promise<PendingLoanRequestListItemResponse[]> {
  return apiRequest<PendingLoanRequestListItemResponse[]>("/loan-requests/pending");
}

export function approveLoanRequest(loanRequestId: number): Promise<LoanRequestResponse> {
  return apiRequest<LoanRequestResponse>(`/loan-requests/${loanRequestId}/approve`, { method: "PUT" });
}

export function rejectLoanRequest(
  loanRequestId: number,
  loanRequestRejectRequest: LoanRequestRejectRequest,
): Promise<LoanRequestResponse> {
  return apiRequest<LoanRequestResponse>(`/loan-requests/${loanRequestId}/reject`, {
    method: "PUT",
    body: loanRequestRejectRequest,
  });
}

export function adminCancelLoanRequest(
  loanRequestId: number,
  loanRequestAdminCancelRequest: LoanRequestAdminCancelRequest,
): Promise<LoanRequestResponse> {
  return apiRequest<LoanRequestResponse>(`/loan-requests/${loanRequestId}/admin-cancel`, {
    method: "PUT",
    body: loanRequestAdminCancelRequest,
  });
}
