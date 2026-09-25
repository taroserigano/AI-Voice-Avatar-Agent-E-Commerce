"use client";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { Notice } from "@/components/ui/notice";
import { browserApi, errorMessage } from "@/lib/api-browser";
import { safeReturnTo } from "@/lib/return-to";
import Link from "next/link";
import { useRef, useState } from "react";
import { PasswordInput } from "../password-input";

export function SignUpForm({ returnTo, minPasswordLength }: { returnTo: string; minPasswordLength: number }) {
  const [error, setError] = useState<string>();
  const [pending, setPending] = useState(false);
  const errorRef = useRef<HTMLDivElement>(null);
  const withReturn = returnTo === "/" ? "" : `?returnTo=${encodeURIComponent(returnTo)}`;

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const password = String(form.get("password") ?? "");
    if (password.length < minPasswordLength) {
      setError(`Use at least ${minPasswordLength} characters for your password.`);
      requestAnimationFrame(() => errorRef.current?.focus());
      return;
    }
    setPending(true);
    setError(undefined);
    const { error: apiError, response } = await browserApi.POST("/v1/auth/sign-up", {
      body: {
        display_name: String(form.get("display_name") ?? ""),
        email: String(form.get("email") ?? ""),
        password,
      },
    });
    if (response.ok) {
      window.location.assign(safeReturnTo(returnTo));
      return;
    }
    setPending(false);
    setError(errorMessage(apiError, "We couldn't create your account. Please try again."));
    requestAnimationFrame(() => errorRef.current?.focus());
  }

  return (
    <div>
      <h1 className="text-2xl font-bold">Create your account</h1>
      <p className="mt-1 text-muted">It takes one short form.</p>
      <div ref={errorRef} tabIndex={-1} className="outline-none">
        {error ? <Notice tone="error" className="mt-4">{error}</Notice> : null}
      </div>
      <form method="post" onSubmit={onSubmit} className="mt-6 space-y-4" noValidate>
        <Field id="display_name" label="Your name">
          <Input id="display_name" name="display_name" autoComplete="name" required maxLength={120} />
        </Field>
        <Field id="email" label="Email">
          <Input id="email" name="email" type="email" autoComplete="email" inputMode="email" required />
        </Field>
        <Field id="password" label="Password" hint={`At least ${minPasswordLength} characters.`}>
          <PasswordInput
            id="password"
            name="password"
            autoComplete="new-password"
            minLength={minPasswordLength}
            describedBy="password-hint"
          />
        </Field>
        <Button type="submit" size="lg" className="w-full" disabled={pending}>
          {pending ? "Creating account…" : "Create account"}
        </Button>
      </form>
      <p className="mt-6 text-center text-sm text-muted">
        Already have an account?{" "}
        <Link
          href={`/sign-in${withReturn}`}
          className="font-semibold text-brand-700 underline underline-offset-2 hover:text-brand-900"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}
