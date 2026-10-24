// 認証・認可API呼び出し（共通基盤）
//
// 【概要】
// backend/app/main.pyが公開する認証・認可（auth）エンドポイントを呼び出す。

import { apiRequest } from "./client";
import type { LoginRequest, PasswordChangeRequest, TokenResponse, UserResponse } from "../types/api";

export function login(loginRequest: LoginRequest): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/token", { method: "POST", body: loginRequest, skipAuthHeader: true });
}

export function logout(): Promise<void> {
  return apiRequest<void>("/logout", { method: "POST" });
}

export function getMyInfo(): Promise<UserResponse> {
  return apiRequest<UserResponse>("/me");
}

export function changePassword(passwordChangeRequest: PasswordChangeRequest): Promise<TokenResponse> {
  return apiRequest<TokenResponse>("/me/password", { method: "PUT", body: passwordChangeRequest });
}
