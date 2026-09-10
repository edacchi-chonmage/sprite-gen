import { ClickableCard } from "@astryxdesign/core/ClickableCard";
import { HStack } from "@astryxdesign/core/HStack";
import { Thumbnail } from "@astryxdesign/core/Thumbnail";
import { Badge } from "@astryxdesign/core/Badge";
import type { Version } from "@/lib/types";

type Props = {
  version: Version;
  index: number; // 1始まりの版番号
  isLatest: boolean;
  onSelect: (versionId: string) => void;
};

export function VersionCard({ version, index, isLatest, onSelect }: Props) {
  const label = `第${index}版${isLatest ? " · 最新" : ""} — ${version.title}`;
  return (
    <ClickableCard label={label} onClick={() => onSelect(version.id)}>
      <HStack gap={2} vAlign="center">
        <Thumbnail src={version.image} alt={version.title} />
        <HStack gap={1} wrap="wrap">
          <Badge variant={isLatest ? "success" : "neutral"} label={`第${index}版`} />
          {isLatest && <Badge variant="info" label="最新" />}
        </HStack>
        <span>{version.title}</span>
      </HStack>
    </ClickableCard>
  );
}
