import type { Metadata } from "next";
import { DM_Sans, Fraunces } from "next/font/google";

import "./globals.css";

import { AppShell } from "@/components/layout/app-shell";
import { CommandPaletteProvider } from "@/components/ui/command-palette";
import { WorkspaceProvider } from "@/lib/workspace-context";

const dmSans = DM_Sans({
  subsets: ["latin"],
  variable: "--font-dm-sans",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

const fraunces = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
  style: ["normal", "italic"],
  axes: ["SOFT", "opsz"],
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
    <html lang="en" className={`${dmSans.variable} ${fraunces.variable}`}>
      <body>
        <CommandPaletteProvider>
          <WorkspaceProvider>
            <AppShell>{children}</AppShell>
          </WorkspaceProvider>
        </CommandPaletteProvider>
      </body>
    </html>
  );
}

