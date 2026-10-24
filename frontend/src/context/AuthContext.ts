// 認証状態の型・Context定義（共通基盤）
//
// 【概要】
// AuthProvider（状態管理の実装）とuseAuth（参照用フック）の間で共有する
// Context定義と型のみを置く（react-refreshの制約上、コンポーネントとは別ファイルに分離する）。

import { createContext } from "react";
import type { LoginRequest, PasswordChangeRequest, UserResponse } from "../types/api";

export type AuthStatus = "loading" | "authenticated" | "unauthenticated";

export interface AuthContextValue {
  user: UserResponse | null;
  status: AuthStatus;
  loginWithCredentials: (loginRequest: LoginRequest) => Promise<UserResponse>;
  logoutCurrentUser: () => Promise<void>;
  refreshCurrentUser: () => Promise<void>;
  changeOwnPassword: (passwordChangeRequest: PasswordChangeRequest) => Promise<UserResponse>;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
