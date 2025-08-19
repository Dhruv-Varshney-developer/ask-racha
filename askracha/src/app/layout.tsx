import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css"; // Your merged CSS file
import { ThemeProvider } from "@/components/theme-provider";
import ClarityAnalytics from "@/components/analytics/ClarityAnalytics";
import ClientClarityWrapper from "@/components/analytics/ClientClarityWrapper";

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
    <html lang="en" className={inter.className} suppressHydrationWarning>
      <body>
        {/* ThemeProvider from next-themes.
            - attribute="class" will add a class (e.g., "dark", "light", "storacha") to the <html> tag.
            - defaultTheme="dark" sets the initial theme.
            - enableSystem allows the system's preferred theme to be used initially.
            - themes prop is crucial: it lists all available themes, including your custom 'storacha' theme.
        */}
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          themes={["light", "dark", "storacha"]}
        >
          {children}
        </ThemeProvider>
        <ClarityAnalytics />
        <ClientClarityWrapper />
      </body>
    </html>
  );
}
