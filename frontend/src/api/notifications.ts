// 通知API呼び出し（共通基盤）
//
// 【概要】
// backend/app/main.pyが公開する通知一覧取得・通知既読化エンドポイントを呼び出す。

import { apiRequest } from "./client";
import type { NotificationResponse } from "../types/api";

export function getNotifications(): Promise<NotificationResponse[]> {
  return apiRequest<NotificationResponse[]>("/notifications");
}

export function markNotificationRead(notificationId: number): Promise<NotificationResponse> {
  return apiRequest<NotificationResponse>(`/notifications/${notificationId}/read`, { method: "PUT" });
}
