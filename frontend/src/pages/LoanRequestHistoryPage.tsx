// 貸出履歴画面（S11、F17）
//
// 【概要】
// 管理者が、全貸出申請の履歴を期間・資産番号・申請者IDで検索・閲覧し、CSV出力する画面。

import { useState } from "react";
import type { FormEvent } from "react";
import { exportLoanRequestHistoryCsv, getLoanRequestHistory } from "../api/loanRequests";
import { ApiError } from "../api/client";
import type { LoanRequestHistoryListItemResponse, LoanRequestHistorySearchParams } from "../types/api";

const STATUS_LABELS: Record<string, string> = {
  pending: "申請中",
  approved: "承認済み",
  lending: "貸出中",
  returned: "返却済み",
  rejected: "却下",
  cancelled: "取消済み",
};

function downloadCsvBlob(csvBlob: Blob, fileName: string) {
  const objectUrl = URL.createObjectURL(csvBlob);
  const downloadLink = document.createElement("a");
  downloadLink.href = objectUrl;
  downloadLink.download = fileName;
  document.body.appendChild(downloadLink);
  downloadLink.click();
  document.body.removeChild(downloadLink);
  URL.revokeObjectURL(objectUrl);
}

export function LoanRequestHistoryPage() {
  const [startDateFrom, setStartDateFrom] = useState("");
  const [startDateTo, setStartDateTo] = useState("");
  const [assetNumber, setAssetNumber] = useState("");
  const [userId, setUserId] = useState("");

  const [loanRequestHistoryList, setLoanRequestHistoryList] = useState<LoanRequestHistoryListItemResponse[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [isExporting, setIsExporting] = useState(false);

  function buildSearchParams(): LoanRequestHistorySearchParams {
    return {
      start_date_from: startDateFrom === "" ? undefined : startDateFrom,
      start_date_to: startDateTo === "" ? undefined : startDateTo,
      asset_number: assetNumber === "" ? undefined : assetNumber,
      user_id: userId === "" ? undefined : userId,
    };
  }

  async function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setIsSearching(true);
    try {
      const fetchedLoanRequestHistoryList = await getLoanRequestHistory(buildSearchParams());
      setLoanRequestHistoryList(fetchedLoanRequestHistoryList);
      setHasSearched(true);
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "貸出履歴の検索に失敗しました");
    } finally {
      setIsSearching(false);
    }
  }

  async function handleExportCsv() {
    setErrorMessage(null);
    setIsExporting(true);
    try {
      const csvBlob = await exportLoanRequestHistoryCsv(buildSearchParams());
      downloadCsvBlob(csvBlob, "loan_history.csv");
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "貸出履歴のCSV出力に失敗しました");
    } finally {
      setIsExporting(false);
    }
  }

  return (
    <div className="loan-request-history-page">
      <h1>貸出履歴</h1>

      <section>
        <h2>検索条件</h2>
        <form onSubmit={handleSearch}>
          <div>
            <label htmlFor="start_date_from">開始日（from）</label>
            <input
              id="start_date_from"
              type="date"
              value={startDateFrom}
              onChange={(event) => setStartDateFrom(event.target.value)}
            />
          </div>
          <div>
            <label htmlFor="start_date_to">開始日（to）</label>
            <input
              id="start_date_to"
              type="date"
              value={startDateTo}
              onChange={(event) => setStartDateTo(event.target.value)}
            />
          </div>
          <div>
            <label htmlFor="asset_number">資産番号</label>
            <input
              id="asset_number"
              type="text"
              value={assetNumber}
              onChange={(event) => setAssetNumber(event.target.value)}
              maxLength={32}
            />
          </div>
          <div>
            <label htmlFor="user_id">申請者ID</label>
            <input id="user_id" type="text" value={userId} onChange={(event) => setUserId(event.target.value)} maxLength={32} />
          </div>
          {errorMessage !== null && <p className="error-message">{errorMessage}</p>}
          <button type="submit" disabled={isSearching}>
            検索
          </button>
          <button type="button" onClick={() => void handleExportCsv()} disabled={isExporting}>
            CSV出力
          </button>
        </form>
      </section>

      <section>
        <h2>検索結果</h2>
        {isSearching && <p>読み込み中...</p>}
        {!isSearching && hasSearched && loanRequestHistoryList.length === 0 && <p>該当する履歴はありません</p>}
        {loanRequestHistoryList.length > 0 && (
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
                <th>状態</th>
                <th>却下・取消理由</th>
                <th>申請日時</th>
                <th>承認・却下日時</th>
                <th>承認・却下者</th>
                <th>貸出日時</th>
                <th>貸出処理者</th>
                <th>返却日時</th>
                <th>返却処理者</th>
                <th>状態メモ</th>
                <th>取消日時</th>
                <th>取消処理者</th>
              </tr>
            </thead>
            <tbody>
              {loanRequestHistoryList.map((loanRequestHistory) => (
                <tr key={loanRequestHistory.id}>
                  <td>{loanRequestHistory.id}</td>
                  <td>{loanRequestHistory.asset_number}</td>
                  <td>{loanRequestHistory.equipment_name}</td>
                  <td>{loanRequestHistory.applicant_name}</td>
                  <td>{loanRequestHistory.start_date}</td>
                  <td>{loanRequestHistory.due_date}</td>
                  <td>{loanRequestHistory.purpose}</td>
                  <td>{STATUS_LABELS[loanRequestHistory.status]}</td>
                  <td>{loanRequestHistory.rejection_reason ?? ""}</td>
                  <td>{loanRequestHistory.requested_at}</td>
                  <td>{loanRequestHistory.decided_at ?? ""}</td>
                  <td>{loanRequestHistory.approved_by_name ?? ""}</td>
                  <td>{loanRequestHistory.lent_at ?? ""}</td>
                  <td>{loanRequestHistory.lent_by_name ?? ""}</td>
                  <td>{loanRequestHistory.returned_at ?? ""}</td>
                  <td>{loanRequestHistory.returned_by_name ?? ""}</td>
                  <td>{loanRequestHistory.return_note ?? ""}</td>
                  <td>{loanRequestHistory.cancelled_at ?? ""}</td>
                  <td>{loanRequestHistory.cancelled_by_name ?? ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
