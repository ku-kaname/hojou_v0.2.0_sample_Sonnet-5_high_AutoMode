// ホーム画面（S02、F13）
//
// 【概要】
// ログイン後の既定表示画面。通知確認（F08）はヘッダーの共通コンポーネントで提供する。
// 管理者には、期限超過件数（F13）を表示する。

import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/useAuth";
import { getOverdueLoanRequests } from "../api/loanRequests";
import { ApiError } from "../api/client";

export function HomePage() {
  const { user } = useAuth();
  const [overdueCount, setOverdueCount] = useState<number | null>(null);
  const [overdueErrorMessage, setOverdueErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (user === null || user.role !== "admin") {
      return;
    }
    let isCancelled = false;
    async function loadOverdueCount() {
      try {
        const overdueLoanRequests = await getOverdueLoanRequests();
        if (!isCancelled) {
          setOverdueCount(overdueLoanRequests.length);
        }
      } catch (error) {
        if (!isCancelled) {
          setOverdueErrorMessage(error instanceof ApiError ? error.message : "期限超過件数の取得に失敗しました");
        }
      }
    }
    void loadOverdueCount();
    return () => {
      isCancelled = true;
    };
  }, [user]);

  return (
    <div className="home-page">
      <h1>ホーム</h1>
      {user !== null && <p>{user.name}さん、ログインしています。</p>}

      {user !== null && user.role === "admin" && (
        <section>
          <h2>期限超過件数</h2>
          {overdueErrorMessage !== null && <p className="error-message">{overdueErrorMessage}</p>}
          {overdueErrorMessage === null && (
            <p>
              現在、返却予定日を過ぎた貸出が<strong>{overdueCount ?? "読み込み中..."}</strong>件あります。
              {overdueCount !== null && overdueCount > 0 && <Link to="/overdue-loan-requests">一覧を確認する</Link>}
            </p>
          )}
        </section>
      )}
    </div>
  );
}
