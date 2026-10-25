// 貸出申請・承認・貸出・返却・履歴・状況確認API呼び出し（貸出申請・承認、貸出・返却、履歴・状況確認）
//
// 【概要】
// backend/app/main.pyが公開する貸出申請、申請取消、承認待ち申請一覧取得、申請承認、
// 申請却下、管理者申請取消、貸出処理、返却処理、自分申請一覧取得、期限超過一覧取得、
// 貸出履歴検索・取得、貸出履歴CSV出力エンドポイントを呼び出す。

import { apiDownloadRequest, apiRequest } from "./client";
import type {
  LoanLendReturnResponse,
  LoanRequestAdminCancelRequest,
  LoanRequestCreateRequest,
  LoanRequestHistoryListItemResponse,
  LoanRequestHistorySearchParams,
  LoanRequestRejectRequest,
  LoanRequestResponse,
  LoanRequestReturnRequest,
  MyLoanRequestListItemResponse,
  OverdueLoanRequestListItemResponse,
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

export function lendLoanRequest(loanRequestId: number): Promise<LoanLendReturnResponse> {
  return apiRequest<LoanLendReturnResponse>(`/loan-requests/${loanRequestId}/lend`, { method: "PUT" });
}

export function returnLoanRequest(
  loanRequestId: number,
  loanRequestReturnRequest: LoanRequestReturnRequest,
): Promise<LoanLendReturnResponse> {
  return apiRequest<LoanLendReturnResponse>(`/loan-requests/${loanRequestId}/return`, {
    method: "PUT",
    body: loanRequestReturnRequest,
  });
}

export function getMyLoanRequests(): Promise<MyLoanRequestListItemResponse[]> {
  return apiRequest<MyLoanRequestListItemResponse[]>("/loan-requests");
}

export function getOverdueLoanRequests(): Promise<OverdueLoanRequestListItemResponse[]> {
  return apiRequest<OverdueLoanRequestListItemResponse[]>("/loan-requests/overdue");
}

function buildLoanRequestHistoryQuery(params: LoanRequestHistorySearchParams): string {
  const searchParams = new URLSearchParams();
  if (params.start_date_from !== undefined && params.start_date_from !== "") {
    searchParams.set("start_date_from", params.start_date_from);
  }
  if (params.start_date_to !== undefined && params.start_date_to !== "") {
    searchParams.set("start_date_to", params.start_date_to);
  }
  if (params.asset_number !== undefined && params.asset_number !== "") {
    searchParams.set("asset_number", params.asset_number);
  }
  if (params.user_id !== undefined && params.user_id !== "") {
    searchParams.set("user_id", params.user_id);
  }
  return searchParams.toString();
}

export function getLoanRequestHistory(
  params: LoanRequestHistorySearchParams = {},
): Promise<LoanRequestHistoryListItemResponse[]> {
  const query = buildLoanRequestHistoryQuery(params);
  return apiRequest<LoanRequestHistoryListItemResponse[]>(
    query === "" ? "/loan-requests/all" : `/loan-requests/all?${query}`,
  );
}

export function exportLoanRequestHistoryCsv(params: LoanRequestHistorySearchParams = {}): Promise<Blob> {
  const query = buildLoanRequestHistoryQuery(params);
  return apiDownloadRequest(query === "" ? "/loan-requests/all/export" : `/loan-requests/all/export?${query}`);
}
