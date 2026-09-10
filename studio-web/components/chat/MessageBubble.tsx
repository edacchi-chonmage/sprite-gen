import { Markdown } from "@astryxdesign/core/Markdown";
import { Card } from "@astryxdesign/core/Card";
import { Text } from "@astryxdesign/core/Text";
import { VStack } from "@astryxdesign/core/VStack";
import type { Message } from "@/lib/types";
import { Collapsible } from "@/components/common/Collapsible";

type Props = {
  message: Message;
};

export function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <VStack gap={1} hAlign={isUser ? "end" : "start"}>
      <Text type="supporting">{isUser ? "あなた" : "制作アシスタント"}</Text>
      <Card variant={isUser ? "muted" : "default"} maxWidth={isUser ? "85%" : undefined}>
        {isUser ? (
          <Markdown>{message.text}</Markdown>
        ) : (
          <Collapsible>
            <Markdown>{message.text}</Markdown>
          </Collapsible>
        )}
      </Card>
    </VStack>
  );
}
