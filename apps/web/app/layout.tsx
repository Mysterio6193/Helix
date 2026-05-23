import type { Metadata } from "next";
import { DM_Sans } from "next/font/google";

import "./globals.css";

import { AppShell } from "@/components/layout/app-shell";
import { CommandPaletteProvider } from "@/components/ui/command-palette";

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Helix — Creative Operating System",
  description:
    "Helix is the AI-native creative operating system for restaurants and food brands.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={dmSans.variable}>
      <body>
        <CommandPaletteProvider>
          <AppShell>{children}</AppShell>
        </CommandPaletteProvider>
      </body>
    </html>
  );
}

