"use client";

import { ArrowRightIcon, MailIcon, UserIcon } from "@/components/icons";
import { Button, ButtonLink } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { Notice } from "@/components/ui/notice";
import { browserApi, errorMessage } from "@/lib/api-browser";
import { safeReturnTo } from "@/lib/return-to";
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
      <p className="text-xs font-semibold uppercase tracking-eyebrow text-brand-700">Join Serigan Mart</p>
      <h1 className="mt-2 font-display text-3xl font-semibold text-ink">Create your account</h1>
      <p className="mt-2 text-muted">It takes one short form.</p>
      <div ref={errorRef} tabIndex={-1} className="outline-none">
        {error ? (
          <Notice tone="error" className="mt-5 animate-fade-in">
            {error}
          </Notice>
        ) : null}
      </div>
      <form method="post" onSubmit={onSubmit} className="mt-7 space-y-5" noValidate>
        <Field id="display_name" label="Your name">
          <div className="group/name relative">
            <UserIcon className="pointer-events-none absolute left-3.5 top-1/2 size-4.5 -translate-y-1/2 text-muted transition-colors group-focus-within/name:text-brand-600" />
            <Input
              id="display_name"
              name="display_name"
              autoComplete="name"
              required
              maxLength={120}
              className="pl-11"
            />
          </div>
        </Field>
        <Field id="email" label="Email">
          <div className="group/email relative">
            <MailIcon className="pointer-events-none absolute left-3.5 top-1/2 size-4.5 -translate-y-1/2 text-muted transition-colors group-focus-within/email:text-brand-600" />
            <Input
              id="email"
              name="email"
              type="email"
              autoComplete="email"
              inputMode="email"
              required
              placeholder="you@example.com"
              className="pl-11"
            />
          </div>
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
        <Button type="submit" size="lg" className="mt-2 w-full" loading={pending} disabled={pending}>
          {pending ? "Creating account…" : "Create account"}
          {pending ? null : <ArrowRightIcon className="size-4.5" />}
        </Button>
      </form>
      <div className="mt-8 flex items-center gap-3 text-sm text-muted">
        <span aria-hidden="true" className="h-px flex-1 bg-line" />
        <span>Already have an account?</span>
        <span aria-hidden="true" className="h-px flex-1 bg-line" />
      </div>
      <ButtonLink href={`/sign-in${withReturn}`} variant="outline" size="lg" className="mt-4 w-full">
        Sign in
      </ButtonLink>
    </div>
  );
}
