import type { KeyboardEvent } from "react";
import { TextArea } from "@astryxdesign/core/TextArea";
import { Button } from "@astryxdesign/core/Button";
import { VStack } from "@astryxdesign/core/VStack";
import { Text } from "@astryxdesign/core/Text";

type Props = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isRunning: boolean;
  isSubmitting: boolean;
  isViewingPastVersion: boolean;
};

export function ComposerBar({
  value,
  onChange,
  onSubmit,
  isRunning,
  isSubmitting,
  isViewingPastVersion,
}: Props) {
  // 制作中は入力だけ受け付ける（送信は不可）。次の依頼を先に入力しておけるように、あえて無効化しない。
  const hintMessage = isRunning
    ? "制作中。次の依頼は入力しておけるよ"
    : isViewingPastVersion
      ? "過去の版を表示中。最新版に戻ると依頼できるよ"
      : null;

  const canSubmit = value.trim() !== "" && !isRunning && !isSubmitting && !isViewingPastVersion;

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    // IME変換中のEnterは無視する
    if (e.nativeEvent.isComposing) return;
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      if (canSubmit) onSubmit();
    }
  };

  return (
    <VStack gap={1}>
      <div style={{ position: "relative", width: "100%" }}>
        <TextArea
          label="メッセージ"
          isLabelHidden
          value={value}
          onChange={onChange}
          onKeyDown={handleKeyDown}
          isDisabled={isSubmitting || isViewingPastVersion}
          placeholder="作りたい絵や、直したい動きを伝えてね"
          width="100%"
        />
        <div style={{ position: "absolute", right: 8, bottom: 8 }}>
          <Button
            label="送信"
            size="md"
            isDisabled={!canSubmit}
            isLoading={isSubmitting}
            onClick={onSubmit}
          />
        </div>
      </div>
      {hintMessage && <Text type="supporting">{hintMessage}</Text>}
    </VStack>
  );
}
