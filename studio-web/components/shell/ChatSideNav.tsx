// PC用: 左サイドナビの会話一覧＋新規作成ボタン。
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { SideNav, SideNavSection, SideNavItem } from "@astryxdesign/core/SideNav";
import { Button } from "@astryxdesign/core/Button";
import { saveLastChatId } from "@/hooks/useChatList";
import { NewChatDialog } from "./NewChatDialog";
import type { Chat, ChatSummary } from "@/lib/types";

type ChatSideNavProps = {
  chats: ChatSummary[];
  currentChatId?: string;
};

export function ChatSideNav({ chats, currentChatId }: ChatSideNavProps) {
  const router = useRouter();
  const [isNewChatOpen, setIsNewChatOpen] = useState(false);

  const handleSelect = (id: string) => {
    saveLastChatId(id);
    router.push(`/chat/${id}`);
  };

  const handleCreated = (chat: Chat) => {
    setIsNewChatOpen(false);
    saveLastChatId(chat.id);
    router.push(`/chat/${chat.id}`);
  };

  return (
    <>
      <SideNav
        topContent={<Button label="新規作成" variant="secondary" width="100%" onClick={() => setIsNewChatOpen(true)} />}
      >
        <SideNavSection title="会話">
          {chats.map((chat) => (
            <SideNavItem
              key={chat.id}
              label={chat.title || "新しい作品"}
              isSelected={chat.id === currentChatId}
              onClick={() => handleSelect(chat.id)}
            />
          ))}
        </SideNavSection>
      </SideNav>
      <NewChatDialog isOpen={isNewChatOpen} onOpenChange={setIsNewChatOpen} onCreated={handleCreated} />
    </>
  );
}
