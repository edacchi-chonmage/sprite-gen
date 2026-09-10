import { VStack } from "@astryxdesign/core/VStack";
import type { Chat } from "@/lib/types";
import { MessageBubble } from "./MessageBubble";
import { VersionCard } from "./VersionCard";

type Props = {
  chat: Chat;
  onSelectVersion: (versionId: string) => void;
};

export function MessageList({ chat, onSelectVersion }: Props) {
  // Messageに保存時刻が無いため（lib/types.ts参照）、version.created_atとの突き合わせができない。
  // 設計の「時刻が無ければ末尾」の規定に従い、版カード群はメッセージ一覧の末尾にまとめて表示する。
  const latestId = chat.versions.at(-1)?.id;

  return (
    <VStack gap={3}>
      {chat.messages.map((message, i) => (
        <MessageBubble key={i} message={message} />
      ))}
      {chat.versions.map((version, i) => (
        <VersionCard
          key={version.id}
          version={version}
          index={i + 1}
          isLatest={version.id === latestId}
          onSelect={onSelectVersion}
        />
      ))}
    </VStack>
  );
}
