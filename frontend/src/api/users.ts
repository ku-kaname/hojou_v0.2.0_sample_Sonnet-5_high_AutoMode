// ユーザー管理API呼び出し（ユーザー管理）
//
// 【概要】
// backend/app/main.pyが公開するユーザー登録・一覧取得・詳細取得・編集・無効化・再有効化・
// パスワード初期化エンドポイントを呼び出す。

import { apiRequest } from "./client";
import type {
  PasswordResetRequest,
  UserCreateRequest,
  UserManagementResponse,
  UserUpdateRequest,
} from "../types/api";

export function createUser(userCreateRequest: UserCreateRequest): Promise<UserManagementResponse> {
  return apiRequest<UserManagementResponse>("/users", { method: "POST", body: userCreateRequest });
}

export function getUsers(): Promise<UserManagementResponse[]> {
  return apiRequest<UserManagementResponse[]>("/users");
}

export function getUser(userId: string): Promise<UserManagementResponse> {
  return apiRequest<UserManagementResponse>(`/users/${userId}`);
}

export function updateUser(
  userId: string,
  userUpdateRequest: UserUpdateRequest,
): Promise<UserManagementResponse> {
  return apiRequest<UserManagementResponse>(`/users/${userId}`, { method: "PUT", body: userUpdateRequest });
}

export function disableUser(userId: string): Promise<UserManagementResponse> {
  return apiRequest<UserManagementResponse>(`/users/${userId}/disable`, { method: "PUT" });
}

export function enableUser(userId: string): Promise<UserManagementResponse> {
  return apiRequest<UserManagementResponse>(`/users/${userId}/enable`, { method: "PUT" });
}

export function resetUserPassword(
  userId: string,
  passwordResetRequest: PasswordResetRequest,
): Promise<UserManagementResponse> {
  return apiRequest<UserManagementResponse>(`/users/${userId}/reset-password`, {
    method: "PUT",
    body: passwordResetRequest,
  });
}
