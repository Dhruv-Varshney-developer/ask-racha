import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AskRacha - AI Storacha Assistant",
  description:
    "Your intelligent AI-powered assistant for Storacha documentation",
  keywords: ["Storacha", "AI", "Assistant", "Documentation", "Gemini"],
  authors: [{ name: "AskRacha Team" }],
  viewport: "width=device-width, initial-scale=1",
  themeColor: "#1e293b",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} antialiased`}>{children}</body>
    </html>
  );
}
