// 常時表示のエラーバナー。ユーザー操作で閉じる手段は持たせない（要件通り、isDismissableは指定しない＝既定false）。

import { Banner } from "@astryxdesign/core/Banner";

type Props = {
  message: string;
};

export function ErrorBanner({ message }: Props) {
  return <Banner status="error" title={message} collapsible={false} />;
}
