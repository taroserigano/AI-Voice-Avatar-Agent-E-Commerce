import { ArrowLeftIcon, SearchIcon } from "@/components/icons";
import { Logo } from "@/components/logo";
import { ButtonLink, buttonClasses } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="relative isolate flex min-h-screen flex-col overflow-hidden bg-canvas">
      <div aria-hidden="true" className="absolute inset-x-0 top-0 -z-10 h-[32rem] bg-mesh-light mask-[linear-gradient(to_bottom,black_40%,transparent)]" />

      <header className="px-4 py-4 sm:px-8">
        <Logo />
      </header>

      <main id="main" className="flex flex-1 flex-col items-center justify-center px-4 pb-24 pt-6 text-center">
        {/* Illustration: a lost plush otter on a big "404" */}
        <div aria-hidden="true" className="relative animate-fade-up">
          <p className="select-none font-display text-[9rem] font-semibold leading-none tracking-[-0.06em] text-brand-200 sm:text-[12rem]">
            404
          </p>
          {/* eslint-disable-next-line @next/next/no-img-element -- local SVG product art */}
          <img
            src="/images/products/pebble-pine-plush-otter.svg"
            alt=""
            width={640}
            height={640}
            className="absolute left-1/2 top-1/2 size-28 -translate-x-1/2 -translate-y-1/2 -rotate-6 rounded-3xl shadow-xl ring-4 ring-raised sm:size-36"
          />
          <span className="absolute right-[18%] top-[8%] grid size-10 place-items-center rounded-full bg-accent-400 font-display text-xl font-semibold text-ink shadow-md sm:size-12">
            ?
          </span>
        </div>

        <p className="mt-6 text-xs font-semibold uppercase tracking-eyebrow text-brand-700">Error 404</p>
        <h1 className="mt-3 max-w-lg font-display text-3xl font-semibold text-ink sm:text-4xl">
          We couldn&apos;t find that page.
        </h1>
        <p className="mt-3 max-w-md text-lg text-muted">It may have moved, or the link may be wrong.</p>

        <form role="search" action="/search" className="relative mt-8 w-full max-w-md">
          <label htmlFor="not-found-search" className="sr-only">
            Search products
          </label>
          <SearchIcon className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted" />
          <input
            id="not-found-search"
            name="q"
            type="search"
            placeholder="Search everything at Serigan Mart"
            className="h-13 w-full rounded-full border border-control bg-raised pl-11 pr-28 text-base text-ink shadow-sm placeholder:text-subtle transition focus-visible:border-brand-600 focus-visible:outline-transparent focus-visible:ring-4 focus-visible:ring-brand-500/20"
          />
          <button type="submit" className={buttonClasses("primary", "sm", "absolute right-2 top-1/2 -translate-y-1/2")}>
            Search
          </button>
        </form>

        <ButtonLink href="/" variant="ghost" className="mt-4 text-brand-700 hover:text-brand-800">
          <ArrowLeftIcon className="size-4.5" />
          Go to the home page
        </ButtonLink>
      </main>
    </div>
  );
}
