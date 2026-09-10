"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getChat, postMessage } from "@/lib/api";
import type { Chat } from "@/lib/types";

export function useChat(chatId: string | null) {
  const [chat, setChat] = useState<Chat | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const chatIdRef = useRef(chatId);
  chatIdRef.current = chatId;

  useEffect(() => {
    setChat(null);
    setError(null);
    if (!chatId) return;

    let cancelled = false;
    getChat(chatId)
      .then((c) => {
        if (cancelled || chatIdRef.current !== chatId) return;
        setChat(c);
      })
      .catch((e) => {
        if (cancelled || chatIdRef.current !== chatId) return;
        setError(e instanceof Error ? e.message : "会話の取得に失敗した");
      });
    return () => {
      cancelled = true;
    };
  }, [chatId]);

  // status==='running'かつタブが表示中の時だけ1秒間隔でポーリングする。
  useEffect(() => {
    if (!chatId || chat?.status !== "running") return;

    let cancelled = false;
    const poll = () => {
      if (document.visibilityState !== "visible") return;
      getChat(chatId)
        .then((c) => {
          if (cancelled || chatIdRef.current !== chatId) return;
          setChat(c);
          setError(null);
        })
        .catch((e) => {
          if (cancelled || chatIdRef.current !== chatId) return;
          setError(e instanceof Error ? e.message : "会話の取得に失敗した");
        });
    };
    const interval = setInterval(poll, 1000);
    document.addEventListener("visibilitychange", poll);
    return () => {
      cancelled = true;
      clearInterval(interval);
      document.removeEventListener("visibilitychange", poll);
    };
  }, [chatId, chat?.status]);

  const submit = useCallback(
    async (text: string) => {
      if (!chatId) return;
      setIsSubmitting(true);
      setError(null);
      try {
        const updated = await postMessage(chatId, text);
        if (chatIdRef.current === chatId) setChat(updated);
      } catch (e) {
        if (chatIdRef.current === chatId) {
          setError(e instanceof Error ? e.message : "送信に失敗した");
        }
      } finally {
        setIsSubmitting(false);
      }
    },
    [chatId],
  );

  return { chat, error, isSubmitting, submit };
}
