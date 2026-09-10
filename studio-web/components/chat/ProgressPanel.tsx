"use client";

import { useEffect, useRef, useState } from "react";
import { Stepper, Step } from "@astryxdesign/core/Stepper";
import { HStack } from "@astryxdesign/core/HStack";
import { VStack } from "@astryxdesign/core/VStack";
import { Badge } from "@astryxdesign/core/Badge";
import { Button } from "@astryxdesign/core/Button";
import { Dialog, DialogHeader } from "@astryxdesign/core/Dialog";
import type { Chat } from "@/lib/types";
import { PHASE_STEPS, phaseStep } from "@/lib/phase";

type Props = {
  chat: Chat;
};

function formatElapsed(ms: number): string {
  const totalSeconds = Math.max(0, Math.floor(ms / 1000));
  const mm = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const ss = String(totalSeconds % 60).padStart(2, "0");
  return `${mm}:${ss}`;
}

export function ProgressPanel({ chat }: Props) {
  // phase文字列がKEYWORD_STEPSに無い場合はnullが返るため、直前のstepを保持する。
  const lastStepRef = useRef(0);
  const resolved = phaseStep(chat.phase);
  if (resolved) lastStepRef.current = resolved.step;
  const activeStep = lastStepRef.current;

  // 経過時間: runningになった時点の時刻をstateで保持してカウントアップする。
  // ページ再読込直後などrunning開始をこの場で観測できなかった場合は、
  // chat.messagesに保存時刻が無いため(lib/types.ts参照)、events内で最も古い時刻を代用する。
  // それも無ければ「経過不明」とする。
  const [startedAt, setStartedAt] = useState<number | null>(null);
  const wasRunningRef = useRef(chat.status === "running");
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (chat.status === "running" && !wasRunningRef.current) {
      setStartedAt(Date.now());
    }
    if (chat.status !== "running") {
      setStartedAt(null);
    }
    wasRunningRef.current = chat.status === "running";
  }, [chat.status]);

  useEffect(() => {
    if (chat.status !== "running" || startedAt !== null) return;
    const earliestEvent = chat.events[0]?.time;
    if (earliestEvent) setStartedAt(new Date(earliestEvent).getTime());
  }, [chat.status, chat.events, startedAt]);

  useEffect(() => {
    if (chat.status !== "running") return;
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, [chat.status]);

  const elapsedLabel =
    chat.status === "running"
      ? startedAt !== null
        ? formatElapsed(now - startedAt)
        : "経過不明"
      : null;

  const latestVersion = chat.versions.at(-1) ?? null;
  const review = latestVersion?.review;
  const [isEventsOpen, setIsEventsOpen] = useState(false);

  return (
    <VStack gap={2}>
      <Stepper activeStep={activeStep} label="制作の工程">
        {PHASE_STEPS.map((label, i) => (
          <Step key={label} step={i} label={label} />
        ))}
      </Stepper>
      <HStack gap={2} vAlign="center" wrap="wrap">
        {elapsedLabel && <span>経過 {elapsedLabel}</span>}
        {chat.status === "idle" && latestVersion && (
          <Badge variant="success" label="生成完了" />
        )}
        {review &&
          (review.issues.length > 0 ? (
            <Badge variant="warning" label={`要確認 (${review.issues.length})`} />
          ) : (
            <Badge variant="success" label={latestVersion?.review_status} />
          ))}
        <Button
          label="経過を見る"
          variant="ghost"
          size="sm"
          onClick={() => setIsEventsOpen(true)}
        />
      </HStack>
      <Dialog isOpen={isEventsOpen} onOpenChange={setIsEventsOpen} purpose="info">
        <DialogHeader title="経過ログ" onOpenChange={setIsEventsOpen} />
        <VStack gap={2} padding={3}>
          {chat.events.length === 0 ? (
            <span>まだログが無い</span>
          ) : (
            chat.events.map((event, i) => (
              <div key={i}>
                <span>{event.time}</span> {event.text}
              </div>
            ))
          )}
        </VStack>
      </Dialog>
    </VStack>
  );
}
