"use client";

import { AlertCircleIcon, StarFilledIcon, StarIcon } from "@/components/icons";
import { cn } from "@/lib/cn";
import { pluralize, ratingWord } from "@/lib/reviews-query";
import { useState, type Ref } from "react";

/**
 * Required 1–5 star input. A native radio group inside a fieldset, so Tab enters the group and
 * the arrow keys move and select (no custom key handling). Hovering previews a value; the caption
 * always says the value in words so color and fill are never the only signal.
 */
export function StarPicker({
  name,
  value,
  onChange,
  error,
  firstInputRef,
  disabled,
}: {
  name: string;
  value: number | null;
  onChange: (stars: number) => void;
  error?: string;
  /** Receives the radio that should take focus (the checked one, or 1 star). */
  firstInputRef?: Ref<HTMLInputElement>;
  disabled?: boolean;
}) {
  const [hover, setHover] = useState<number | null>(null);
  const shown = hover ?? value ?? 0;
  const errorId = `${name}-error`;
  const focusTarget = value ?? 1;

  return (
    <fieldset disabled={disabled}>
      <legend className="text-sm font-semibold text-ink">
        Your rating <span className="font-normal text-muted">(required)</span>
      </legend>
      <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2">
        <div className="-ml-1.5 flex" onMouseLeave={() => setHover(null)}>
          {[1, 2, 3, 4, 5].map((stars) => {
            const filled = stars <= shown;
            return (
              <label
                key={stars}
                onMouseEnter={() => setHover(stars)}
                className={cn(
                  "group/star grid size-11 cursor-pointer place-items-center rounded-lg transition-colors duration-150",
                  "hover:bg-accent-50 has-focus-visible:outline-2 has-focus-visible:outline-offset-0 has-focus-visible:outline-focus",
                  "has-disabled:cursor-not-allowed",
                )}
              >
                <input
                  ref={stars === focusTarget ? firstInputRef : undefined}
                  type="radio"
                  name={name}
                  value={stars}
                  checked={value === stars}
                  onChange={() => onChange(stars)}
                  aria-describedby={error ? errorId : undefined}
                  className="sr-only"
                />
                <span className="sr-only">
                  {pluralize(stars, "star")}, {ratingWord(stars)}
                </span>
                {filled ? (
                  <StarFilledIcon
                    className={cn(
                      "size-8 text-star transition-transform duration-200 ease-spring",
                      hover != null && "scale-110 motion-reduce:scale-100",
                    )}
                  />
                ) : (
                  <StarIcon
                    className={cn(
                      "size-8 transition-colors duration-150",
                      error ? "text-danger-600" : "text-control group-hover/star:text-accent-600",
                    )}
                  />
                )}
              </label>
            );
          })}
        </div>
        {/* Visual echo of the hovered/chosen value; the radios already carry their names. */}
        <p className="min-w-28 text-sm font-medium text-ink-soft" aria-hidden="true">
          {shown > 0 ? (
            <>
              <span className="tabular-nums text-ink">{shown}</span>
              <span className="text-muted"> / 5 · </span>
              {ratingWord(shown)}
            </>
          ) : (
            <span className="text-muted">Select 1 to 5 stars</span>
          )}
        </p>
      </div>
      {error ? (
        <p id={errorId} className="mt-2 flex items-start gap-1.5 text-sm font-medium text-danger-700">
          <AlertCircleIcon className="mt-px size-4" />
          <span>{error}</span>
        </p>
      ) : null}
    </fieldset>
  );
}
