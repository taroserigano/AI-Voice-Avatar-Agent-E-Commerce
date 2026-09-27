"use client";

import { ChatIcon } from "@/components/icons";
import { buttonClasses, type ButtonSize, type ButtonVariant } from "@/components/ui/button";
import type { ReactNode } from "react";

export const OPEN_STEPH_EVENT = "larkspur:open-steph";

/** Open the Steph panel from anywhere, optionally asking a question right away. */
export function openSteph(prompt?: string) {
  window.dispatchEvent(new CustomEvent(OPEN_STEPH_EVENT, { detail: { prompt } }));
}

/** A button that opens Steph (and optionally asks `prompt`). */
export function OpenStephButton({
  prompt,
  children = "Ask Steph",
  variant = "primary",
  size = "md",
  className,
  icon = true,
}: {
  prompt?: string;
  children?: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  className?: string;
  icon?: boolean;
}) {
  return (
    <button type="button" onClick={() => openSteph(prompt)} className={buttonClasses(variant, size, className)}>
      {icon ? <ChatIcon className="size-4.5" /> : null}
      {children}
    </button>
  );
}
