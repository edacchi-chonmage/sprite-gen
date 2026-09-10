// chat.phase / events[].text の文字列を、進捗表示用の5工程に対応付ける。
// 対応表は sprite_gen/serve/chat_studio.py の work()/submit()/event() が
// 実際に発行する文字列（固定文言のみ）を読んで作成した。

export const PHASE_STEPS = [
  "依頼を確認",
  "特徴を整理",
  "生成",
  "検査",
  "保存",
] as const;

export type PhaseStepResult = { step: number; label: (typeof PHASE_STEPS)[number] };

// 固定文言のみを対象にする。以下は意図的に対応表から外している：
// - 「使用モデル：...」「参考情報を検索している：...」「参考ページの内容を確認している：...」
//   「OrcaからClaude Sonnetを起動した。参照画像と依頼を確認している」
//   「Orcaの作業ターミナルを閉じられなかった。実行の取消しは送信済み」
//   → いずれも sonnet_bridge 内で計画作成(特徴を整理)と目視比較(検査)の両方から
//     発行され、文言だけでは工程を一意に決められないため null（直前の工程を保持）。
// - 「回答したよ」（discuss応答。生成を伴わないため5工程のどれにも該当しない）
// - 「処理を完了できなかった」「中断」（失敗時。どの工程で失敗したか文言からは分からない）
const KEYWORD_STEPS: Record<string, number> = {
  "依頼を入力してね": 0,
  "素材と履歴を確認中": 0,
  "Claude Sonnetが素材の特徴と動きを確認中": 1,
  "再生順序と間を調整中": 2,
  "Images 2.5で画像を生成中": 2,
  "画像を切り出して再生を作成中": 2,
  "Claude Sonnetが元絵と生成結果を比較中": 3,
  "新しい版を保存したよ": 4,
};

export function phaseStep(phase: string): PhaseStepResult | null {
  const step = KEYWORD_STEPS[phase];
  if (step === undefined) return null;
  return { step, label: PHASE_STEPS[step] };
}
