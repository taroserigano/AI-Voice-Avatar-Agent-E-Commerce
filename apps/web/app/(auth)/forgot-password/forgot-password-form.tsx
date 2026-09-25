"use client";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { Notice } from "@/components/ui/notice";
import { browserApi } from "@/lib/api-browser";
import Link from "next/link";
import { useState } from "react";

export function ForgotPasswordForm({ development }: { development: boolean }) {
  const [sent, setSent] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string>();

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const email = String(new FormData(event.currentTarget).get("email") ?? "");
    setPending(true);
    setError(undefined);
    const { response } = await browserApi.POST("/v1/auth/forgot-password", { body: { email } });
    setPending(false);
    if (response.status === 202) setSent(true);
    else if (response.status === 422) setError("Enter a valid email address.");
    else setError("Something went wrong. Please try again.");
  }

  return (
    <div>
      <h1 className="text-2xl font-bold">Reset your password</h1>
      {sent ? (
        <Notice tone="success" className="mt-4" title="Check your email">
          If an account exists for that email, we&apos;ve sent a link to reset the password. The
          link works for 30 minutes.
          {development ? (
            <p className="mt-2">
              <strong>Development:</strong> no email is sent. The reset link is in the commerce API
              server log.
            </p>
          ) : null}
        </Notice>
      ) : (
        <>
          <p className="mt-1 text-muted">Enter your account email and we&apos;ll send a reset link.</p>
          {error ? <Notice tone="error" className="mt-4">{error}</Notice> : null}
          <form method="post" onSubmit={onSubmit} className="mt-6 space-y-4" noValidate>
            <Field id="email" label="Email">
              <Input id="email" name="email" type="email" autoComplete="email" inputMode="email" required />
            </Field>
            <Button type="submit" size="lg" className="w-full" disabled={pending}>
              {pending ? "Sending…" : "Send reset link"}
            </Button>
          </form>
        </>
      )}
      <p className="mt-6 text-center text-sm">
        <Link href="/sign-in" className="font-semibold text-brand-700 underline underline-offset-2">
          Back to sign in
        </Link>
      </p>
    </div>
  );
}
