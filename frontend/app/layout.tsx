import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { AppProviders } from "../lib/providers";
import { SiteShell } from "../components/site-shell";
import "./globals.css";

const inter = Inter({
  subsets: ["latin", "cyrillic"],
  display: "swap"
});

export const metadata: Metadata = {
  title: {
    default: "AnimeAttire",
    template: "%s | AnimeAttire"
  },
  description:
    "AnimeAttire - интернет-магазин аниме-стритвира и лимитированных коллекций одежды."
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru">
      <body className={inter.className}>
        <AppProviders>
          <SiteShell>{children}</SiteShell>
        </AppProviders>
      </body>
    </html>
  );
}
