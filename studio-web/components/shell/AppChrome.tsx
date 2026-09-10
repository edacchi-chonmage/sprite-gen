// layout.tsx直下から使う配線コンポーネント。
// layout.tsxはmetadataをexportする都合でServer Componentのままにしたいため、
// useChatList/usePathname等のClient側の配線をここに切り出す。
"use client";

import { useEffect, useRef, type ReactNode } from "react";
import { usePathname } from "next/navigation";
import { useChatList } from "@/hooks/useChatList";
import { ViewStateProvider } from "@/hooks/useViewState";
import { StudioShell } from "./StudioShell";
import { ChatSideNav } from "./ChatSideNav";
import { ChatMobileNav } from "./ChatMobileNav";

export function AppChrome({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const currentChatId = pathname.match(/^\/chat\/([^/]+)/)?.[1];
  const { chats, reload } = useChatList();

  // 新規作成直後など、遷移先のchatIdが一覧に無い時だけ一覧を更新する
  // (chatIdごとに1回だけ再試行し、無限ループを避ける)
  const reloadedForRef = useRef<string | null>(null);
  useEffect(() => {
    if (!currentChatId) return;
    if (chats.some((c) => c.id === currentChatId)) return;
    if (reloadedForRef.current === currentChatId) return;
    reloadedForRef.current = currentChatId;
    reload();
  }, [currentChatId, chats, reload]);

  const currentTitle = chats.find((c) => c.id === currentChatId)?.title;

  return (
    <ViewStateProvider>
      <StudioShell
        sideNav={<ChatSideNav chats={chats} currentChatId={currentChatId} />}
        mobileNav={<ChatMobileNav chats={chats} currentChatId={currentChatId} />}
        chatTitle={currentTitle}
      >
        {children}
      </StudioShell>
    </ViewStateProvider>
  );
}
