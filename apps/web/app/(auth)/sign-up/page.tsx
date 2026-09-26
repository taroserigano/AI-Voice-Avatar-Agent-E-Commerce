import { safeReturnTo } from "@/lib/return-to";
import type { Metadata } from "next";
import { SignUpForm } from "./sign-up-form";

export const metadata: Metadata = { title: "Create account" };

// Matches MIN_PASSWORD_LENGTH in services/commerce/src/commerce/auth/sessions.py.
const MIN_PASSWORD_LENGTH = 8;

export default async function SignUpPage({ searchParams }: { searchParams: Promise<{ returnTo?: string }> }) {
  const { returnTo } = await searchParams;
  return <SignUpForm returnTo={safeReturnTo(returnTo)} minPasswordLength={MIN_PASSWORD_LENGTH} />;
}
