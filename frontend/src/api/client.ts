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

// 行単位の検証エラー（例：備品CSV一括登録の行番号・エラー内容）
export interface ApiRowError {
  row_number: number;
  error_message: string;
}

export class ApiError extends Error {
  readonly status: number;
  // detailがリスト形状（行単位の検証エラー一覧）の場合に設定する。文字列形状の場合はundefined
  readonly rowErrors?: ApiRowError[];

  constructor(status: number, detail: string, rowErrors?: ApiRowError[]) {
    super(detail);
    this.status = status;
    this.rowErrors = rowErrors;
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
  skipAuthHeader?: boolean;
}

interface ParsedErrorDetail {
  message: string;
  rowErrors?: ApiRowError[];
}

function isApiRowErrorList(data: unknown): data is ApiRowError[] {
  return (
    Array.isArray(data) &&
    data.every(
      (item) =>
        typeof item === "object" &&
        item !== null &&
        typeof (item as ApiRowError).row_number === "number" &&
        typeof (item as ApiRowError).error_message === "string",
    )
  );
}

async function parseErrorDetail(response: Response): Promise<ParsedErrorDetail> {
  try {
    const data = await response.json();
    if (typeof data.detail === "string") {
      return { message: data.detail };
    }
    if (isApiRowErrorList(data.detail)) {
      return { message: "入力内容に誤りがあります", rowErrors: data.detail };
    }
  } catch {
    // 応答本文がJSONでない場合は既定のメッセージを使用する
  }
  return { message: "通信中にエラーが発生しました" };
}

async function throwApiError(response: Response): Promise<never> {
  const { message, rowErrors } = await parseErrorDetail(response);
  throw new ApiError(response.status, message, rowErrors);
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
    await throwApiError(response);
  }

  if (!response.ok) {
    await throwApiError(response);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

// CSV等の非JSON応答（ファイルダウンロード）を取得する
export async function apiDownloadRequest(path: string): Promise<Blob> {
  const headers: Record<string, string> = {};

  const accessToken = getStoredAccessToken();
  if (accessToken !== null) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  const response = await fetch(`/api${path}`, {
    method: "GET",
    headers,
  });

  if (response.status === 401) {
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    await throwApiError(response);
  }

  if (!response.ok) {
    await throwApiError(response);
  }

  return await response.blob();
}

// multipart/form-dataでファイルを送信する（CSV一括登録等）。Content-Typeは
// ブラウザがboundary付きで自動設定するため、明示的に設定しない。
export async function apiUploadRequest<T>(path: string, formData: FormData): Promise<T> {
  const headers: Record<string, string> = {};

  const accessToken = getStoredAccessToken();
  if (accessToken !== null) {
    headers["Authorization"] = `Bearer ${accessToken}`;
  }

  const response = await fetch(`/api${path}`, {
    method: "POST",
    headers,
    body: formData,
  });

  if (response.status === 401) {
    window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    await throwApiError(response);
  }

  if (!response.ok) {
    await throwApiError(response);
  }

  return (await response.json()) as T;
}
