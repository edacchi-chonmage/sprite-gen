// 作品プレビュー全体を束ねるコンポーネント。PC作品パネル/モバイルBottomSheet中身どちらからも使われる想定
// （PC/モバイルの入れ物側は「統合」担当のapp/chat/[id]/page.tsxが用意する）。
//
// ツール列: アニメ/静止Switch（animationが無ければ非表示）、比較Switch、−/全体/+、拡大表示、保存(素の<a download>)。
// 過去版表示中はBadge+「最新版へ戻る」Buttonのバナー。
// versionが無くreferenceがある時は元絵（ライブラリのサムネ）を表示、どちらも無い時は空状態の案内。

"use client";

import { useEffect, useRef, useState } from "react";
import { VStack } from "@astryxdesign/core/VStack";
import { HStack } from "@astryxdesign/core/HStack";
import { Button } from "@astryxdesign/core/Button";
import { Switch } from "@astryxdesign/core/Switch";
import { Badge } from "@astryxdesign/core/Badge";
import { Text } from "@astryxdesign/core/Text";
import { EmptyState } from "@astryxdesign/core/EmptyState";
import type { Chat, Version, LibraryItem } from "@/lib/types";
import { getLibrary } from "@/lib/api";
import { PanZoomCanvas, type PanZoomHandle } from "./PanZoomCanvas";
import { CompareGrid } from "./CompareGrid";
import { VersionSelect } from "./VersionSelect";
import { LightboxView } from "./LightboxView";
import { DetailSections } from "./DetailSections";

type PreviewStageProps = {
  chat: Chat;
  version: Version | undefined;
  versions: Version[];
  onSelectVersion: (id: string) => void;
  isMobile: boolean;
};

export function PreviewStage({ chat, version, versions, onSelectVersion, isMobile }: PreviewStageProps) {
  const [showAnimation, setShowAnimation] = useState(Boolean(version?.animation));
  const [compare, setCompare] = useState(false);
  const [lightbox, setLightbox] = useState<{ src: string; alt: string } | null>(null);
  const [reference, setReference] = useState<LibraryItem | null>(null);
  const canvasRef = useRef<PanZoomHandle>(null);

  const latestId = versions[versions.length - 1]?.id;
  const isPastVersion = version !== undefined && version.id !== latestId;

  // 版が切り替わったらアニメ表示状態を、その版のanimation有無に合わせ直す
  useEffect(() => {
    setShowAnimation(Boolean(version?.animation));
  }, [version?.id, version?.animation]);

  // 元絵(reference)が指定されていればライブラリから引く。versionの有無に関わらず、生成が進んでも参照元は表示し続ける
  useEffect(() => {
    if (!chat.reference_id) {
      setReference(null);
      return;
    }
    let cancelled = false;
    getLibrary()
      .then((items) => {
        if (!cancelled) setReference(items.find((item) => item.id === chat.reference_id) ?? null);
      })
      .catch(() => {
        if (!cancelled) setReference(null);
      });
    return () => {
      cancelled = true;
    };
  }, [chat.reference_id]);

  if (!version && !reference) {
    return (
      <VStack height="100%" align="center" justify="center" padding={6}>
        <EmptyState
          title="まだ作品がない"
          description="メッセージを送るか、ライブラリから元絵を選ぶと作品がここに表示される"
        />
      </VStack>
    );
  }

  const displaySrc = version ? (showAnimation && version.animation ? version.animation : version.image) : reference!.thumbnail;
  const displayAlt = version ? version.title : reference!.title;
  const compareBaseSrc = reference?.thumbnail ?? versions[0]?.image;
  const compareBaseLabel = reference ? "元絵" : "最初の版";
  const canCompare = Boolean(compareBaseSrc) && compareBaseSrc !== displaySrc;

  return (
    <VStack height="100%" gap={2} minHeight={0} width="100%">
      {reference && <Text type="supporting">参照：{reference.title}</Text>}

      {isPastVersion && (
        <HStack gap={2} align="center" wrap="wrap" width="100%">
          <Badge variant="warning" label="過去の版を見ています" />
          <Button label="最新版へ戻る" size="sm" onClick={() => latestId && onSelectVersion(latestId)} />
        </HStack>
      )}

      <VStack gap={2} width="100%">
        <HStack gap={2} align="center" wrap="wrap">
          {version?.animation && <Switch label="アニメで再生" value={showAnimation} onChange={setShowAnimation} size="sm" />}
          {canCompare && <Switch label="比較" value={compare} onChange={setCompare} size="sm" />}
        </HStack>
        <HStack gap={2} align="center" wrap="wrap">
          <Button label="縮小" size="lg" isDisabled={compare} onClick={() => canvasRef.current?.step(1 / 1.4)}>
            −
          </Button>
          <Button label="全体表示" size="lg" isDisabled={compare} onClick={() => canvasRef.current?.fit()} />
          <Button label="拡大" size="lg" isDisabled={compare} onClick={() => canvasRef.current?.step(1.4)}>
            ＋
          </Button>
          <Button label="拡大表示" size="lg" onClick={() => setLightbox({ src: displaySrc, alt: displayAlt })} />
          <a
            href={displaySrc}
            download
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              minHeight: 32,
              padding: "0 12px",
              border: "1px solid #cbd2c9",
              borderRadius: 8,
              fontSize: 12,
              textDecoration: "none",
              color: "inherit",
            }}
          >
            保存
          </a>
        </HStack>
      </VStack>

      <div style={{ flex: 1, minHeight: isMobile ? 220 : 320 }}>
        {compare && compareBaseSrc ? (
          <CompareGrid
            baseSrc={compareBaseSrc}
            baseLabel={compareBaseLabel}
            currentSrc={displaySrc}
            currentLabel={displayAlt}
            stacked={isMobile}
          />
        ) : (
          <PanZoomCanvas ref={canvasRef} src={displaySrc} alt={displayAlt} />
        )}
      </div>

      {versions.length > 0 && (
        <VersionSelect versions={versions} selectedId={version?.id ?? latestId ?? ""} onSelect={onSelectVersion} />
      )}

      {version && <DetailSections version={version} onOpenImage={(src, alt) => setLightbox({ src, alt })} />}

      <LightboxView
        isOpen={lightbox !== null}
        onOpenChange={(open) => {
          if (!open) setLightbox(null);
        }}
        src={lightbox?.src ?? ""}
        alt={lightbox?.alt ?? ""}
        title={lightbox?.alt ?? "拡大表示"}
      />
    </VStack>
  );
}
