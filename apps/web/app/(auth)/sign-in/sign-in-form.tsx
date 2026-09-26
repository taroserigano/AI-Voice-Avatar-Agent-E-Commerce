"use client";

import { ArrowRightIcon, MailIcon } from "@/components/icons";
import { Button, ButtonLink } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { Notice } from "@/components/ui/notice";
import { browserApi, errorMessage } from "@/lib/api-browser";
import { safeReturnTo } from "@/lib/return-to";
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
      <p className="text-xs font-semibold uppercase tracking-eyebrow text-brand-700">Welcome back</p>
      <h1 className="mt-2 font-display text-3xl font-semibold text-ink">Sign in</h1>
      <p className="mt-2 text-muted">Sign in to shop, track orders, and get help.</p>

      <div ref={errorRef} tabIndex={-1} className="outline-none">
        {error ? (
          <Notice tone="error" className="mt-5 animate-fade-in">
            {error}
          </Notice>
        ) : null}
      </div>

      <form method="post" onSubmit={onSubmit} className="mt-7 space-y-5" noValidate>
        <Field id="email" label="Email">
          <div className="group/email relative">
            <MailIcon className="pointer-events-none absolute left-3.5 top-1/2 size-4.5 -translate-y-1/2 text-muted transition-colors group-focus-within/email:text-brand-600" />
            <Input
              id="email"
              name="email"
              type="email"
              autoComplete="username"
              inputMode="email"
              required
              placeholder="you@example.com"
              className="pl-11"
              aria-invalid={error ? true : undefined}
            />
          </div>
        </Field>
        <Field id="password" label="Password">
          <PasswordInput id="password" name="password" autoComplete="current-password" invalid={!!error} />
        </Field>
        <Button
          type="submit"
          size="lg"
          className="mt-2 w-full"
          loading={pending}
          disabled={pending}
          aria-disabled={pending}
        >
          {pending ? "Signing in…" : "Sign in"}
          {pending ? null : <ArrowRightIcon className="size-4.5" />}
        </Button>
      </form>

      <div className="mt-8 flex items-center gap-3 text-sm text-muted">
        <span aria-hidden="true" className="h-px flex-1 bg-line" />
        <span>New to Serigan Mart?</span>
        <span aria-hidden="true" className="h-px flex-1 bg-line" />
      </div>
      <ButtonLink href={`/sign-up${withReturn}`} variant="outline" size="lg" className="mt-4 w-full">
        Create an account
      </ButtonLink>
    </div>
  );
}
