// 作品プレビュー本体（画像/GIF）。既存index.htmlのpanZoom()と同等の操作感を自作で再現する。
// Astryxに該当部品なしのため自作（設計書2節）。StyleXコンパイラは未導入のためインラインstyleで実装する。

"use client";

import { forwardRef, useEffect, useImperativeHandle } from "react";
import { usePanZoom, type PanZoomHandle } from "@/hooks/usePanZoom";

export type { PanZoomHandle };

type PanZoomCanvasProps = {
  src: string;
  alt: string;
  /** 指定時、4px未満の動きだったクリックでのみ発火する（ドラッグ操作と区別するため） */
  onClick?: () => void;
};

export const PanZoomCanvas = forwardRef<PanZoomHandle, PanZoomCanvasProps>(function PanZoomCanvas(
  { src, alt, onClick },
  ref,
) {
  const { areaRef, imgRef, step, fit, wasMoved } = usePanZoom();

  useImperativeHandle(ref, () => ({ step, fit }), [step, fit]);

  // 画像が切り替わったら拡大・移動状態をリセットする（既存挙動: 版ごとに独立したcanvasを作り直すのと同等）
  useEffect(() => {
    fit();
  }, [src, fit]);

  return (
    <div
      ref={areaRef}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      aria-label={onClick ? `${alt}を拡大` : undefined}
      onClick={() => {
        if (onClick && !wasMoved()) onClick();
      }}
      onKeyDown={(e) => {
        if (onClick && (e.key === "Enter" || e.key === " ")) {
          e.preventDefault();
          onClick();
        }
      }}
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        minHeight: 0,
        overflow: "hidden",
        touchAction: "none",
        cursor: "grab",
        borderRadius: 12,
        border: "1px solid #d8ddd6",
        backgroundColor: "#e3e7df",
        backgroundImage:
          "linear-gradient(45deg,#eef1e9 25%,transparent 25%),linear-gradient(-45deg,#eef1e9 25%,transparent 25%),linear-gradient(45deg,transparent 75%,#eef1e9 75%),linear-gradient(-45deg,transparent 75%,#eef1e9 75%)",
        backgroundSize: "20px 20px",
        backgroundPosition: "0 0, 0 10px, 10px -10px, -10px 0",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <img
        ref={imgRef}
        src={src}
        alt={alt}
        draggable={false}
        style={{
          width: "90%",
          height: "90%",
          objectFit: "contain",
          imageRendering: "pixelated",
          userSelect: "none",
          pointerEvents: "none",
          transformOrigin: "center",
        }}
      />
    </div>
  );
});
