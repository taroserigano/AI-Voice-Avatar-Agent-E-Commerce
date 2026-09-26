import { AlertCircleIcon, AlertTriangleIcon, CheckCircleIcon, InfoIcon, type Icon } from "@/components/icons";
import { cn } from "@/lib/cn";
import type { ReactNode } from "react";

type Tone = "info" | "warning" | "error" | "success";

const tones: Record<Tone, { box: string; icon: string; Icon: Icon }> = {
  info: { box: "border-brand-100 bg-brand-50 text-brand-900", icon: "text-brand-600", Icon: InfoIcon },
  warning: { box: "border-warning-200 bg-warning-50 text-warning-900", icon: "text-warning-600", Icon: AlertTriangleIcon },
  error: { box: "border-danger-200 bg-danger-50 text-danger-900", icon: "text-danger-600", Icon: AlertCircleIcon },
  success: { box: "border-success-200 bg-success-50 text-success-900", icon: "text-success-600", Icon: CheckCircleIcon },
};

/**
 * A tonal message box with an icon. Errors use role="alert"; everything else is a polite status.
 * Pass `role` only to override (e.g. `role="note"` for static guidance that shouldn't announce).
 */
export function Notice({
  tone = "info",
  title,
  children,
  className,
  id,
  action,
  role,
}: {
  tone?: Tone;
  title?: string;
  children?: ReactNode;
  className?: string;
  id?: string;
  /** Optional trailing control, e.g. a small ButtonLink. */
  action?: ReactNode;
  role?: "alert" | "status" | "note";
}) {
  const { box, icon, Icon } = tones[tone];
  return (
    <div
      id={id}
      role={role ?? (tone === "error" ? "alert" : "status")}
      className={cn("flex gap-3 rounded-xl border px-4 py-3.5 text-sm leading-relaxed", box, className)}
    >
      <Icon className={cn("mt-0.5 size-5", icon)} />
      <div className="min-w-0 flex-1">
        {title ? <p className="font-semibold">{title}</p> : null}
        {children ? <div className={title ? "mt-0.5" : undefined}>{children}</div> : null}
      </div>
      {action ? <div className="shrink-0 self-center">{action}</div> : null}
    </div>
  );
}
