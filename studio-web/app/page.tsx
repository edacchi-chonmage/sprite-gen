"use client";

// 最後に開いた会話があればそこへリダイレクトし、無ければ空状態を出す。
// 空状態では常設のComposerBarからテキスト送信するだけで会話が自動作成される(既存chat_ui/index.htmlと同じ導線)。
// ライブラリから元絵を選びたい時はNewChatDialogをボタンから開く。

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { VStack } from "@astryxdesign/core/VStack";
import { EmptyState } from "@astryxdesign/core/EmptyState";
import { Button } from "@astryxdesign/core/Button";
import { getLastChatId, saveLastChatId } from "@/hooks/useChatList";
import { NewChatDialog } from "@/components/shell/NewChatDialog";
import { ComposerBar } from "@/components/chat/ComposerBar";
import { ErrorBanner } from "@/components/common/ErrorBanner";
import { createChat, postMessage } from "@/lib/api";
import type { Chat } from "@/lib/types";

export default function Home() {
  const router = useRouter();
  const [isRedirecting, setIsRedirecting] = useState(true);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [text, setText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const lastId = getLastChatId();
    if (lastId) {
      router.replace(`/chat/${lastId}`);
      return;
    }
    setIsRedirecting(false);
  }, [router]);

  const handleCreated = (chat: Chat) => {
    setIsDialogOpen(false);
    saveLastChatId(chat.id);
    router.push(`/chat/${chat.id}`);
  };

  const handleSubmit = async () => {
    if (!text) return;
    setIsSubmitting(true);
    setError(null);
    try {
      const chat = await createChat(undefined);
      const updated = await postMessage(chat.id, text);
      handleCreated(updated);
    } catch (e) {
      setError(e instanceof Error ? e.message : "送信に失敗した");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isRedirecting) return null;

  return (
    <VStack height="100%" align="center" justify="center" padding={6} gap={4}>
      <EmptyState
        title="会話がまだない"
        description="作りたいものを伝えるか、ライブラリから元絵を選んで会話を始める"
        actions={<Button label="ライブラリから選ぶ" variant="secondary" onClick={() => setIsDialogOpen(true)} />}
      />
      <div style={{ width: "100%", maxWidth: 480 }}>
        <ComposerBar
          value={text}
          onChange={setText}
          onSubmit={handleSubmit}
          isRunning={false}
          isSubmitting={isSubmitting}
          isViewingPastVersion={false}
        />
        {error && (
          <div style={{ marginTop: 8 }}>
            <ErrorBanner message={error} />
          </div>
        )}
      </div>
      <NewChatDialog isOpen={isDialogOpen} onOpenChange={setIsDialogOpen} onCreated={handleCreated} />
    </VStack>
  );
}
