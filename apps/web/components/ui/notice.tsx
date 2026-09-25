import { cn } from "@/lib/cn";
import type { ReactNode } from "react";

type Tone = "info" | "warning" | "error" | "success";

const tones: Record<Tone, string> = {
  info: "border-brand-100 bg-brand-50 text-brand-900",
  warning: "border-amber-300 bg-amber-50 text-amber-950",
  error: "border-red-300 bg-red-50 text-red-900",
  success: "border-emerald-300 bg-emerald-50 text-emerald-950",
};

/** A message box. Errors use role="alert"; everything else is a polite status. */
export function Notice({
  tone = "info",
  title,
  children,
  className,
  id,
}: {
  tone?: Tone;
  title?: string;
  children?: ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <div
      id={id}
      role={tone === "error" ? "alert" : "status"}
      className={cn("rounded-lg border px-4 py-3 text-sm", tones[tone], className)}
    >
      {title ? <p className="font-semibold">{title}</p> : null}
      {children ? <div className={title ? "mt-1" : undefined}>{children}</div> : null}
    </div>
  );
}
