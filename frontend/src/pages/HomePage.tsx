// ホーム画面（S02の基盤部分）
//
// 【概要】
// ログイン後の既定表示画面。通知確認（F08）はヘッダーの共通コンポーネントで提供する。
// 自分の貸出状況・期限超過件数等（F13等）は、該当機能群バックログで本画面に追加する。

import { useAuth } from "../context/useAuth";

export function HomePage() {
  const { user } = useAuth();

  return (
    <div className="home-page">
      <h1>ホーム</h1>
      {user !== null && <p>{user.name}さん、ログインしています。</p>}
    </div>
  );
}
