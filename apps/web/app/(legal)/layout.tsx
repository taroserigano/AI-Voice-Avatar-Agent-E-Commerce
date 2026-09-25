import { Logo } from "@/components/logo";
import Link from "next/link";

export default function LegalLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <header className="border-b border-line bg-white">
        <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4">
          <Logo />
          <Link href="/sign-in" className="text-sm font-semibold text-brand-700 underline underline-offset-2">
            Sign in
          </Link>
        </div>
      </header>
      <main id="main" className="mx-auto max-w-3xl px-4 py-10">
        <article className="space-y-4 leading-relaxed [&_h1]:text-3xl [&_h1]:font-bold [&_h2]:mt-8 [&_h2]:text-xl [&_h2]:font-semibold">
          {children}
        </article>
      </main>
    </div>
  );
}
