"use client";

// 長文の先頭だけを見せて「続きを見る」で全文展開する自作コンポーネント。
// Astryxの`Collapsible`はトリガーと中身が別（中身は開くまで非表示）だが、
// ここでは「先頭を常に見せたまま続きだけ展開する」挙動が必要なため自作する。

import { useState } from "react";
import { Button } from "@astryxdesign/core/Button";
import { VStack } from "@astryxdesign/core/VStack";

type Props = {
  children: React.ReactNode;
  previewLines?: number;
};

export function Collapsible({ children, previewLines = 2 }: Props) {
  const [isOpen, setIsOpen] = useState(false);

  if (isOpen) {
    return (
      <VStack gap={1}>
        {children}
        <Button
          label="閉じる"
          variant="ghost"
          size="sm"
          onClick={() => setIsOpen(false)}
        />
      </VStack>
    );
  }

  return (
    <VStack gap={1}>
      <div
        style={{
          display: "-webkit-box",
          WebkitLineClamp: previewLines,
          WebkitBoxOrient: "vertical",
          overflow: "hidden",
        }}
      >
        {children}
      </div>
      <Button
        label="続きを見る"
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(true)}
      />
    </VStack>
  );
}
