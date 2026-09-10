// 会話ごとの表示状態(選択中の版・最新追従・メッセージ一覧のスクロール位置)を保持する。
// app/chat/[id]/page.tsxはルート遷移でアンマウントされるため、
// この値をlayout.tsx直下のProviderが持つMapに保存し、会話に戻ったときに復元する。

"use client";

import { createContext, useCallback, useContext, useReducer, useRef, type ReactNode } from "react";

type ViewState = {
  // nullの間は最新版に自動追従する。過去版を明示選択するとその版のidが入る。
  selectedVersionId: string | null;
  followLatest: boolean;
  scrollTop: number;
};

const DEFAULT_STATE: ViewState = { selectedVersionId: null, followLatest: true, scrollTop: 0 };

type ViewStateContextValue = {
  get: (chatId: string) => ViewState;
  set: (chatId: string, patch: Partial<ViewState>) => void;
};

const ViewStateContext = createContext<ViewStateContextValue | null>(null);

export function ViewStateProvider({ children }: { children: ReactNode }) {
  const mapRef = useRef(new Map<string, ViewState>());

  const get = useCallback((chatId: string) => mapRef.current.get(chatId) ?? DEFAULT_STATE, []);
  const set = useCallback((chatId: string, patch: Partial<ViewState>) => {
    const current = mapRef.current.get(chatId) ?? DEFAULT_STATE;
    mapRef.current.set(chatId, { ...current, ...patch });
  }, []);

  return <ViewStateContext.Provider value={{ get, set }}>{children}</ViewStateContext.Provider>;
}

export function useViewState(chatId: string) {
  const ctx = useContext(ViewStateContext);
  if (!ctx) throw new Error("useViewState must be used within ViewStateProvider");

  // chatIdが変わったら描画中にMapから復元する(effect経由だと1描画分遅れて古い値を使ってしまうため)
  const cacheRef = useRef<{ chatId: string; state: ViewState }>({ chatId, state: ctx.get(chatId) });
  if (cacheRef.current.chatId !== chatId) {
    cacheRef.current = { chatId, state: ctx.get(chatId) };
  }

  const [, forceRender] = useReducer((n: number) => n + 1, 0);

  const update = useCallback(
    (patch: Partial<ViewState>) => {
      ctx.set(chatId, patch);
      cacheRef.current = { chatId, state: { ...cacheRef.current.state, ...patch } };
      forceRender();
    },
    [chatId, ctx],
  );

  return { ...cacheRef.current.state, update };
}
