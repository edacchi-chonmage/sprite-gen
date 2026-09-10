"use client";

// 長文の先頭だけを見せて「続きを見る」で全文展開する自作コンポーネント。
// Astryxの`Collapsible`はトリガーと中身が別（中身は開くまで非表示）だが、
// ここでは「先頭を常に見せたまま続きだけ展開する」挙動が必要なため自作する。
//
// -webkit-line-clampは直接の子がブロック要素（Markdownが出すp要素など）だと
// 行単位でなくブロック単位でしか数えられず折りたためないため使わない。
// 代わりに実測した1行の高さ×previewLinesを上限にして、実際の高さと比較する。

import { useLayoutEffect, useRef, useState } from "react";
import { Button } from "@astryxdesign/core/Button";
import { VStack } from "@astryxdesign/core/VStack";

type Props = {
  children: React.ReactNode;
  previewLines?: number;
};

export function Collapsible({ children, previewLines = 4 }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const contentRef = useRef<HTMLDivElement>(null);
  const [collapsedHeight, setCollapsedHeight] = useState<number | null>(null);
  const [isOverflowing, setIsOverflowing] = useState(false);

  useLayoutEffect(() => {
    const el = contentRef.current;
    if (!el) return;
    const sample = el.querySelector("p, li, h1, h2, h3, h4, h5, h6") ?? el;
    const lineHeight = parseFloat(getComputedStyle(sample).lineHeight);
    const max = (Number.isFinite(lineHeight) ? lineHeight : 20) * previewLines;
    setCollapsedHeight(max);
    setIsOverflowing(el.scrollHeight > max + 1);
  }, [children, previewLines]);

  return (
    <VStack gap={1}>
      <div
        ref={contentRef}
        style={
          !isOpen && collapsedHeight !== null
            ? { maxHeight: collapsedHeight, overflow: "hidden" }
            : undefined
        }
      >
        {children}
      </div>
      {isOverflowing && (
        <Button
          label={isOpen ? "閉じる" : "続きを見る"}
          variant="ghost"
          size="sm"
          onClick={() => setIsOpen((v) => !v)}
        />
      )}
    </VStack>
  );
}
