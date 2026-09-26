import { AlertTriangleIcon, CheckIcon } from "@/components/icons";
import { cn } from "@/lib/cn";
import { formatDay } from "@/lib/orders";

export type StepperStep = { key: string; label: string; date?: string | null };

/**
 * Horizontal progress stepper. An ordered list: every step says in words whether it's done,
 * current (`aria-current="step"`), or still to come, so state never relies on color.
 * When the last step is current, the whole track reads as complete (success tone).
 */
export function Stepper({
  steps,
  current,
  label,
  issue = false,
  size = "md",
  className,
}: {
  steps: StepperStep[];
  current: number;
  /** Accessible name for the list, e.g. "Delivery progress". */
  label: string;
  /** The current step has a problem (delivery exception). */
  issue?: boolean;
  size?: "sm" | "md";
  className?: string;
}) {
  const complete = current >= steps.length - 1 && !issue;
  const doneFill = complete ? "bg-success-600" : "bg-brand-600";
  const dot = size === "sm" ? "size-7" : "size-8";
  const lineTop = size === "sm" ? "top-3.5" : "top-4";

  return (
    <ol aria-label={label} className={cn("grid", className)} style={{ gridTemplateColumns: `repeat(${steps.length}, minmax(0, 1fr))` }}>
      {steps.map((step, i) => {
        const done = i < current || (i === current && complete);
        const isCurrent = i === current;
        const state = isCurrent ? (issue ? "needs attention" : complete ? "completed" : "current step") : done ? "completed" : "not yet";
        return (
          <li
            key={step.key}
            aria-current={isCurrent ? "step" : undefined}
            className="relative flex flex-col items-center px-1 text-center"
          >
            {i > 0 ? (
              <span
                aria-hidden="true"
                className={cn(
                  "absolute right-1/2 h-0.5 w-full -translate-y-1/2 rounded-full",
                  lineTop,
                  i <= current ? doneFill : "bg-line-strong",
                )}
              />
            ) : null}
            <span
              aria-hidden="true"
              className={cn(
                "relative z-10 grid shrink-0 place-items-center rounded-full transition-colors",
                dot,
                done && cn(doneFill, "text-white shadow-xs"),
                isCurrent && !done && !issue && "bg-raised ring-2 ring-brand-600 ring-offset-0",
                isCurrent && issue && "bg-warning-50 text-warning-700 ring-2 ring-warning-600",
                !done && !isCurrent && "bg-raised ring-2 ring-line-strong",
              )}
            >
              {done ? (
                <CheckIcon className={size === "sm" ? "size-3.5" : "size-4"} strokeWidth={2.5} />
              ) : isCurrent && issue ? (
                <AlertTriangleIcon className="size-4" />
              ) : isCurrent ? (
                <>
                  <span className="absolute inset-0 animate-ping rounded-full bg-brand-400/30 [animation-duration:2s]" />
                  <span className="size-2.5 rounded-full bg-brand-600" />
                </>
              ) : null}
            </span>
            <span
              className={cn(
                "mt-2.5 leading-tight sm:text-sm", size === "sm" ? "text-[0.6875rem] min-[420px]:text-xs" : "text-xs",
                isCurrent || done ? "font-semibold text-ink" : "font-medium text-muted",
              )}
            >
              {step.label}
              <span className="sr-only">, {state}</span>
            </span>
            {step.date ? (
              <time dateTime={step.date} className="mt-0.5 text-xs tabular-nums text-muted">
                {formatDay(step.date)}
              </time>
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}
