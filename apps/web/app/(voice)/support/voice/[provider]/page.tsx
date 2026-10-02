import { notFound } from "next/navigation";
import type { Metadata } from "next";

export const metadata: Metadata = { title: "Talk to Xana" };

export default async function ProviderPage({ params }: { params: Promise<{ provider: string }> }) {
  const { provider } = await params;
  if (provider !== "tavus" && provider !== "heygen") notFound();
  return null;
}
