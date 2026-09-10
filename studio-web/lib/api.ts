import type { Chat, ChatSummary, LibraryItem } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) {
    let message = "リクエストに失敗した";
    try {
      const data = await res.json();
      if (typeof data?.error === "string") message = data.error;
    } catch {
      // 応答が空/非JSONの場合は既定メッセージのまま
    }
    throw new Error(message);
  }
  return res.json() as Promise<T>;
}

export function getLibrary(): Promise<LibraryItem[]> {
  return request<{ items: LibraryItem[] }>("/api/library").then((d) => d.items);
}

export function getChats(): Promise<ChatSummary[]> {
  return request<{ chats: ChatSummary[] }>("/api/chats").then((d) => d.chats);
}

export function getChat(id: string): Promise<Chat> {
  return request<Chat>(`/api/chats/${id}`);
}

export function createChat(referenceId?: string): Promise<Chat> {
  return request<Chat>("/api/chats", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(referenceId ? { reference_id: referenceId } : {}),
  });
}

export function postMessage(id: string, text: string): Promise<Chat> {
  return request<Chat>(`/api/chats/${id}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}
