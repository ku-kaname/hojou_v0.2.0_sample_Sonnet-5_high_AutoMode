// 認証状態管理（共通基盤）
//
// 【概要】
// ログイン中ユーザー情報の保持・復元、ログイン・ログアウト処理、およびAPIからの401応答を
// 受けた際の強制ログアウトを一箇所で管理する。各画面はuseAuth()経由でこの状態を参照する。

import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { changePassword as changePasswordApi, getMyInfo, login as loginApi, logout as logoutApi } from "../api/auth";
import { UNAUTHORIZED_EVENT, clearStoredAccessToken, getStoredAccessToken, setStoredAccessToken } from "../api/client";
import type { LoginRequest, PasswordChangeRequest, UserResponse } from "../types/api";
import { AuthContext } from "./AuthContext";
import type { AuthStatus } from "./AuthContext";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  const refreshCurrentUser = useCallback(async () => {
    if (getStoredAccessToken() === null) {
      setUser(null);
      setStatus("unauthenticated");
      return;
    }

    try {
      const myInfo = await getMyInfo();
      setUser(myInfo);
      setStatus("authenticated");
    } catch {
      clearStoredAccessToken();
      setUser(null);
      setStatus("unauthenticated");
    }
  }, []);

  const loginWithCredentials = useCallback(async (loginRequest: LoginRequest): Promise<UserResponse> => {
    const tokenResponse = await loginApi(loginRequest);
    setStoredAccessToken(tokenResponse.access_token);
    const myInfo = await getMyInfo();
    setUser(myInfo);
    setStatus("authenticated");
    return myInfo;
  }, []);

  const changeOwnPassword = useCallback(async (passwordChangeRequest: PasswordChangeRequest): Promise<UserResponse> => {
    const tokenResponse = await changePasswordApi(passwordChangeRequest);
    setStoredAccessToken(tokenResponse.access_token);
    const myInfo = await getMyInfo();
    setUser(myInfo);
    setStatus("authenticated");
    return myInfo;
  }, []);

  const logoutCurrentUser = useCallback(async () => {
    try {
      await logoutApi();
    } finally {
      clearStoredAccessToken();
      setUser(null);
      setStatus("unauthenticated");
    }
  }, []);

  useEffect(() => {
    refreshCurrentUser();
  }, [refreshCurrentUser]);

  useEffect(() => {
    function handleUnauthorized() {
      clearStoredAccessToken();
      setUser(null);
      setStatus("unauthenticated");
    }

    window.addEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, handleUnauthorized);
  }, []);

  return (
    <AuthContext.Provider
      value={{ user, status, loginWithCredentials, logoutCurrentUser, refreshCurrentUser, changeOwnPassword }}
    >
      {children}
    </AuthContext.Provider>
  );
}
