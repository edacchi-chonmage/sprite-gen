// AppShellを組み、topNavに「Sprite Studio」＋現在の会話タイトルを表示する共通シェル。
"use client";

import type { ReactNode } from "react";
import { AppShell, useAppShellMobile } from "@astryxdesign/core/AppShell";
import { TopNav, TopNavHeading } from "@astryxdesign/core/TopNav";
import { MobileNav } from "@astryxdesign/core/MobileNav";

// 子コンポーネントからモバイル判定を使うための再エクスポート。
export { useAppShellMobile as useStudioShellMobile };

type StudioShellProps = {
  sideNav?: ReactNode;
  mobileNav?: ReactNode;
  chatTitle?: string;
  children: ReactNode;
};

export function StudioShell({ sideNav, mobileNav, chatTitle, children }: StudioShellProps) {
  return (
    <AppShell
      topNav={<TopNav heading={<TopNavHeading heading="Sprite Studio" subheading={chatTitle} />} />}
      sideNav={sideNav}
      // MobileNavで包まないと単なる子要素として本文中にそのまま描画されてしまう
      // (ドロワーとしてのオフキャンバス表示・背景オーバーレイはMobileNav自身が担う)
      mobileNav={mobileNav ? { content: <MobileNav header="Sprite Studio">{mobileNav}</MobileNav> } : undefined}
      contentPadding={0}
    >
      {children}
    </AppShell>
  );
}
