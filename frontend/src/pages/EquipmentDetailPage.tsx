// 備品詳細画面（S04、F04・F05）
//
// 【概要】
// 指定した資産番号の備品の詳細情報と予約状況（承認済み・貸出中の申請）を表示し、
// 当該備品の貸出を申請するフォームを提供する画面。借用者氏名は管理者のみ表示される。

import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { getEquipment, getEquipmentReservations } from "../api/equipment";
import { createLoanRequest } from "../api/loanRequests";
import { ApiError } from "../api/client";
import type { EquipmentListItemResponse, LoanRequestResponse, ReservationPeriodResponse } from "../types/api";

export function EquipmentDetailPage() {
  const { assetNumber } = useParams<{ assetNumber: string }>();

  const [equipment, setEquipment] = useState<EquipmentListItemResponse | null>(null);
  const [reservations, setReservations] = useState<ReservationPeriodResponse[]>([]);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const [startDate, setStartDate] = useState("");
  const [dueDate, setDueDate] = useState("");
  const [purpose, setPurpose] = useState("");
  const [requestErrorMessage, setRequestErrorMessage] = useState<string | null>(null);
  const [createdLoanRequest, setCreatedLoanRequest] = useState<LoanRequestResponse | null>(null);
  const [isRequesting, setIsRequesting] = useState(false);

  const loadEquipmentDetail = useCallback(async (targetAssetNumber: string) => {
    setIsLoading(true);
    setErrorMessage(null);
    try {
      const [fetchedEquipment, fetchedReservations] = await Promise.all([
        getEquipment(targetAssetNumber),
        getEquipmentReservations(targetAssetNumber),
      ]);
      setEquipment(fetchedEquipment);
      setReservations(fetchedReservations);
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "備品詳細の取得に失敗しました");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (assetNumber !== undefined) {
      void loadEquipmentDetail(assetNumber);
    }
  }, [assetNumber, loadEquipmentDetail]);

  const showsBorrowerName = reservations.some((reservation) => reservation.borrower_name !== null);

  async function handleCreateLoanRequest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (assetNumber === undefined) {
      return;
    }
    setRequestErrorMessage(null);
    setIsRequesting(true);
    try {
      const loanRequest = await createLoanRequest({
        asset_number: assetNumber,
        start_date: startDate,
        due_date: dueDate,
        purpose,
      });
      setCreatedLoanRequest(loanRequest);
      setStartDate("");
      setDueDate("");
      setPurpose("");
      await loadEquipmentDetail(assetNumber);
    } catch (error) {
      setRequestErrorMessage(error instanceof ApiError ? error.message : "貸出申請に失敗しました");
    } finally {
      setIsRequesting(false);
    }
  }

  return (
    <div className="equipment-detail-page">
      <p>
        <Link to="/equipment">一覧に戻る</Link>
      </p>
      <h1>備品詳細</h1>

      {isLoading && <p>読み込み中...</p>}
      {errorMessage !== null && <p className="error-message">{errorMessage}</p>}

      {equipment !== null && (
        <section>
          <table>
            <tbody>
              <tr>
                <th>資産番号</th>
                <td>{equipment.asset_number}</td>
              </tr>
              <tr>
                <th>名称</th>
                <td>{equipment.name}</td>
              </tr>
              <tr>
                <th>分類</th>
                <td>{equipment.category}</td>
              </tr>
              <tr>
                <th>説明</th>
                <td>{equipment.description ?? "-"}</td>
              </tr>
              <tr>
                <th>保管場所</th>
                <td>{equipment.location ?? "-"}</td>
              </tr>
              <tr>
                <th>状態</th>
                <td>{equipment.is_active ? "有効" : "無効"}</td>
              </tr>
              <tr>
                <th>貸出状況</th>
                <td>{equipment.lending_status === "lending" ? "貸出中" : "貸出可能"}</td>
              </tr>
              <tr>
                <th>返却期限</th>
                <td>{equipment.due_date ?? "-"}</td>
              </tr>
            </tbody>
          </table>
        </section>
      )}

      {equipment !== null && (
        <section>
          <h2>予約状況</h2>
          {reservations.length === 0 && <p>予約されている期間はありません</p>}
          {reservations.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>開始日</th>
                  <th>返却期限</th>
                  <th>状態</th>
                  {showsBorrowerName && <th>借用者</th>}
                </tr>
              </thead>
              <tbody>
                {reservations.map((reservation, index) => (
                  <tr key={`${reservation.start_date}-${index}`}>
                    <td>{reservation.start_date}</td>
                    <td>{reservation.due_date}</td>
                    <td>{reservation.status === "lending" ? "貸出中" : "承認済み"}</td>
                    {showsBorrowerName && <td>{reservation.borrower_name ?? "-"}</td>}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>
      )}

      {equipment !== null && equipment.is_active && (
        <section>
          <h2>貸出申請</h2>
          <form onSubmit={handleCreateLoanRequest}>
            <div>
              <label htmlFor="loan_request_start_date">開始日</label>
              <input
                id="loan_request_start_date"
                type="date"
                value={startDate}
                onChange={(event) => setStartDate(event.target.value)}
                required
              />
            </div>
            <div>
              <label htmlFor="loan_request_due_date">返却予定日</label>
              <input
                id="loan_request_due_date"
                type="date"
                value={dueDate}
                onChange={(event) => setDueDate(event.target.value)}
                required
              />
            </div>
            <div>
              <label htmlFor="loan_request_purpose">用途</label>
              <input
                id="loan_request_purpose"
                type="text"
                value={purpose}
                onChange={(event) => setPurpose(event.target.value)}
                maxLength={200}
                required
              />
            </div>
            {requestErrorMessage !== null && <p className="error-message">{requestErrorMessage}</p>}
            <button type="submit" disabled={isRequesting}>
              申請する
            </button>
          </form>
        </section>
      )}

      {createdLoanRequest !== null && (
        <section>
          <h2>申請結果</h2>
          <p className="success-message">貸出申請を受け付けました（申請ID：{createdLoanRequest.id}）。</p>
          <p>管理者の承認をお待ちください。申請の取消は「自分の申請一覧」画面から行えます。</p>
        </section>
      )}
    </div>
  );
}
