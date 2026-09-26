"use client";

import { CheckIcon } from "@/components/icons";
import { cn } from "@/lib/cn";
import { useEffect, useState } from "react";

function CopyIcon({ className }: { className?: string }) {
  return (
    <svg
      aria-hidden="true"
      focusable="false"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={1.75}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={cn("size-4 shrink-0", className)}
    >
      <rect x="8.5" y="8.5" width="12" height="12" rx="2" />
      <path d="M15.5 8.5V5a1.5 1.5 0 0 0-1.5-1.5H5A1.5 1.5 0 0 0 3.5 5v9A1.5 1.5 0 0 0 5 15.5h3.5" />
    </svg>
  );
}

/** Copies a value (e.g. a tracking number) and confirms it in words, announced politely. */
export function CopyButton({ value, label }: { value: string; label: string }) {
  const [state, setState] = useState<"idle" | "copied" | "failed">("idle");

  useEffect(() => {
    if (state === "idle") return;
    const t = window.setTimeout(() => setState("idle"), 2200);
    return () => window.clearTimeout(t);
  }, [state]);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      setState("copied");
    } catch {
      setState("failed");
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={copy}
        className={cn(
          "relative inline-flex h-9 items-center gap-1.5 rounded-full px-3 text-sm font-semibold transition-colors duration-150 ease-snappy",
          "before:absolute before:inset-x-0 before:-inset-y-1 before:content-['']",
          state === "copied"
            ? "bg-success-50 text-success-800 ring-1 ring-inset ring-success-200"
            : "bg-raised text-ink ring-1 ring-inset ring-line-strong hover:bg-neutral-50 hover:ring-neutral-400",
        )}
      >
        {state === "copied" ? <CheckIcon className="size-4" strokeWidth={2.25} /> : <CopyIcon />}
        {state === "copied" ? "Copied" : "Copy"}
        <span className="sr-only"> {label}</span>
      </button>
      <span role="status" className="sr-only">
        {state === "copied" ? `${label} copied` : state === "failed" ? "Couldn't copy. Select the number to copy it." : ""}
      </span>
    </>
  );
}
