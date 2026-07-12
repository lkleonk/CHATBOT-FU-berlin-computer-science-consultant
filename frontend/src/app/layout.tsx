import type { Metadata } from "next";

import { DegreeProvider } from "@/context/DegreeContext";
import { SettingsProvider } from "@/context/SettingsContext";
import { UsageProvider } from "@/context/UsageContext";

import { EmotionRegistry } from "./EmotionRegistry";
import "./globals.css";

export const metadata: Metadata = {
  title: "Modulio",
  description: "Study consultant for FU Berlin computer science degree programs.",
  icons: {
    icon: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <EmotionRegistry>
          <SettingsProvider>
            <UsageProvider>
              <DegreeProvider>{children}</DegreeProvider>
            </UsageProvider>
          </SettingsProvider>
        </EmotionRegistry>
      </body>
    </html>
  );
}
