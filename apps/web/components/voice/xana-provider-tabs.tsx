"use client";

import { useRouter } from "next/navigation";
import { useRef } from "react";
import type { AvatarProvider } from "@/lib/voice-protocol";
import { cn } from "@/lib/cn";

const providers = ["tavus", "heygen"] as const;

export function XanaProviderTabs({ provider, disabled = false }: { provider: AvatarProvider; disabled?: boolean }) {
  const router = useRouter();
  const buttons = useRef<(HTMLButtonElement | null)[]>([]);
  return (
    <div role="tablist" aria-label="Xena avatar provider" className="mt-5 flex gap-1 rounded-2xl border border-white/15 bg-white/5 p-1">
      {providers.map((value, index) => (
        <button
          key={value}
          ref={(el) => { buttons.current[index] = el; }}
          id={`avatar-tab-${value}`}
          role="tab"
          type="button"
          disabled={disabled}
          aria-selected={provider === value}
          aria-controls="avatar-provider-panel"
          tabIndex={provider === value ? 0 : -1}
          onClick={() => router.push(`/support/voice/${value}`, { scroll: false })}
          onKeyDown={(e) => {
            const next = e.key === "Home" ? 0 : e.key === "End" ? 1
              : e.key === "ArrowRight" ? (index + 1) % 2
                : e.key === "ArrowLeft" ? (index + 1) % 2 : null;
            if (next !== null) { e.preventDefault(); buttons.current[next]?.focus(); }
          }}
          className={cn("min-w-28 rounded-xl px-5 py-2.5 font-semibold transition",
            provider === value ? "bg-brand-600 text-white shadow-sm" : "text-neutral-300 hover:bg-white/10")}
        >
          {value === "tavus" ? "Tavus" : "HeyGen"}
        </button>
      ))}
    </div>
  );
}
