// 特徴の整理・評価 / 生成に使ったプロンプト / 参照した素材 / コマを並べて確認 の折りたたみ群。
// 該当フィールドが無いversion（失敗時フォールバック等）では該当セクションごと非表示にする。

"use client";

import { Collapsible } from "@astryxdesign/core/Collapsible";
import { Card } from "@astryxdesign/core/Card";
import { VStack } from "@astryxdesign/core/VStack";
import { Text } from "@astryxdesign/core/Text";
import { Markdown } from "@astryxdesign/core/Markdown";
import type { Version } from "@/lib/types";

type DetailSectionsProps = {
  version: Version;
  onOpenImage: (src: string, alt: string) => void;
};

const thumbButtonStyle: React.CSSProperties = {
  border: "1px solid #d8ddd6",
  borderRadius: 8,
  padding: 0,
  cursor: "zoom-in",
  background: "#fff",
  overflow: "hidden",
};

const thumbImgStyle: React.CSSProperties = {
  width: "100%",
  display: "block",
  imageRendering: "pixelated",
};

export function DetailSections({ version, onOpenImage }: DetailSectionsProps) {
  const hasReview = Boolean(version.analysis || version.review);
  const hasPrompt = Boolean(version.prompt);
  const hasSources = Boolean(version.sources?.length || version.references?.length);
  const hasFrames = Boolean(version.contact || version.inserted);

  if (!hasReview && !hasPrompt && !hasSources && !hasFrames) return null;

  return (
    <VStack gap={2} width="100%">
      {hasReview && (
        <Card>
          <Collapsible trigger="特徴の整理・評価" defaultIsOpen={false}>
            <VStack gap={2}>
              {version.analysis && <Markdown>{version.analysis}</Markdown>}
              {version.review && (
                <VStack gap={1}>
                  <Text type="body">{version.review.summary}</Text>
                  {version.review.issues.length > 0 && (
                    <ul style={{ margin: 0, paddingInlineStart: 20 }}>
                      {version.review.issues.map((issue, i) => (
                        <li key={i}>
                          <Text type="body">{issue}</Text>
                        </li>
                      ))}
                    </ul>
                  )}
                </VStack>
              )}
            </VStack>
          </Collapsible>
        </Card>
      )}

      {hasPrompt && (
        <Card>
          <Collapsible trigger="生成に使ったプロンプト" defaultIsOpen={false}>
            <Markdown>{version.prompt ?? ""}</Markdown>
          </Collapsible>
        </Card>
      )}

      {hasSources && (
        <Card>
          <Collapsible trigger="参照した素材" defaultIsOpen={false}>
            <VStack gap={2}>
              {version.sources && version.sources.length > 0 && (
                <VStack gap={1}>
                  {version.sources.map((s, i) => (
                    <a key={i} href={s.url} target="_blank" rel="noopener noreferrer">
                      {s.title}
                    </a>
                  ))}
                </VStack>
              )}
              {version.references && version.references.length > 0 && (
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fill, minmax(80px, 1fr))",
                    gap: 8,
                  }}
                >
                  {version.references.map((url, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => onOpenImage(url, `参照素材${i + 1}`)}
                      style={thumbButtonStyle}
                    >
                      <img src={url} alt={`参照素材${i + 1}`} style={{ ...thumbImgStyle, height: 80, objectFit: "contain" }} />
                    </button>
                  ))}
                </div>
              )}
            </VStack>
          </Collapsible>
        </Card>
      )}

      {hasFrames && (
        <Card>
          <Collapsible trigger="コマを並べて確認" defaultIsOpen={false}>
            <VStack gap={2}>
              {version.contact && (
                <button type="button" onClick={() => onOpenImage(version.contact!, "コマ割り")} style={thumbButtonStyle}>
                  <img src={version.contact} alt="コマ割り" style={thumbImgStyle} />
                </button>
              )}
              {version.inserted && (
                <button
                  type="button"
                  onClick={() => onOpenImage(version.inserted!, "補間したコマ")}
                  style={thumbButtonStyle}
                >
                  <img src={version.inserted} alt="補間したコマ" style={thumbImgStyle} />
                </button>
              )}
            </VStack>
          </Collapsible>
        </Card>
      )}
    </VStack>
  );
}
