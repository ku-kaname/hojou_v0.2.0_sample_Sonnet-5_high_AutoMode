// APIクライアント（共通基盤）
//
// 【概要】
// バックエンドAPIへのHTTPリクエストを共通化する。アクセストークンの付与、エラー応答の
// 共通ハンドリング（401発生時のログアウト通知）を一箇所に集約し、各API呼び出し元が
// 個別にヘッダー設定・エラー処理を書かないようにする。

const ACCESS_TOKEN_STORAGE_KEY = "accessToken";

export function getStoredAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
}

export function setStoredAccessToken(accessToken: string): void {
  localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, accessToken);
}

export function clearStoredAccessToken(): void {
  localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
}

// 401応答（トークン無効・期限切れ）を受け取った際に、AuthContextへログアウトを通知するためのイベント名
export const UNAUTHORIZED_EVENT = "api:unauthorized";

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  skipAuthHeader?: boolean;
}

async function parseErrorDetail(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data.detail === "string") {
      return data.detail;
    }
  } catch {
    // 応答本文がJSONでない場合は既定のメッセージを使用する
  }
  return "通信中にエラーが発生しました";
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };

  if (!options.skipAuthHeader) {
    const accessToken = getStoredAccessToken();
    if (accessToken !== null) {
      headers["Authorization"] = `Bearer ${accessToken}`;
    }
  }

  const response = await fetch(`/api${path}`, {
    method: options.method ?? "GET",
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  if (response.status === 401) {
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    throw new ApiError(401, await parseErrorDetail(response));
  }

  if (!response.ok) {
    throw new ApiError(response.status, await parseErrorDetail(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
