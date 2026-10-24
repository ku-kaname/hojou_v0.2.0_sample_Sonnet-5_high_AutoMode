// ユーザー管理画面（S10、F16）
//
// 【概要】
// 管理者がユーザーの登録・編集・無効化・再有効化・パスワード初期化を行う画面。
// 一覧表示、新規登録フォーム、選択したユーザーの編集フォームを1画面上にまとめる。

import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";
import {
  createUser,
  disableUser,
  enableUser,
  getUsers,
  resetUserPassword,
  updateUser,
} from "../api/users";
import { ApiError } from "../api/client";
import type { UserManagementResponse } from "../types/api";

const PASSWORD_MIN_LENGTH = 8;

export function UserManagementPage() {
  const [users, setUsers] = useState<UserManagementResponse[]>([]);
  const [listErrorMessage, setListErrorMessage] = useState<string | null>(null);
  const [isLoadingUsers, setIsLoadingUsers] = useState(true);

  const [newUserId, setNewUserId] = useState("");
  const [newUserName, setNewUserName] = useState("");
  const [newUserDepartment, setNewUserDepartment] = useState("");
  const [newUserPassword, setNewUserPassword] = useState("");
  const [newUserRole, setNewUserRole] = useState<"general" | "admin">("general");
  const [createErrorMessage, setCreateErrorMessage] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");
  const [editDepartment, setEditDepartment] = useState("");
  const [editRole, setEditRole] = useState<"general" | "admin">("general");
  const [editErrorMessage, setEditErrorMessage] = useState<string | null>(null);
  const [isSavingEdit, setIsSavingEdit] = useState(false);

  const [resetPassword, setResetPassword] = useState("");
  const [resetErrorMessage, setResetErrorMessage] = useState<string | null>(null);
  const [isResettingPassword, setIsResettingPassword] = useState(false);

  const loadUsers = useCallback(async () => {
    setIsLoadingUsers(true);
    setListErrorMessage(null);
    try {
      const fetchedUsers = await getUsers();
      setUsers(fetchedUsers);
    } catch (error) {
      setListErrorMessage(error instanceof ApiError ? error.message : "ユーザー一覧の取得に失敗しました");
    } finally {
      setIsLoadingUsers(false);
    }
  }, []);

  useEffect(() => {
    void loadUsers();
  }, [loadUsers]);

  async function handleCreateUser(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setCreateErrorMessage(null);
    setIsCreating(true);
    try {
      await createUser({
        user_id: newUserId,
        name: newUserName,
        department: newUserDepartment === "" ? null : newUserDepartment,
        password: newUserPassword,
        role: newUserRole,
      });
      setNewUserId("");
      setNewUserName("");
      setNewUserDepartment("");
      setNewUserPassword("");
      setNewUserRole("general");
      await loadUsers();
    } catch (error) {
      setCreateErrorMessage(error instanceof ApiError ? error.message : "ユーザーの登録に失敗しました");
    } finally {
      setIsCreating(false);
    }
  }

  function handleSelectUser(user: UserManagementResponse) {
    setSelectedUserId(user.user_id);
    setEditName(user.name);
    setEditDepartment(user.department ?? "");
    setEditRole(user.role);
    setEditErrorMessage(null);
    setResetPassword("");
    setResetErrorMessage(null);
  }

  async function handleSaveEdit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedUserId === null) {
      return;
    }
    setEditErrorMessage(null);
    setIsSavingEdit(true);
    try {
      await updateUser(selectedUserId, {
        name: editName,
        department: editDepartment === "" ? null : editDepartment,
        role: editRole,
      });
      await loadUsers();
    } catch (error) {
      setEditErrorMessage(error instanceof ApiError ? error.message : "ユーザーの編集に失敗しました");
    } finally {
      setIsSavingEdit(false);
    }
  }

  async function handleToggleActive(user: UserManagementResponse) {
    setListErrorMessage(null);
    try {
      if (user.is_active) {
        await disableUser(user.user_id);
      } else {
        await enableUser(user.user_id);
      }
      await loadUsers();
    } catch (error) {
      setListErrorMessage(error instanceof ApiError ? error.message : "ユーザーの状態変更に失敗しました");
    }
  }

  async function handleResetPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (selectedUserId === null) {
      return;
    }
    setResetErrorMessage(null);
    setIsResettingPassword(true);
    try {
      await resetUserPassword(selectedUserId, { password: resetPassword });
      setResetPassword("");
      await loadUsers();
    } catch (error) {
      setResetErrorMessage(error instanceof ApiError ? error.message : "パスワードの初期化に失敗しました");
    } finally {
      setIsResettingPassword(false);
    }
  }

  return (
    <div className="user-management-page">
      <h1>ユーザー管理</h1>

      <section>
        <h2>ユーザー一覧</h2>
        {isLoadingUsers && <p>読み込み中...</p>}
        {listErrorMessage !== null && <p className="error-message">{listErrorMessage}</p>}
        {!isLoadingUsers && users.length === 0 && <p>ユーザーが登録されていません</p>}
        {users.length > 0 && (
          <table>
            <thead>
              <tr>
                <th>ユーザーID</th>
                <th>氏名</th>
                <th>部署</th>
                <th>ロール</th>
                <th>状態</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              {users.map((user) => (
                <tr key={user.user_id}>
                  <td>{user.user_id}</td>
                  <td>{user.name}</td>
                  <td>{user.department ?? "-"}</td>
                  <td>{user.role === "admin" ? "管理者" : "一般"}</td>
                  <td>{user.is_active ? "有効" : "無効"}</td>
                  <td>
                    <button type="button" onClick={() => handleSelectUser(user)}>
                      編集
                    </button>
                    <button type="button" onClick={() => void handleToggleActive(user)}>
                      {user.is_active ? "無効化" : "再有効化"}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section>
        <h2>ユーザー登録</h2>
        <form onSubmit={handleCreateUser}>
          <div>
            <label htmlFor="new_user_id">ユーザーID</label>
            <input
              id="new_user_id"
              type="text"
              value={newUserId}
              onChange={(event) => setNewUserId(event.target.value)}
              minLength={3}
              maxLength={32}
              required
            />
          </div>
          <div>
            <label htmlFor="new_user_name">氏名</label>
            <input
              id="new_user_name"
              type="text"
              value={newUserName}
              onChange={(event) => setNewUserName(event.target.value)}
              maxLength={50}
              required
            />
          </div>
          <div>
            <label htmlFor="new_user_department">部署</label>
            <input
              id="new_user_department"
              type="text"
              value={newUserDepartment}
              onChange={(event) => setNewUserDepartment(event.target.value)}
              maxLength={50}
            />
          </div>
          <div>
            <label htmlFor="new_user_password">初期パスワード</label>
            <input
              id="new_user_password"
              type="password"
              value={newUserPassword}
              onChange={(event) => setNewUserPassword(event.target.value)}
              minLength={PASSWORD_MIN_LENGTH}
              required
            />
          </div>
          <div>
            <label htmlFor="new_user_role">ロール</label>
            <select
              id="new_user_role"
              value={newUserRole}
              onChange={(event) => setNewUserRole(event.target.value as "general" | "admin")}
            >
              <option value="general">一般</option>
              <option value="admin">管理者</option>
            </select>
          </div>
          {createErrorMessage !== null && <p className="error-message">{createErrorMessage}</p>}
          <button type="submit" disabled={isCreating}>
            登録する
          </button>
        </form>
      </section>

      {selectedUserId !== null && (
        <section>
          <h2>ユーザー編集（{selectedUserId}）</h2>
          <form onSubmit={handleSaveEdit}>
            <div>
              <label htmlFor="edit_user_name">氏名</label>
              <input
                id="edit_user_name"
                type="text"
                value={editName}
                onChange={(event) => setEditName(event.target.value)}
                maxLength={50}
                required
              />
            </div>
            <div>
              <label htmlFor="edit_user_department">部署</label>
              <input
                id="edit_user_department"
                type="text"
                value={editDepartment}
                onChange={(event) => setEditDepartment(event.target.value)}
                maxLength={50}
              />
            </div>
            <div>
              <label htmlFor="edit_user_role">ロール</label>
              <select
                id="edit_user_role"
                value={editRole}
                onChange={(event) => setEditRole(event.target.value as "general" | "admin")}
              >
                <option value="general">一般</option>
                <option value="admin">管理者</option>
              </select>
            </div>
            {editErrorMessage !== null && <p className="error-message">{editErrorMessage}</p>}
            <button type="submit" disabled={isSavingEdit}>
              保存する
            </button>
          </form>

          <h3>パスワード初期化</h3>
          <form onSubmit={handleResetPassword}>
            <div>
              <label htmlFor="reset_password">新しい初期パスワード</label>
              <input
                id="reset_password"
                type="password"
                value={resetPassword}
                onChange={(event) => setResetPassword(event.target.value)}
                minLength={PASSWORD_MIN_LENGTH}
                required
              />
            </div>
            {resetErrorMessage !== null && <p className="error-message">{resetErrorMessage}</p>}
            <button type="submit" disabled={isResettingPassword}>
              初期化する
            </button>
          </form>
        </section>
      )}
    </div>
  );
}
