// sprite_gen/serve/chat_studio.py のHTTP API・実データ(chat.json)から確認した型。

export type Message = {
  role: "user" | "assistant";
  text: string;
};

export type Event = {
  time: string; // ISO8601
  text: string;
};

export type ReviewResult = {
  summary: string;
  issues: string[];
};

export type Version = {
  id: string;
  title: string;
  created_at: string; // ISO8601
  image: string; // /media/... URL
  review_status: string; // "確認中" | "目視比較済み" | "要確認" | "比較未完了" | "加工未完了"
  analysis: string;
  // 失敗時の縮小版フォールバックversionには以下が無い
  prompt?: string;
  sources?: { title: string; url: string }[];
  references?: string[]; // /media/... URL群
  operation?: string; // "generate" | "interpolate" | "timing"
  // generation.jsonが存在する時のみ(generate/interpolateのみ、timingには無い)
  image_model?: string;
  // pipelineがあれば{kind}-contact.png、sceneならprocessed.png。失敗時フォールバックには無い
  contact?: string;
  // pipelineがある場合のみ(sceneには無い)
  animation?: string;
  // interpolate操作で中間コマを追加した場合のみ
  inserted?: string;
  // reviewフェーズまで到達した場合のみ
  review?: ReviewResult;
};

export type Chat = {
  id: string; // 32桁hex
  title: string;
  reference_id: string; // 空文字あり
  updated_at: string; // ISO8601
  messages: Message[];
  events: Event[]; // 直近のsubmitで空配列にリセットされる
  status: "idle" | "running" | "failed";
  phase: string;
  error: string | null;
  versions: Version[];
};

export type ChatSummary = {
  id: string;
  title: string;
  updated_at: string;
};

export type LibraryItem = {
  id: string;
  title: string;
  notes: string;
  thumbnail: string; // /media/...raw.png
  animation: string | null; // pipeline/qa/*.gif の先頭
};
