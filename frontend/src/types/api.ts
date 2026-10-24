// API入出力DTO型定義
//
// 【概要】
// backend/app/schemas.pyの認証・認可・通知区分のPydanticスキーマに対応するTypeScript型を定義する。
// 他機能群のスキーマは各機能群バックログで追加する。

export interface LoginRequest {
  user_id: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface PasswordChangeRequest {
  current_password: string;
  new_password: string;
}

export interface UserResponse {
  user_id: string;
  name: string;
  department: string | null;
  role: "general" | "admin";
  must_change_password: boolean;
}

export type NotificationType = "approved" | "rejected" | "cancelled" | "new_request" | "due_reminder";

export interface NotificationResponse {
  id: number;
  notification_type: NotificationType;
  loan_request_id: number;
  is_read: boolean;
  created_at: string;
}

export interface UserCreateRequest {
  user_id: string;
  name: string;
  department: string | null;
  password: string;
  role: "general" | "admin";
}

export interface UserUpdateRequest {
  name: string;
  department: string | null;
  role: "general" | "admin";
}

export interface PasswordResetRequest {
  password: string;
}

export interface UserManagementResponse {
  user_id: string;
  name: string;
  department: string | null;
  role: "general" | "admin";
  is_active: boolean;
  must_change_password: boolean;
  created_at: string;
  updated_at: string;
}
