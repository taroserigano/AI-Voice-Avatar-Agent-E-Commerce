"use client";

import { Button } from "@/components/ui/button";
import { Field } from "@/components/ui/field";
import { Notice } from "@/components/ui/notice";
import { browserApi, errorMessage } from "@/lib/api-browser";
import Link from "next/link";
import { useState } from "react";
import { PasswordInput } from "../password-input";

export function ResetPasswordForm({ token, minPasswordLength }: { token: string; minPasswordLength: number }) {
  const [error, setError] = useState<string>();
  const [pending, setPending] = useState(false);

  if (!token) {
    return (
      <div>
        <h1 className="text-2xl font-bold">Choose a new password</h1>
        <Notice tone="error" className="mt-4">
          This reset link is incomplete. <Link href="/forgot-password" className="underline">Request a new one</Link>.
        </Notice>
      </div>
    );
  }

  async function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const password = String(new FormData(event.currentTarget).get("password") ?? "");
    if (password.length < minPasswordLength) {
      setError(`Use at least ${minPasswordLength} characters.`);
      return;
    }
    setPending(true);
    setError(undefined);
    const { error: apiError, response } = await browserApi.POST("/v1/auth/reset-password", {
      body: { token, password },
    });
    if (response.status === 204) {
      // Full page load on purpose: auth state changed, so drop all client-side state.
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.assign("/sign-in?reset=1");
      return;
    }
    setPending(false);
    setError(errorMessage(apiError, "This reset link is invalid or has expired."));
  }

  return (
    <div>
      <h1 className="text-2xl font-bold">Choose a new password</h1>
      <p className="mt-1 text-muted">This signs you out everywhere else.</p>
      {error ? <Notice tone="error" className="mt-4">{error}</Notice> : null}
      <form method="post" onSubmit={onSubmit} className="mt-6 space-y-4" noValidate>
        <Field id="password" label="New password" hint={`At least ${minPasswordLength} characters.`}>
          <PasswordInput
            id="password"
            name="password"
            autoComplete="new-password"
            minLength={minPasswordLength}
            describedBy="password-hint"
          />
        </Field>
        <Button type="submit" size="lg" className="w-full" disabled={pending}>
          {pending ? "Saving…" : "Save new password"}
        </Button>
      </form>
    </div>
  );
}
