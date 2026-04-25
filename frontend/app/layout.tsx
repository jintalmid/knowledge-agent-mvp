import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "knowledge-agent-mvp",
  description: "Stage 0 module registry for an enterprise knowledge agent MVP.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
