// 拡大表示。設計書6節の決定通り、AstryxのDialog(器)の中に自作PanZoomCanvasを入れる
// （AstryxのLightbox部品とのhasZoom機能重複を避け、既存挙動の完全再現を優先）。

"use client";

import { useRef } from "react";
import { Dialog, DialogHeader } from "@astryxdesign/core/Dialog";
import { Layout, LayoutContent, LayoutFooter } from "@astryxdesign/core/Layout";
import { HStack } from "@astryxdesign/core/HStack";
import { Button } from "@astryxdesign/core/Button";
import { PanZoomCanvas, type PanZoomHandle } from "./PanZoomCanvas";

type LightboxViewProps = {
  isOpen: boolean;
  onOpenChange: (isOpen: boolean) => void;
  src: string;
  alt: string;
  title: string;
};

export function LightboxView({ isOpen, onOpenChange, src, alt, title }: LightboxViewProps) {
  const canvasRef = useRef<PanZoomHandle>(null);

  return (
    <Dialog isOpen={isOpen} onOpenChange={onOpenChange} variant="fullscreen" purpose="info">
      <Layout
        header={<DialogHeader title={title} onOpenChange={onOpenChange} />}
        content={
          <LayoutContent padding={2} isScrollable={false}>
            <div style={{ height: "100%", minHeight: 0 }}>
              {isOpen && <PanZoomCanvas ref={canvasRef} src={src} alt={alt} />}
            </div>
          </LayoutContent>
        }
        footer={
          <LayoutFooter hasDivider>
            <HStack gap={2} justify="center">
              <Button label="縮小" size="sm" onClick={() => canvasRef.current?.step(1 / 1.4)}>
                −
              </Button>
              <Button label="全体表示" size="sm" onClick={() => canvasRef.current?.fit()} />
              <Button label="拡大" size="sm" onClick={() => canvasRef.current?.step(1.4)}>
                ＋
              </Button>
            </HStack>
          </LayoutFooter>
        }
      />
    </Dialog>
  );
}
