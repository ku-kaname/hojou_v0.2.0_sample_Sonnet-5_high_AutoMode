// アプリケーションルーティング（共通基盤）
//
// 【概要】
// 画面遷移（ルーティング）を定義する。ログイン画面は認証不要、それ以外はProtectedRouteで
// ログイン・初回パスワード変更済みを要求する。各機能群バックログの画面は本ルーティングに追加する。

import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthProvider";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AdminRoute } from "./components/AdminRoute";
import { Layout } from "./components/Layout";
import { LoginPage } from "./pages/LoginPage";
import { PasswordChangePage } from "./pages/PasswordChangePage";
import { HomePage } from "./pages/HomePage";
import { UserManagementPage } from "./pages/UserManagementPage";
import { EquipmentListPage } from "./pages/EquipmentListPage";
import { EquipmentDetailPage } from "./pages/EquipmentDetailPage";
import { EquipmentManagementPage } from "./pages/EquipmentManagementPage";

export function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route path="/" element={<HomePage />} />
            <Route path="/password-change" element={<PasswordChangePage />} />
            <Route path="/equipment" element={<EquipmentListPage />} />
            <Route path="/equipment/:assetNumber" element={<EquipmentDetailPage />} />
            <Route element={<AdminRoute />}>
              <Route path="/users" element={<UserManagementPage />} />
              <Route path="/equipment-management" element={<EquipmentManagementPage />} />
            </Route>
          </Route>
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AuthProvider>
  );
}
