// Python 側（sprite_gen/gen/openai_provider.py）が返す英語の失敗理由を、画面向けの日本語にする。
// 判別できないものは原文をそのまま返す。
const RETRY_NOTE = "二重課金を避けるため自動では再送しないので、もう一度依頼を送ってね。";

export function describeChatError(raw: string): string {
  if (raw.startsWith("Orcaへの接続に失敗した")) {
    return `${raw}。Sonnetを起動する前の段階なので画像APIは呼ばれていない。サーバー起動時の --orca-worktree がOrcaに登録された作業ツリーか確認して、もう一度依頼を送ってね。`;
  }
  if (!raw.startsWith("openai-gen:")) return raw;
  if (raw.includes("transport failed")) {
    return `画像APIから時間内に返事が来なかった（通信の途中で切れた可能性もある）。${RETRY_NOTE}`;
  }
  const http = raw.match(/HTTP (\d{3})/);
  if (http) {
    const code = http[1];
    const reason =
      code === "429" ? "画像APIの利用上限に当たった" :
      code.startsWith("5") ? "画像API側で障害が起きている" :
      code === "401" || code === "403" ? "画像APIの認証に失敗した（APIキーを確認してね）" :
      `画像APIがエラー ${code} を返した`;
    return `${reason}。${RETRY_NOTE}`;
  }
  if (raw.includes("invalid API response") || raw.includes("no valid PNG")) {
    return `画像APIの返事を絵として読み取れなかった。${RETRY_NOTE}`;
  }
  if (raw.includes("OPENAI_API_KEY")) return "画像APIのキーが設定されていない。.env.local を確認してね。";
  return raw;
}
