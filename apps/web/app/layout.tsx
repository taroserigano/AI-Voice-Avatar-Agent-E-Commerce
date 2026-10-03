import type { Metadata, Viewport } from "next";
import { SessionGuard } from "@/components/session-guard";
import { Bricolage_Grotesque, Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";

// Self-hosted at build time by next/font (browsers never request Google).
// Inter = UI and body text; Bricolage Grotesque = display headings. Wired to
// --font-sans / --font-display in globals.css.
const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
  axes: ["opsz"],
});

const bricolage = Bricolage_Grotesque({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-bricolage",
  axes: ["opsz"],
});

export const metadata: Metadata = {
  title: { default: "Serigan Mart", template: "%s · Serigan Mart" },
  description: "Serigan Mart: everyday essentials, with a shopping assistant that helps by text or voice.",
  // Everything behind sign-in: tell crawlers not to index.
  robots: { index: false, follow: false },
};

export const viewport: Viewport = { width: "device-width", initialScale: 1, themeColor: "#6740de" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    // Browser extensions can add attributes to <html> before React loads; that one element's
    // mismatch is expected, not a bug in the page.
    <html lang="en" className={`${inter.variable} ${bricolage.variable}`} suppressHydrationWarning>
      <head>
        {/* The site has its own light and dark designs: Dark Reader leaves it alone instead of
            rewriting every icon's styles before React loads (a hydration error otherwise). */}
        <meta name="darkreader-lock" />
        {/* Back/forward re-check of the session on private pages; see the component. */}
        <SessionGuard />
      </head>
      <body className="min-h-screen bg-canvas font-sans text-ink antialiased">
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-full focus:bg-raised focus:px-5 focus:py-3 focus:font-semibold focus:text-brand-700 focus:shadow-lg"
        >
          Skip to main content
        </a>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
