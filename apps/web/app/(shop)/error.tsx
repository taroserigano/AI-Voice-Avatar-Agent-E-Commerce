"use client";

import { Button } from "@/components/ui/button";
import { useEffect, useRef } from "react";

export default function ShopError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => heading.current?.focus(), []);
  return (
    <div role="alert" className="mx-auto max-w-lg rounded-2xl border border-red-200 bg-white p-8 text-center">
      <h1 ref={heading} tabIndex={-1} className="text-xl font-bold outline-none">
        Something went wrong on our side.
      </h1>
      <p className="mt-2 text-muted">Your cart is saved. Try again in a moment.</p>
      <Button className="mt-5" onClick={reset}>
        Try again
      </Button>
    </div>
  );
}
