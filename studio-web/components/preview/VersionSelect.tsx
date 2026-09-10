// 版セレクト。AstryxのSelectorが存在したためそれを使う（設計書のメモでは「未確認」だったが実物確認済み）。

"use client";

import { Selector } from "@astryxdesign/core/Selector";
import type { Version } from "@/lib/types";

type VersionSelectProps = {
  versions: Version[];
  selectedId: string;
  onSelect: (id: string) => void;
};

export function VersionSelect({ versions, selectedId, onSelect }: VersionSelectProps) {
  const latestId = versions[versions.length - 1]?.id;
  const options = versions
    .map((v, i) => ({
      value: v.id,
      label: `第${i + 1}版${v.id === latestId ? " · 最新" : ""} — ${v.title}`,
    }))
    .reverse();

  return (
    <Selector
      label="表示する版"
      isLabelHidden
      options={options}
      value={selectedId}
      onChange={onSelect}
      size="sm"
    />
  );
}
