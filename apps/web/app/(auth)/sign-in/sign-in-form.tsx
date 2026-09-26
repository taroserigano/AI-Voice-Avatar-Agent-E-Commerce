"use client";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { Notice } from "@/components/ui/notice";
import { browserApi, errorMessage } from "@/lib/api-browser";
import { safeReturnTo } from "@/lib/return-to";
import Link from "next/link";
import { useRef, useState } from "react";
import { PasswordInput } from "../password-input";

export function SignInForm({ returnTo }: { returnTo: string }) {
  const [error, setError] = useState<string>();
  const [pending, setPending] = useState(false);
  const errorRef = useRef<HTMLDivElement>(null);
  const withReturn = returnTo === "/" ? "" : `?returnTo=${encodeURIComponent(returnTo)}`;

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setPending(true);
    setError(undefined);
    const { error: apiError, response } = await browserApi.POST("/v1/auth/sign-in", {
      body: { email: String(form.get("email") ?? ""), password: String(form.get("password") ?? "") },
    });
    if (response.ok) {
      // Full navigation so the server renders the next page with the new session.
      window.location.assign(safeReturnTo(returnTo));
      return;
    }
    setPending(false);
    setError(
      response.status === 422
        ? "Enter a valid email address and your password."
        : errorMessage(apiError, "We couldn't sign you in. Please try again."),
    );
    requestAnimationFrame(() => errorRef.current?.focus());
  }

  return (
    <div>
      <h1 className="text-2xl font-bold">Sign in</h1>
      <p className="mt-1 text-muted">Welcome back. Sign in to shop, track orders, and get help.</p>

      <div ref={errorRef} tabIndex={-1} className="outline-none">
        {error ? <Notice tone="error" className="mt-4">{error}</Notice> : null}
      </div>

      <form method="post" onSubmit={onSubmit} className="mt-6 space-y-4" noValidate>
        <Field id="email" label="Email">
          <Input
            id="email"
            name="email"
            type="email"
            autoComplete="username"
            inputMode="email"
            required
            aria-invalid={error ? true : undefined}
          />
        </Field>
        <Field id="password" label="Password">
          <PasswordInput id="password" name="password" autoComplete="current-password" invalid={!!error} />
        </Field>
        <Button type="submit" size="lg" className="w-full" disabled={pending} aria-disabled={pending}>
          {pending ? "Signing in…" : "Sign in"}
        </Button>
      </form>

      <p className="mt-6 text-center text-sm text-muted">
        New to Larkspur?{" "}
        <Link
          href={`/sign-up${withReturn}`}
          className="font-semibold text-brand-700 underline underline-offset-2 hover:text-brand-900"
        >
          Create an account
        </Link>
      </p>
    </div>
  );
}
