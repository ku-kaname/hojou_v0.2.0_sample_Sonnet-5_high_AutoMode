// 認証必須ルート（共通基盤）
//
// 【概要】
// ログイン済みであることを要求するルートの共通ガード。未ログインの場合はログイン画面へ、
// 初回パスワード変更が未完了の場合はパスワード変更画面へ遷移させる
// （バックエンドの初回パスワード変更検証（require_password_changed）と同じ制約をUI側でも適用する）。

import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../context/useAuth";

const PASSWORD_CHANGE_PATH = "/password-change";

export function ProtectedRoute() {
  const { user, status } = useAuth();
  const location = useLocation();

  if (status === "loading") {
    return <p>読み込み中...</p>;
  }

  if (status === "unauthenticated" || user === null) {
    return <Navigate to="/login" replace />;
  }

  if (user.must_change_password && location.pathname !== PASSWORD_CHANGE_PATH) {
    return <Navigate to={PASSWORD_CHANGE_PATH} replace />;
  }

  return <Outlet />;
}
