import { getAuthConfig } from "@/lib/api-server";
import type { Metadata } from "next";
import { ForgotPasswordForm } from "./forgot-password-form";

export const metadata: Metadata = { title: "Forgot password" };

export default async function ForgotPasswordPage() {
  const config = await getAuthConfig();
  return <ForgotPasswordForm development={config.development_sign_in} />;
}
