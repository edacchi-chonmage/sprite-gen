// モバイル用: AppShellのmobileNavドロワーに入れる会話一覧＋新規作成ボタン。
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAppShellMobile } from "@astryxdesign/core/AppShell";
import { SideNavSection, SideNavItem } from "@astryxdesign/core/SideNav";
import { Button } from "@astryxdesign/core/Button";
import { VStack } from "@astryxdesign/core/Stack";
import { saveLastChatId } from "@/hooks/useChatList";
import { NewChatDialog } from "./NewChatDialog";
import type { Chat, ChatSummary } from "@/lib/types";

type ChatMobileNavProps = {
  chats: ChatSummary[];
  currentChatId?: string;
};

export function ChatMobileNav({ chats, currentChatId }: ChatMobileNavProps) {
  const router = useRouter();
  const { closeMobileNav } = useAppShellMobile();
  const [isNewChatOpen, setIsNewChatOpen] = useState(false);

  const handleSelect = (id: string) => {
    saveLastChatId(id);
    closeMobileNav();
    router.push(`/chat/${id}`);
  };

  const handleCreated = (chat: Chat) => {
    setIsNewChatOpen(false);
    saveLastChatId(chat.id);
    closeMobileNav();
    router.push(`/chat/${chat.id}`);
  };

  return (
    <VStack gap={2} padding={3}>
      <Button label="新規作成" variant="secondary" size="lg" width="100%" onClick={() => setIsNewChatOpen(true)} />
      <SideNavSection title="会話">
        {chats.map((chat) => (
          <SideNavItem
            key={chat.id}
            label={chat.title || "無題の会話"}
            isSelected={chat.id === currentChatId}
            onClick={() => handleSelect(chat.id)}
          />
        ))}
      </SideNavSection>
      <NewChatDialog isOpen={isNewChatOpen} onOpenChange={setIsNewChatOpen} onCreated={handleCreated} />
    </VStack>
  );
}
