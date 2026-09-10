// 新規会話ダイアログ: ライブラリから元絵を選ぶか、元絵なしで作成する。
"use client";

import { useEffect, useState } from "react";
import { Dialog, DialogHeader } from "@astryxdesign/core/Dialog";
import { LayoutContent } from "@astryxdesign/core/Layout";
import { VStack } from "@astryxdesign/core/Stack";
import { ClickableCard } from "@astryxdesign/core/ClickableCard";
import { Thumbnail } from "@astryxdesign/core/Thumbnail";
import { Text } from "@astryxdesign/core/Text";
import { Spinner } from "@astryxdesign/core/Spinner";
import { ErrorBanner } from "@/components/common/ErrorBanner";
import { getLibrary, createChat } from "@/lib/api";
import type { Chat, LibraryItem } from "@/lib/types";

type NewChatDialogProps = {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  onCreated: (chat: Chat) => void;
};

export function NewChatDialog({ isOpen, onOpenChange, onCreated }: NewChatDialogProps) {
  const [items, setItems] = useState<LibraryItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isCreating, setIsCreating] = useState(false);

  useEffect(() => {
    if (!isOpen) return;
    setIsLoading(true);
    getLibrary()
      .then((list) => {
        setItems(list);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "ライブラリの取得に失敗した"))
      .finally(() => setIsLoading(false));
  }, [isOpen]);

  const handleCreate = (referenceId?: string) => {
    if (isCreating) return; // 二重送信防止
    setIsCreating(true);
    createChat(referenceId)
      .then((chat) => onCreated(chat))
      .catch((e) => setError(e instanceof Error ? e.message : "会話の作成に失敗した"))
      .finally(() => setIsCreating(false));
  };

  return (
    <Dialog isOpen={isOpen} onOpenChange={onOpenChange} purpose="form" width={480}>
      <DialogHeader title="新しい会話" onOpenChange={onOpenChange} />
      <LayoutContent>
        <VStack gap={3} padding={4}>
          <ClickableCard
            label="元絵なしで、新しくつくる"
            onClick={() => handleCreate(undefined)}
            isDisabled={isCreating}
          >
            <Text type="body" weight="bold">
              元絵なしで、新しくつくる
            </Text>
          </ClickableCard>
          {isLoading && <Spinner label="読み込み中" />}
          {error && <ErrorBanner message={error} />}
          {items.map((item) => (
            <ClickableCard
              key={item.id}
              label={item.title || "無題の素材"}
              onClick={() => handleCreate(item.id)}
              isDisabled={isCreating}
            >
              <VStack gap={2}>
                <Thumbnail src={item.thumbnail} alt={item.title} />
                <Text type="body">{item.title || "無題の素材"}</Text>
                {item.notes && <Text type="supporting">{item.notes}</Text>}
              </VStack>
            </ClickableCard>
          ))}
        </VStack>
      </LayoutContent>
    </Dialog>
  );
}
