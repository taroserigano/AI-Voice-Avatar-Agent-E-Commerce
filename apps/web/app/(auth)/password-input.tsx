"use client";

import { EyeIcon, EyeOffIcon, LockIcon } from "@/components/icons";
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
    <div className="group/pw relative">
      <LockIcon className="pointer-events-none absolute left-3.5 top-1/2 size-4.5 -translate-y-1/2 text-muted transition-colors group-focus-within/pw:text-brand-600" />
      <input
        id={id}
        name={name}
        type={visible ? "text" : "password"}
        autoComplete={autoComplete}
        required
        minLength={minLength}
        aria-invalid={invalid ? true : undefined}
        aria-describedby={describedBy}
        className={cn(inputClasses, "pl-11 pr-24")}
      />
      <button
        type="button"
        onClick={() => setVisible((v) => !v)}
        aria-pressed={visible}
        aria-controls={id}
        className="absolute inset-y-0 right-1 my-auto inline-flex h-11 min-w-20 items-center justify-center gap-1.5 rounded-lg px-2.5 text-sm font-semibold text-brand-700 transition-colors hover:bg-brand-50 hover:text-brand-800"
      >
        {visible ? <EyeOffIcon className="size-4" /> : <EyeIcon className="size-4" />}
        {visible ? "Hide" : "Show"}
        <span className="sr-only"> password</span>
      </button>
    </div>
  );
}
