import type { KeyboardEvent } from "react";
import { TextArea } from "@astryxdesign/core/TextArea";
import { Button } from "@astryxdesign/core/Button";
import { VStack } from "@astryxdesign/core/VStack";
import { HStack } from "@astryxdesign/core/HStack";

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
  const disabledReason = isRunning
    ? "制作中は送信できない"
    : isSubmitting
      ? "送信中"
      : isViewingPastVersion
        ? "過去の版を見ている間は送信できない"
        : value === ""
          ? "テキストを入力してね"
          : null;

  const canSubmit = disabledReason === null;

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
      <HStack gap={2} vAlign="end">
        <TextArea
          label="メッセージ"
          isLabelHidden
          value={value}
          onChange={onChange}
          onKeyDown={handleKeyDown}
          isDisabled={isRunning || isSubmitting || isViewingPastVersion}
          placeholder="指示を入力(Ctrl/⌘+Enterで送信)"
        />
        <Button
          label="送信"
          size="lg"
          isDisabled={!canSubmit}
          isLoading={isSubmitting}
          onClick={onSubmit}
        />
      </HStack>
      {disabledReason && <span>{disabledReason}</span>}
    </VStack>
  );
}
