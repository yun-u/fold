import "./globals.css";
import type { Metadata } from "next";
import { Inter } from "next/font/google";

import { QueryClientProvider } from "@/components/query-provider";
import { SearchProvider } from "@/components/search-provider";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/toaster";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Fold",
  description: "Manage linked documents and utilize vector search.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <QueryClientProvider>
          <SearchProvider>
            <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
              {children}
            </ThemeProvider>
          </SearchProvider>
        </QueryClientProvider>
        <Toaster />
      </body>
    </html>
  );
}
