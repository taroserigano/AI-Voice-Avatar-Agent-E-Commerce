"use client";

import { AlertTriangleIcon, HomeIcon, RefreshIcon } from "@/components/icons";
import { Button, ButtonLink } from "@/components/ui/button";
import { useEffect, useRef } from "react";

export default function ShopError({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => heading.current?.focus(), []);
  return (
    <div className="flex justify-center py-10 sm:py-16">
      <div
        role="alert"
        className="relative w-full max-w-xl overflow-hidden rounded-3xl border border-line bg-raised px-6 py-12 text-center shadow-lg animate-fade-up sm:px-12"
      >
        <div aria-hidden="true" className="absolute inset-x-0 top-0 h-40 bg-mesh-light mask-[linear-gradient(to_bottom,black,transparent)]" />
        <div className="relative">
          <span className="mx-auto grid size-16 place-items-center rounded-2xl bg-raised text-warning-600 shadow-md ring-1 ring-warning-200">
            <AlertTriangleIcon className="size-8" />
          </span>
          <h1
            ref={heading}
            tabIndex={-1}
            className="mt-6 font-display text-2xl font-semibold text-ink outline-none sm:text-3xl"
          >
            Something went wrong on our side.
          </h1>
          <p className="mx-auto mt-3 max-w-sm text-muted">Your cart is saved. Try again in a moment.</p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Button size="lg" onClick={reset}>
              <RefreshIcon className="size-4.5" />
              Try again
            </Button>
            <ButtonLink href="/" variant="outline" size="lg">
              <HomeIcon className="size-4.5" />
              Go to the home page
            </ButtonLink>
          </div>
          {error.digest ? (
            <p className="mt-8 text-xs text-muted">
              Reference: <code className="rounded bg-sunken px-1.5 py-0.5 font-mono">{error.digest}</code>
            </p>
          ) : null}
        </div>
      </div>
    </div>
  );
}
