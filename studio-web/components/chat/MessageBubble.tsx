import { Markdown } from "@astryxdesign/core/Markdown";
import { Card } from "@astryxdesign/core/Card";
import type { Message } from "@/lib/types";
import { Collapsible } from "@/components/common/Collapsible";

// assistantの長文（目安: 改行3行以上）だけ折りたたみ対象にする。
const LONG_TEXT_LINE_THRESHOLD = 3;

type Props = {
  message: Message;
};

export function MessageBubble({ message }: Props) {
  const isLong =
    message.role === "assistant" &&
    message.text.split("\n").length >= LONG_TEXT_LINE_THRESHOLD;

  return (
    <Card variant={message.role === "user" ? "muted" : "default"}>
      {isLong ? (
        <Collapsible>
          <Markdown>{message.text}</Markdown>
        </Collapsible>
      ) : (
        <Markdown>{message.text}</Markdown>
      )}
    </Card>
  );
}
