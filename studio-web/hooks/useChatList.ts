// 会話一覧の取得と、最後に開いた会話IDのlocalStorage永続化。
"use client";

import { useCallback, useEffect, useState } from "react";
import { getChats } from "@/lib/api";
import type { ChatSummary } from "@/lib/types";

const LAST_CHAT_ID_KEY = "sprite-chat-id";

export function saveLastChatId(id: string) {
  try {
    localStorage.setItem(LAST_CHAT_ID_KEY, id);
  } catch {
    // localStorageが使えない環境では無視
  }
}

export function getLastChatId(): string | null {
  try {
    return localStorage.getItem(LAST_CHAT_ID_KEY);
  } catch {
    return null;
  }
}

export function useChatList() {
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(() => {
    setIsLoading(true);
    getChats()
      .then((list) => {
        setChats(list);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "会話一覧の取得に失敗した"))
      .finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  return { chats, isLoading, error, reload };
}
