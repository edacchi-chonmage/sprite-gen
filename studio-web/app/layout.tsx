import type { Metadata, Viewport } from "next";
import { Theme } from "@astryxdesign/core";
import { neutralTheme } from "@astryxdesign/theme-neutral/built";
import "./globals.css";
import { AppChrome } from "@/components/shell/AppChrome";

export const metadata: Metadata = {
  title: "Sprite Studio",
};

export const viewport: Viewport = {
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ja">
      <body>
        <Theme theme={neutralTheme} mode="light">
          <AppChrome>{children}</AppChrome>
        </Theme>
      </body>
    </html>
  );
}
