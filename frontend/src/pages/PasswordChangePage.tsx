// パスワード変更画面（S06、F02）
//
// 【概要】
// 現在のパスワードを確認したうえで、新しいパスワードに変更する。初回ログイン時の
// 変更必須フロー（ProtectedRouteによる強制遷移）にも使用する。

import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";
import { ApiError } from "../api/client";

const NEW_PASSWORD_MIN_LENGTH = 8;

export function PasswordChangePage() {
  const { changeOwnPassword } = useAuth();
  const navigate = useNavigate();
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newPasswordConfirmation, setNewPasswordConfirmation] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);

    if (newPassword !== newPasswordConfirmation) {
      setErrorMessage("新しいパスワードが一致しません");
      return;
    }
    if (newPassword.length < NEW_PASSWORD_MIN_LENGTH) {
      setErrorMessage(`新しいパスワードは${NEW_PASSWORD_MIN_LENGTH}文字以上で入力してください`);
      return;
    }

    setIsSubmitting(true);
    try {
      await changeOwnPassword({ current_password: currentPassword, new_password: newPassword });
      navigate("/", { replace: true });
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "パスワードの変更に失敗しました");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="password-change-page">
      <h1>パスワード変更</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="current_password">現在のパスワード</label>
          <input
            id="current_password"
            type="password"
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="new_password">新しいパスワード</label>
          <input
            id="new_password"
            type="password"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            minLength={NEW_PASSWORD_MIN_LENGTH}
            required
          />
        </div>
        <div>
          <label htmlFor="new_password_confirmation">新しいパスワード（確認）</label>
          <input
            id="new_password_confirmation"
            type="password"
            value={newPasswordConfirmation}
            onChange={(event) => setNewPasswordConfirmation(event.target.value)}
            minLength={NEW_PASSWORD_MIN_LENGTH}
            required
          />
        </div>
        {errorMessage !== null && <p className="error-message">{errorMessage}</p>}
        <button type="submit" disabled={isSubmitting}>
          変更する
        </button>
      </form>
    </div>
  );
}
