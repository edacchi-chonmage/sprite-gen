// 比較表示（2カラム）。元絵/最初の版と、現在表示中の版を並べる。

"use client";

import { HStack } from "@astryxdesign/core/HStack";
import { VStack } from "@astryxdesign/core/VStack";
import { PanZoomCanvas } from "./PanZoomCanvas";

type CompareGridProps = {
  baseSrc: string;
  baseLabel: string;
  currentSrc: string;
  currentLabel: string;
  /** モバイル幅など2カラムが狭すぎる時は縦積みにする */
  stacked?: boolean;
};

export function CompareGrid({ baseSrc, baseLabel, currentSrc, currentLabel, stacked = false }: CompareGridProps) {
  const Container = stacked ? VStack : HStack;
  const panels = [
    { src: baseSrc, label: baseLabel },
    { src: currentSrc, label: currentLabel },
  ];

  return (
    <Container gap={2} height="100%" width="100%">
      {panels.map((p) => (
        <figure
          key={p.label}
          style={{
            margin: 0,
            flex: 1,
            minWidth: 0,
            minHeight: 0,
            display: "flex",
            flexDirection: "column",
            height: "100%",
          }}
        >
          <figcaption style={{ fontSize: 11, color: "#717872", marginBottom: 6 }}>{p.label}</figcaption>
          <div style={{ flex: 1, minHeight: 0 }}>
            <PanZoomCanvas src={p.src} alt={p.label} />
          </div>
        </figure>
      ))}
    </Container>
  );
}
