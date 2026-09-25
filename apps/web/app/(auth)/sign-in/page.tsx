import { getAuthConfig } from "@/lib/api-server";
import { safeReturnTo } from "@/lib/return-to";
import type { Metadata } from "next";
import { SignInForm } from "./sign-in-form";

export const metadata: Metadata = { title: "Sign in" };

const ERRORS: Record<string, string> = {
  expired: "Your sign-in attempt expired. Please try again.",
  oidc: "We couldn't sign you in with your provider. Please try again.",
};

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<{ returnTo?: string; error?: string; reset?: string }>;
}) {
  const params = await searchParams;
  const config = await getAuthConfig();
  const returnTo = safeReturnTo(params.returnTo);
  return (
    <SignInForm
      returnTo={returnTo}
      provider={config.provider}
      initialError={params.error ? (ERRORS[params.error] ?? ERRORS.oidc) : undefined}
      passwordWasReset={params.reset === "1"}
    />
  );
}
