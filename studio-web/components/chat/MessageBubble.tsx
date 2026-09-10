import { Markdown } from "@astryxdesign/core/Markdown";
import { Card } from "@astryxdesign/core/Card";
import { Text } from "@astryxdesign/core/Text";
import { VStack } from "@astryxdesign/core/VStack";
import type { Message } from "@/lib/types";
import { Collapsible } from "@/components/common/Collapsible";
import { describeChatError } from "@/lib/errorText";

type Props = {
  message: Message;
};

// サーバーが失敗を会話に残す時の接頭辞（chat_studio.py と同じ文言）
const FAILED_PREFIX = "処理を完了できなかった：";

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";
  const text = !isUser && message.text.startsWith(FAILED_PREFIX)
    ? FAILED_PREFIX + describeChatError(message.text.slice(FAILED_PREFIX.length))
    : message.text;

  return (
    <VStack gap={1} hAlign={isUser ? "end" : "start"}>
      <Text type="supporting">{isUser ? "あなた" : "制作アシスタント"}</Text>
      <Card variant={isUser ? "muted" : "default"} maxWidth={isUser ? "85%" : undefined}>
        {isUser ? (
          <Markdown>{text}</Markdown>
        ) : (
          <Collapsible>
            <Markdown>{text}</Markdown>
          </Collapsible>
        )}
      </Card>
    </VStack>
  );
}
