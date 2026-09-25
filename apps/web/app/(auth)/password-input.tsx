"use client";

import { inputClasses } from "@/components/ui/field";
import { cn } from "@/lib/cn";
import { useState } from "react";

/**
 * Password field that password managers can fill and people can paste into (WCAG 2.2
 * 3.3.8 Accessible Authentication), with a show/hide toggle.
 */
export function PasswordInput({
  id,
  name,
  autoComplete,
  invalid,
  describedBy,
  minLength,
}: {
  id: string;
  name: string;
  autoComplete: "current-password" | "new-password";
  invalid?: boolean;
  describedBy?: string;
  minLength?: number;
}) {
  const [visible, setVisible] = useState(false);
  return (
    <div className="relative">
      <input
        id={id}
        name={name}
        type={visible ? "text" : "password"}
        autoComplete={autoComplete}
        required
        minLength={minLength}
        aria-invalid={invalid ? true : undefined}
        aria-describedby={describedBy}
        className={cn(inputClasses, "pr-20")}
      />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        aria-pressed={visible}
        aria-controls={id}
        className="absolute inset-y-0 right-1 my-1 min-w-16 rounded-md px-2 text-sm font-semibold text-brand-700 hover:bg-brand-50"
      >
        {visible ? "Hide" : "Show"}
        <span className="sr-only"> password</span>
      </button>
    </div>
  );
}
