"use client";

import { useCallback, useEffect, useState } from "react";

// 会話ごとの下書きをlocalStorageに保存する。chatIdが無い（新規作成前）場合は'new'キーを使う。
function draftKey(chatId: string | null): string {
  return `sprite-draft-${chatId ?? "new"}`;
}

export function useDraft(chatId: string | null) {
  const [text, setText] = useState("");

  useEffect(() => {
    try {
      setText(localStorage.getItem(draftKey(chatId)) ?? "");
    } catch {
      setText("");
    }
  }, [chatId]);

  const update = useCallback(
    (value: string) => {
      setText(value);
      try {
        if (value === "") {
          localStorage.removeItem(draftKey(chatId));
        } else {
          localStorage.setItem(draftKey(chatId), value);
        }
      } catch {
        // localStorageが使えない環境では保存をあきらめる
      }
    },
    [chatId],
  );

  const clear = useCallback(() => update(""), [update]);

  return { text, setText: update, clear };
}
