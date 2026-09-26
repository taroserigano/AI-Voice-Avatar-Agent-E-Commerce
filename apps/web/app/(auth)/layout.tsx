import { ChatIcon, LockIcon } from "@/components/icons";
import { Logo } from "@/components/logo";
import { isDevelopment } from "@/lib/api-server";
import { cn } from "@/lib/cn";
import Link from "next/link";

/** Product art for the brand collage (decorative: the tiles carry no information, so alt=""). */
const COLLAGE = [
  { src: "sonora-arc-wireless-headphones", tile: "left-[2%] top-[6%] w-[36%] -rotate-6", delay: "" },
  { src: "kettleworth-french-press", tile: "right-[4%] top-0 w-[30%] rotate-[5deg]", delay: "animation-delay-60" },
  { src: "stridewell-trail-runner-gtx", tile: "left-[33%] top-[30%] z-10 w-[36%] rotate-2", delay: "animation-delay-120" },
  { src: "summit-forge-2p-tent", tile: "left-[5%] bottom-0 w-[28%] rotate-[4deg]", delay: "animation-delay-180" },
  { src: "pebble-pine-plush-otter", tile: "right-0 bottom-[4%] w-[31%] -rotate-[5deg]", delay: "animation-delay-240" },
] as const;

const MOBILE_STRIP = [
  "sonora-arc-wireless-headphones",
  "kettleworth-french-press",
  "stridewell-trail-runner-gtx",
  "pebble-pine-plush-otter",
] as const;

function ProductTile({ src, className }: { src: string; className?: string }) {
  return (
    // eslint-disable-next-line @next/next/no-img-element -- local SVG product art
    <img
      src={`/images/products/${src}.svg`}
      alt=""
      width={640}
      height={640}
      className={cn("aspect-square rounded-3xl object-cover ring-1 ring-white/15 shadow-2xl", className)}
    />
  );
}

