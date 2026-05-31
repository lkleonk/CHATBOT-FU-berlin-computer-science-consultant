import type { Metadata } from "next";

import { SettingsProvider } from "@/context/SettingsContext";

import { EmotionRegistry } from "./EmotionRegistry";
import "./globals.css";

export const metadata: Metadata = {
  title: "FU Berlin CS Consultant",
  description: "Study consultant for the FU Berlin Master Informatik.",
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
          <SettingsProvider>{children}</SettingsProvider>
        </EmotionRegistry>
      </body>
    </html>
  );
}
