// 管理者限定ルート（ユーザー管理）
//
// 【概要】
// ログイン済みユーザーのロールが管理者であることを要求するルートの共通ガード。
// 一般ユーザーがアクセスした場合はホーム画面へ遷移させる（バックエンドの
// 管理者ロール検証（require_admin）と同じ制約をUI側でも適用する）。

import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/useAuth";

export function AdminRoute() {
  const { user } = useAuth();

  if (user === null || user.role !== "admin") {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
