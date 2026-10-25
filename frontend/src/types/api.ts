// API入出力DTO型定義
//
// 【概要】
// backend/app/schemas.pyの認証・認可・通知・ユーザー管理・備品管理・貸出申請・承認・貸出・返却区分のPydanticスキーマに対応するTypeScript型を定義する。
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

export type LendingStatus = "lending" | "available";

export interface EquipmentListItemResponse {
  asset_number: string;
  name: string;
  category: string;
  description: string | null;
  location: string | null;
  is_active: boolean;
  lending_status: LendingStatus;
  due_date: string | null;
}

export type ReservationStatus = "approved" | "lending";

export interface ReservationPeriodResponse {
  start_date: string;
  due_date: string;
  status: ReservationStatus;
  borrower_name: string | null;
}

export interface EquipmentCreateRequest {
  asset_number: string;
  name: string;
  category: string;
  description: string | null;
  location: string | null;
}

export interface EquipmentUpdateRequest {
  name: string;
  category: string;
  description: string | null;
  location: string | null;
}

export interface EquipmentResponse {
  asset_number: string;
  name: string;
  category: string;
  description: string | null;
  location: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EquipmentBulkImportResponse {
  registered_count: number;
}

export type LoanRequestStatus = "pending" | "approved" | "lending" | "returned" | "rejected" | "cancelled";

export interface LoanRequestCreateRequest {
  asset_number: string;
  start_date: string;
  due_date: string;
  purpose: string;
}

export interface LoanRequestRejectRequest {
  rejection_reason: string;
}

export interface LoanRequestAdminCancelRequest {
  cancellation_reason: string;
}

export interface LoanRequestResponse {
  id: number;
  asset_number: string;
  equipment_name: string;
  applicant_name: string;
  start_date: string;
  due_date: string;
  purpose: string;
  status: LoanRequestStatus;
  rejection_reason: string | null;
  requested_at: string;
  decided_at: string | null;
  cancelled_at: string | null;
}

export interface PendingLoanRequestListItemResponse {
  id: number;
  asset_number: string;
  equipment_name: string;
  applicant_name: string;
  start_date: string;
  due_date: string;
  purpose: string;
  requested_at: string;
}

export interface LoanRequestReturnRequest {
  return_note: string | null;
}

export interface LoanLendReturnResponse {
  id: number;
  asset_number: string;
  equipment_name: string;
  applicant_name: string;
  start_date: string;
  due_date: string;
  purpose: string;
  status: LoanRequestStatus;
  lent_at: string;
  returned_at: string | null;
  return_note: string | null;
}
