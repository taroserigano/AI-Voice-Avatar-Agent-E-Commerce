/**
 * Icons the order and store pages need that the shared set doesn't have yet. Same grid and stroke
 * as components/icons.tsx: 24px, 1.75px round strokes, currentColor, decorative.
 */
import { cn } from "@/lib/cn";
import type { ReactNode } from "react";

function icon(content: ReactNode) {
  function OrderIcon({ className }: { className?: string }) {
    return (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        width={24}
        height={24}
        fill="none"
        stroke="currentColor"
        strokeWidth={1.75}
        strokeLinecap="round"
        strokeLinejoin="round"
        focusable="false"
        aria-hidden="true"
        className={cn("size-5 shrink-0", className)}
      >
        {content}
      </svg>
    );
  }
  return OrderIcon;
}

export const PrinterIcon = icon(
  <>
    <path d="M7 8V3.5h10V8" />
    <rect x="3.5" y="8" width="17" height="8.5" rx="2" />
    <path d="M7 14h10v6.5H7Z" />
    <path d="M17 11h.01" />
  </>,
);

export const LocateIcon = icon(
  <>
    <circle cx="12" cy="12" r="6.5" />
    <circle cx="12" cy="12" r="2" />
    <path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3" />
  </>,
);

export const PhoneIcon = icon(
  <path d="M8.2 3.5H5.6a1.6 1.6 0 0 0-1.6 1.8 16.5 16.5 0 0 0 14.7 14.7 1.6 1.6 0 0 0 1.8-1.6v-2.6a1.5 1.5 0 0 0-1.1-1.4l-2.9-.8a1.5 1.5 0 0 0-1.5.4l-1.1 1.1a12 12 0 0 1-5.2-5.2L9.8 8.8a1.5 1.5 0 0 0 .4-1.5l-.8-2.9a1.5 1.5 0 0 0-1.2-.9Z" />,
);
