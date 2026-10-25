// 共通レイアウト（共通基盤）
//
// 【概要】
// ログイン後の全画面で共通して表示するヘッダー（通知表示・ログアウト）と、
// 各画面コンテンツの表示領域（Outlet）を提供する。

import { Link, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";
import { NotificationBell } from "./NotificationBell";

export function Layout() {
  const { user, logoutCurrentUser } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logoutCurrentUser();
    navigate("/login", { replace: true });
  }

  return (
    <div className="app-layout">
      <header className="app-header">
        <Link to="/">社内備品貸出管理システム</Link>
        <div className="app-header-actions">
          {user !== null && <Link to="/equipment">備品一覧</Link>}
          {user !== null && user.role === "admin" && <Link to="/equipment-management">備品管理</Link>}
          {user !== null && user.role === "admin" && <Link to="/users">ユーザー管理</Link>}
          {user !== null && <span>{user.name}さん</span>}
          <NotificationBell />
          <button type="button" onClick={handleLogout}>
            ログアウト
          </button>
        </div>
      </header>
      <main>
        <Outlet />
      </main>
    </div>
  );
}
