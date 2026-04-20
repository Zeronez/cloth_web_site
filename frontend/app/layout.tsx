import type { Metadata } from "next";
import { AppProviders } from "../lib/providers";
import { SiteShell } from "../components/site-shell";
import "./globals.css";

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
      <body>
        <AppProviders>
          <SiteShell>{children}</SiteShell>
        </AppProviders>
      </body>
    </html>
  );
}
