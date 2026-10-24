// 認証状態参照フック（共通基盤）

import { useContext } from "react";
import { AuthContext } from "./AuthContext";
import type { AuthContextValue } from "./AuthContext";

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error("useAuthはAuthProviderの内側で使用してください");
  }
  return context;
}
