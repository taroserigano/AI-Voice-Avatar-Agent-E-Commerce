import { getAuthConfig } from "@/lib/api-server";
import type { Metadata } from "next";
import { ResetPasswordForm } from "./reset-password-form";

export const metadata: Metadata = { title: "Choose a new password" };

export default async function ResetPasswordPage({
  searchParams,
}: {
  searchParams: Promise<{ token?: string }>;
}) {
  const { token } = await searchParams;
  const config = await getAuthConfig();
  return <ResetPasswordForm token={token ?? ""} minPasswordLength={config.min_password_length} />;
}
