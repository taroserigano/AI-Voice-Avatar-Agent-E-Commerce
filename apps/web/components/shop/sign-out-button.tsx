"use client";

import { browserApi } from "@/lib/api-browser";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

export function SignOutButton({ className }: { className?: string }) {
  const [pending, setPending] = useState(false);
  const client = useQueryClient();
  async function signOut() {
    setPending(true);
    await browserApi.POST("/v1/auth/sign-out");
    client.clear(); // drop cached private data from memory
    // replace() so Back doesn't return to a private page.
    window.location.replace("/sign-in");
  }
  return (
    <button type="button" onClick={signOut} disabled={pending} className={className}>
      {pending ? "Signing out…" : "Sign out"}
    </button>
  );
}
