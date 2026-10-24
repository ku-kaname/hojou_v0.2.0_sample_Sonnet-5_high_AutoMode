// ログイン画面（S01、F01）
//
// 【概要】
// ユーザーID・パスワードを入力して認証する。認証成功後、初回パスワード変更が未完了の場合は
// パスワード変更画面へ、完了済みの場合はホーム画面へ遷移する。

import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/useAuth";
import { ApiError } from "../api/client";

export function LoginPage() {
  const { loginWithCredentials } = useAuth();
  const navigate = useNavigate();
  const [userId, setUserId] = useState("");
  const [password, setPassword] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const myInfo = await loginWithCredentials({ user_id: userId, password });
      navigate(myInfo.must_change_password ? "/password-change" : "/", { replace: true });
    } catch (error) {
      setErrorMessage(error instanceof ApiError ? error.message : "ログインに失敗しました");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="login-page">
      <h1>ログイン</h1>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="user_id">ユーザーID</label>
          <input
            id="user_id"
            type="text"
            value={userId}
            onChange={(event) => setUserId(event.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="password">パスワード</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </div>
        {errorMessage !== null && <p className="error-message">{errorMessage}</p>}
        <button type="submit" disabled={isSubmitting}>
          ログイン
        </button>
      </form>
    </div>
  );
}
