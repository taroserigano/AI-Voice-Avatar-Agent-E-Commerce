import { getAuthConfig } from "@/lib/api-server";
import { safeReturnTo } from "@/lib/return-to";
import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { SignUpForm } from "./sign-up-form";

export const metadata: Metadata = { title: "Create account" };

export default async function SignUpPage({
  searchParams,
}: {
  searchParams: Promise<{ returnTo?: string }>;
}) {
  const { returnTo } = await searchParams;
  const config = await getAuthConfig();
  // With OIDC, account creation happens at the identity provider.
  if (config.provider === "oidc") redirect("/sign-in");
  return <SignUpForm returnTo={safeReturnTo(returnTo)} minPasswordLength={config.min_password_length} />;
}