function DevAccounts() {
  const accounts = [
    ["alice@example.com", "alice-dev-password"],
    ["bob@example.com", "bob-dev-password"],
  ] as const;
  return (
    <div
      className="mt-6 rounded-2xl border border-dashed border-warning-200 bg-warning-50 px-4 py-3.5 text-sm text-warning-900"
      role="note"
      aria-label="Development sign-in"
    >
      <p className="flex items-center gap-2 font-semibold">
        <span className="rounded-full bg-warning-100 px-2 py-0.5 text-xs font-semibold uppercase tracking-eyebrow text-warning-900">
          Dev
        </span>
        Development sign-in
      </p>
      <p className="mt-1.5">Local test accounts only. Try:</p>
      <ul className="mt-2 space-y-1.5">
        {accounts.map(([email, password]) => (
          <li key={email} className="flex flex-wrap items-center gap-x-1.5 gap-y-1">
            <code className="rounded-md bg-raised/80 px-1.5 py-0.5 font-mono text-[0.8125rem] ring-1 ring-warning-200">
              {email}
            </code>
            <span aria-hidden="true">/</span>
            <span className="sr-only">password</span>
            <code className="rounded-md bg-raised/80 px-1.5 py-0.5 font-mono text-[0.8125rem] ring-1 ring-warning-200">
              {password}
            </code>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const legalLink =
    "inline-flex min-h-11 items-center rounded-md px-1 text-muted underline-offset-4 transition-colors hover:text-ink hover:underline";
  return (
    <div className="min-h-screen bg-canvas lg:grid lg:grid-cols-[minmax(0,1.08fr)_minmax(0,1fr)] lg:p-3">
      {/* ---------- Brand panel: compact band on phones, tall collage panel on desktop ---------- */}
      <aside
        aria-label="About Larkspur"
        className="relative isolate overflow-hidden bg-mesh-dark text-white focus-inverse lg:sticky lg:top-3 lg:h-[calc(100dvh-1.5rem)] lg:rounded-4xl"
      >
        {/* soft light bloom behind the collage */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -right-24 top-1/4 -z-10 hidden size-[34rem] rounded-full bg-brand-500/25 blur-3xl lg:block"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(rgb(255_255_255/0.07)_1px,transparent_1px)] [background-size:22px_22px] [mask-image:linear-gradient(to_bottom,black,transparent_75%)]"
        />

        <div className="flex h-full flex-col px-5 pb-14 pt-4 sm:px-8 lg:px-12 lg:pb-10 lg:pt-9 xl:px-16">
          <div className="flex items-center justify-between gap-4">
            <Logo inverted />
            {/* Phones: a small stack of product art beside the logo */}
            <div aria-hidden="true" className="flex -space-x-2 lg:hidden">
              {MOBILE_STRIP.map((src, i) => (
                <ProductTile
                  key={src}
                  src={src}
                  className={cn(
                    "size-10 rounded-xl shadow-lg ring-2 ring-brand-950 sm:size-12",
                    i === 0 && "hidden min-[360px]:block",
                  )}
                />
              ))}
            </div>
          </div>

          {/* Desktop collage */}
          <div className="relative hidden min-h-0 flex-1 items-center justify-center py-6 lg:flex" aria-hidden="true">
            {/* Sized by the height left over, so short laptop screens get a smaller collage. */}
            <div className="relative aspect-[4/3] h-full max-h-[22.5rem] max-w-full">
              {COLLAGE.map((item) => (
                <div key={item.src} className={cn("absolute animate-fade-up", item.tile, item.delay)}>
                  <ProductTile src={item.src} className="w-full" />
                </div>
              ))}
              {/* assistant chip: previews the text/voice helper (coming soon, per the copy below) */}
              <div className="absolute -bottom-3 left-[24%] z-20 flex animate-fade-up items-center gap-2.5 rounded-full border border-white/15 bg-brand-950/70 py-2 pl-2 pr-4 text-sm text-white whitespace-nowrap shadow-xl backdrop-blur-md animation-delay-400">
                <span className="grid size-7 place-items-center rounded-full bg-accent-400 text-ink">
                  <ChatIcon className="size-4" />
                </span>
                &ldquo;Start a return for my rain boots&rdquo;
              </div>
            </div>
          </div>

          <div className="mt-5 max-w-xl lg:mt-0">
            <p className="text-xs font-semibold uppercase tracking-eyebrow text-accent-300">Everyday essentials</p>
            <p className="mt-3 font-display text-[1.75rem] font-semibold leading-[1.1] tracking-[-0.03em] text-white sm:text-4xl lg:text-[clamp(2.25rem,3.2vw,3rem)]">
              Everyday essentials, and a helper that actually helps.
            </p>
            <p className="mt-4 hidden max-w-md text-base leading-relaxed text-brand-200 sm:block lg:text-lg">
              Shop headphones to hiking socks, with honest ratings from other shoppers. Returns and a shopping
              assistant you can type or talk to are coming soon. Sign in or create an account to start browsing.
            </p>
          </div>

          <p className="mt-10 hidden items-center gap-2 border-t border-white/10 pt-6 text-sm text-brand-300 lg:flex">
            <LockIcon className="size-4" />A portfolio demo store. Payments run in Stripe test mode; no real charges.
          </p>
        </div>

      </aside>

      {/* ---------- Form column ---------- */}
      <main id="main" className="relative flex flex-col items-center justify-center px-4 pb-10 sm:px-6 lg:px-10 lg:py-12">
        <div className="relative -mt-8 w-full max-w-[28rem] animate-fade-up lg:mt-0">
          <div className="rounded-3xl border border-line bg-raised p-6 shadow-xl sm:p-9 lg:shadow-lg">{children}</div>

          {isDevelopment() ? <DevAccounts /> : null}

          <nav aria-label="Legal" className="mt-6 flex flex-wrap items-center justify-center gap-x-3 text-sm">
            <Link className={legalLink} href="/privacy">
              Privacy
            </Link>
            <span aria-hidden="true" className="text-line-strong">
              ·
            </span>
            <Link className={legalLink} href="/terms">
              Terms
            </Link>
            <span aria-hidden="true" className="text-line-strong">
              ·
            </span>
            <Link className={legalLink} href="/accessibility">
              Accessibility
            </Link>
          </nav>
          <p className="mt-2 flex items-center justify-center gap-1.5 text-center text-xs text-muted lg:hidden">
            <LockIcon className="size-3.5" />
            Demo store · Stripe test mode, no real charges
          </p>
        </div>
      </main>
    </div>
  );
}
