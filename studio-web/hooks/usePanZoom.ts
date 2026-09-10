// 既存 sprite_gen/serve/chat_ui/index.html の panZoom() をReact用に移植したもの。
// wheelで拡大縮小、pointerでドラッグ移動、2本指ピンチ、scale 0.25〜20。
// 4px未満の動きはクリック扱い（wasMoved()がfalseを返す）。

"use client";

import { useCallback, useEffect, useRef } from "react";

const MIN_SCALE = 0.25;
const MAX_SCALE = 20;
const CLICK_THRESHOLD = 4;

export type PanZoomHandle = {
  step: (factor: number) => void;
  fit: () => void;
};

export function usePanZoom() {
  const areaRef = useRef<HTMLDivElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  const scaleRef = useRef(1);
  const xRef = useRef(0);
  const yRef = useRef(0);
  const movedRef = useRef(false);
  const startRef = useRef({ x: 0, y: 0 });
  const pointersRef = useRef(new Map<number, { x: number; y: number }>());
  const distanceRef = useRef(0);

  const draw = useCallback(() => {
    const img = imgRef.current;
    if (img) {
      img.style.transform = `translate(${xRef.current}px,${yRef.current}px) scale(${scaleRef.current})`;
    }
  }, []);

  const step = useCallback(
    (factor: number) => {
      scaleRef.current = Math.max(MIN_SCALE, Math.min(MAX_SCALE, scaleRef.current * factor));
      draw();
    },
    [draw],
  );

  const fit = useCallback(() => {
    scaleRef.current = 1;
    xRef.current = 0;
    yRef.current = 0;
    draw();
  }, [draw]);

  const wasMoved = useCallback(() => movedRef.current, []);

  useEffect(() => {
    const area = areaRef.current;
    if (!area) return;

    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      step(Math.exp(-e.deltaY * 0.002));
    };

    const onPointerDown = (e: PointerEvent) => {
      if (!pointersRef.current.size) {
        movedRef.current = false;
        startRef.current = { x: e.clientX, y: e.clientY };
      }
      distanceRef.current = 0;
      pointersRef.current.set(e.pointerId, { x: e.clientX, y: e.clientY });
      area.setPointerCapture(e.pointerId);
    };

    const onPointerMove = (e: PointerEvent) => {
      const pointers = pointersRef.current;
      if (!pointers.has(e.pointerId)) return;
      const old = pointers.get(e.pointerId)!;
      pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
      if (pointers.size === 1) {
        const dx = e.clientX - old.x;
        const dy = e.clientY - old.y;
        xRef.current += dx;
        yRef.current += dy;
        if (Math.hypot(e.clientX - startRef.current.x, e.clientY - startRef.current.y) > CLICK_THRESHOLD) {
          movedRef.current = true;
        }
      } else {
        movedRef.current = true;
        const [a, b] = [...pointers.values()];
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (distanceRef.current) {
          scaleRef.current = Math.max(MIN_SCALE, Math.min(MAX_SCALE, scaleRef.current * (d / distanceRef.current)));
        }
        distanceRef.current = d;
      }
      draw();
    };

    const onPointerEnd = (e: PointerEvent) => {
      pointersRef.current.delete(e.pointerId);
      distanceRef.current = 0;
    };

    area.addEventListener("wheel", onWheel, { passive: false });
    area.addEventListener("pointerdown", onPointerDown);
    area.addEventListener("pointermove", onPointerMove);
    area.addEventListener("pointerup", onPointerEnd);
    area.addEventListener("pointercancel", onPointerEnd);
    return () => {
      area.removeEventListener("wheel", onWheel);
      area.removeEventListener("pointerdown", onPointerDown);
      area.removeEventListener("pointermove", onPointerMove);
      area.removeEventListener("pointerup", onPointerEnd);
      area.removeEventListener("pointercancel", onPointerEnd);
    };
  }, [draw, step]);

  return { areaRef, imgRef, step, fit, wasMoved };
}
