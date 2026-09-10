"use client";

import { use, useEffect, useRef, useState } from "react";
import { Layout, LayoutContent, LayoutPanel, LayoutHeader, LayoutFooter } from "@astryxdesign/core/Layout";
import { VStack } from "@astryxdesign/core/VStack";
import { Spinner } from "@astryxdesign/core/Spinner";
import { BottomSheet } from "@astryxdesign/core/BottomSheet";
import { useChat } from "@/hooks/useChat";
import { useDraft } from "@/hooks/useDraft";
import { useViewState } from "@/hooks/useViewState";
import { saveLastChatId } from "@/hooks/useChatList";
import { useStudioShellMobile } from "@/components/shell/StudioShell";
import { ProgressPanel } from "@/components/chat/ProgressPanel";
import { MessageList } from "@/components/chat/MessageList";
import { ComposerBar } from "@/components/chat/ComposerBar";
import { ErrorBanner } from "@/components/common/ErrorBanner";
import { PreviewStage } from "@/components/preview/PreviewStage";
import { describeChatError } from "@/lib/errorText";

export default function ChatPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { chat, error, isSubmitting, submit } = useChat(id);
  const draft = useDraft(id);
  const viewState = useViewState(id);
  const { isMobile } = useStudioShellMobile();

  useEffect(() => {
    saveLastChatId(id);
  }, [id]);

  const versions = chat?.versions ?? [];
  const latestId = versions.at(-1)?.id;
  const selectedVersion = viewState.followLatest
    ? versions.at(-1)
    : (versions.find((v) => v.id === viewState.selectedVersionId) ?? versions.at(-1));
  const isViewingPastVersion = !viewState.followLatest && Boolean(selectedVersion);

  const handleSelectVersion = (versionId: string) => {
    if (versionId === latestId) {
      viewState.update({ selectedVersionId: null, followLatest: true });
    } else {
      viewState.update({ selectedVersionId: versionId, followLatest: false });
    }
  };

  // 新版到着(versions配列が伸びた)を検知してモバイルのBottomSheetを自動で開く。
  // chatIdごとに前回件数を保持し、同じ会話で件数が伸びた時だけ開く(会話切替時のchat=null→ロード完了の谷間では開かない)
  const prevVersionsRef = useRef<{ chatId: string; count: number } | null>(null);
  const [isSheetOpen, setIsSheetOpen] = useState(false);
  useEffect(() => {
    if (!chat) return;
    const prev = prevVersionsRef.current;
    if (prev && prev.chatId === chat.id && versions.length > prev.count) setIsSheetOpen(true);
    prevVersionsRef.current = { chatId: chat.id, count: versions.length };
  }, [chat, versions.length]);

  // 会話に戻った時、保存しておいたスクロール位置を復元する。
  // chatがnull(読み込み中)→データありに変わった時、divが再マウントされるのでBoolean(chat)も依存に加える
  // (chatオブジェクト自体はポーリングのたびに変わるため、それを直接依存にすると復元がスクロールを妨げてしまう)
  const messageListRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (messageListRef.current) messageListRef.current.scrollTop = viewState.scrollTop;
  }, [id, viewState.scrollTop, Boolean(chat)]);
  const handleScroll = () => {
    if (messageListRef.current) viewState.update({ scrollTop: messageListRef.current.scrollTop });
  };

  const handleSubmit = async () => {
    if (!draft.text) return;
    await submit(draft.text);
    draft.clear();
  };

  if (!chat) {
    return (
      <VStack height="100%" align="center" justify="center">
        {error ? <ErrorBanner message={error} /> : <Spinner label="読み込み中" />}
      </VStack>
    );
  }

  const bannerMessage = error ?? (chat.status === "failed" && chat.error ? describeChatError(chat.error) : null);

  const progress = (
    <VStack gap={2}>
      <ProgressPanel chat={chat} />
      {bannerMessage && <ErrorBanner message={bannerMessage} />}
    </VStack>
  );

  const messages = (
    <div ref={messageListRef} onScroll={handleScroll} style={{ height: "100%", overflowY: "auto" }}>
      <MessageList chat={chat} onSelectVersion={handleSelectVersion} />
    </div>
  );

  const composer = (
    <ComposerBar
      value={draft.text}
      onChange={draft.setText}
      onSubmit={handleSubmit}
      isRunning={chat.status === "running"}
      isSubmitting={isSubmitting}
      isViewingPastVersion={isViewingPastVersion}
    />
  );

  if (isMobile) {
    const versionIndex = selectedVersion ? versions.findIndex((v) => v.id === selectedVersion.id) + 1 : 0;
    const versionLabel = selectedVersion
      ? `第${versionIndex}版${selectedVersion.id === latestId ? " · 最新" : ""}`
      : null;

    return (
      <>
        <Layout
          height="fill"
          content={
            <LayoutContent isScrollable={false} padding={0}>
              <VStack height="100%" gap={0}>
                <div style={{ padding: "12px 16px" }}>{progress}</div>
                <div style={{ flex: 1, minHeight: 0, padding: "0 16px" }}>{messages}</div>
              </VStack>
            </LayoutContent>
          }
          footer={
            <LayoutFooter hasDivider padding={0}>
              <VStack gap={0} width="100%">
                {!isSheetOpen && versionLabel && (
                  <button
                    type="button"
                    onClick={() => setIsSheetOpen(true)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      width: "100%",
                      padding: "8px 16px",
                      border: "none",
                      borderBottom: "1px solid #d8ddd6",
                      background: "#f4f6f1",
                      font: "inherit",
                      textAlign: "start",
                      cursor: "pointer",
                    }}
                  >
                    {selectedVersion && (
                      <img
                        src={selectedVersion.animation ?? selectedVersion.image}
                        alt=""
                        width={40}
                        height={40}
                        style={{ imageRendering: "pixelated", objectFit: "contain", borderRadius: 4, flexShrink: 0, background: "#e3e7df" }}
                      />
                    )}
                    {versionLabel}
                  </button>
                )}
                <div style={{ padding: "12px 16px calc(12px + env(safe-area-inset-bottom))" }}>{composer}</div>
              </VStack>
            </LayoutFooter>
          }
        />
        <BottomSheet isOpen={isSheetOpen} onOpenChange={setIsSheetOpen} label="作品プレビュー" height="capped" purpose="info">
          {/* ドラッグハンドルと最初の行が重なるため上に余白を確保する */}
          <div style={{ height: "100%", padding: "28px 16px 16px" }}>
            <PreviewStage chat={chat} version={selectedVersion} versions={versions} onSelectVersion={handleSelectVersion} isMobile />
          </div>
        </BottomSheet>
      </>
    );
  }

  return (
    <Layout
      height="fill"
      content={
        <LayoutContent padding={4} isScrollable={false}>
          <PreviewStage chat={chat} version={selectedVersion} versions={versions} onSelectVersion={handleSelectVersion} isMobile={false} />
        </LayoutContent>
      }
      end={
        <LayoutPanel width={420} hasDivider isScrollable={false} padding={0}>
          <Layout
            height="fill"
            header={<LayoutHeader hasDivider padding={3}>{progress}</LayoutHeader>}
            content={
              <LayoutContent isScrollable={false} padding={0}>
                <div style={{ height: "100%", padding: "0 16px" }}>{messages}</div>
              </LayoutContent>
            }
            footer={<LayoutFooter hasDivider padding={3}>{composer}</LayoutFooter>}
          />
        </LayoutPanel>
      }
    />
  );
}
