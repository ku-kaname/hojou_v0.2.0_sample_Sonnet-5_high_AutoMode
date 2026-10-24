// 通知表示（共通基盤、F08: 通知確認）
//
// 【概要】
// ログインユーザー宛の通知一覧を取得し、未読件数を表示する。通知を開くと一覧を表示し、
// クリックで既読化する。

import { useCallback, useEffect, useState } from "react";
import { getNotifications, markNotificationRead } from "../api/notifications";
import type { NotificationResponse } from "../types/api";
import { useAuth } from "../context/useAuth";

const NOTIFICATION_TYPE_LABELS: Record<NotificationResponse["notification_type"], string> = {
  approved: "申請が承認されました",
  rejected: "申請が却下されました",
  cancelled: "申請が取り消されました",
  new_request: "新規の申請があります",
  due_reminder: "返却期限が近づいています",
};

export function NotificationBell() {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  const loadNotifications = useCallback(async () => {
    const notificationList = await getNotifications();
    setNotifications(notificationList);
  }, []);

  useEffect(() => {
    // 初回パスワード変更が未完了の間はバックエンド側でアクセス不可（403）のため取得しない
    if (user === null || user.must_change_password) {
      return;
    }
    loadNotifications();
  }, [user, loadNotifications]);

  function handleToggleOpen() {
    setIsOpen((currentIsOpen) => !currentIsOpen);
  }

  async function handleMarkRead(notificationId: number) {
    try {
      const updatedNotification = await markNotificationRead(notificationId);
      setNotifications((currentNotifications) =>
        currentNotifications.map((notification) =>
          notification.id === updatedNotification.id ? updatedNotification : notification,
        ),
      );
    } catch {
      // 既読化に失敗した場合は、サーバー側の最新状態に表示を合わせ直す
      await loadNotifications();
    }
  }

  const unreadCount = notifications.filter((notification) => !notification.is_read).length;

  return (
    <div className="notification-bell">
      <button type="button" onClick={handleToggleOpen}>
        通知{unreadCount > 0 ? `（${unreadCount}）` : ""}
      </button>
      {isOpen && (
        <ul className="notification-list">
          {notifications.length === 0 && <li>通知はありません</li>}
          {notifications.map((notification) => (
            <li key={notification.id} className={notification.is_read ? "read" : "unread"}>
              <button type="button" onClick={() => handleMarkRead(notification.id)} disabled={notification.is_read}>
                {NOTIFICATION_TYPE_LABELS[notification.notification_type]}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
