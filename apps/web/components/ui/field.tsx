import { AlertCircleIcon } from "@/components/icons";
import { cn } from "@/lib/cn";
import type { ComponentProps, ReactNode } from "react";

/**
 * Shared control styling for <input>, <select>, <textarea>. 48px tall, white, 3:1 border,
 * violet focus border + soft halo, red border when aria-invalid="true".
 */
export const inputClasses =
  "block w-full min-h-12 rounded-lg border border-control bg-raised px-3.5 text-base text-ink shadow-xs " +
  "inset-shadow-well placeholder:text-subtle " +
  "transition-[border-color,box-shadow] duration-150 ease-snappy " +
  "hover:border-neutral-500 " +
  // Focus: 2px violet edge (border + inset ring) and a soft halo. The transparent outline keeps a
  // visible ring in Windows forced-colors mode.
  "focus-visible:border-brand-600 focus-visible:inset-ring-1 focus-visible:inset-ring-brand-600 " +
  "focus-visible:outline-2 focus-visible:outline-offset-0 focus-visible:outline-transparent " +
  "focus-visible:ring-4 focus-visible:ring-brand-500/20 " +
  "disabled:cursor-not-allowed disabled:bg-sunken disabled:text-muted " +
  "aria-[invalid=true]:border-danger-600 aria-[invalid=true]:focus-visible:inset-ring-danger-600 " +
  "aria-[invalid=true]:focus-visible:ring-danger-500/20";

/** Native <select> with a custom chevron. */
export const selectClasses = cn(inputClasses, "appearance-none pr-10 select-chevron");

/** Multi-line text. */
export const textareaClasses = cn(inputClasses, "min-h-28 py-3 leading-relaxed");

export function Input({ className, ...props }: ComponentProps<"input">) {
  return <input className={cn(inputClasses, className)} {...props} />;
}

export function Select({ className, ...props }: ComponentProps<"select">) {
  return <select className={cn(selectClasses, className)} {...props} />;
}

export function Textarea({ className, ...props }: ComponentProps<"textarea">) {
  return <textarea className={cn(textareaClasses, className)} {...props} />;
}

/**
 * Label + control + hint + error. The control is passed as children; wire it with
 * `id`, `aria-describedby={`${id}-hint ${id}-error`}` and `aria-invalid` as needed.
 */
export function Field({
  id,
  label,
  hint,
  error,
  optional,
  className,
  children,
}: {
  id: string;
  label: string;
  hint?: ReactNode;
  error?: string;
  /** Renders a quiet "(optional)" after the label. */
  optional?: boolean;
  className?: string;
  children: ReactNode;
}) {
  return (
    <div className={cn("space-y-2", className)}>
      <label htmlFor={id} className="block text-sm font-semibold text-ink">
        {label}
        {optional ? <span className="ml-1 font-normal text-muted">(optional)</span> : null}
      </label>
      {children}
      {hint ? (
        <p id={`${id}-hint`} className="text-sm text-muted">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={`${id}-error`} className="flex items-start gap-1.5 text-sm font-medium text-danger-700">
          <AlertCircleIcon className="mt-px size-4" />
          <span>{error}</span>
        </p>
      ) : null}
    </div>
  );
}
