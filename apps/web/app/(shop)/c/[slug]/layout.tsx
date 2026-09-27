import type { ReactNode } from "react";
import { loadDepartment } from "./load-department";

/**
 * Checks the department exists before anything streams. This layout sits above this segment's
 * loading.tsx, so an unknown slug answers a real HTTP 404 instead of a 200 with the not-found UI
 * streamed in later.
 */
export default async function DepartmentLayout({ params, children }: { params: Promise<{ slug: string }>; children: ReactNode }) {
  await loadDepartment((await params).slug);
  return children;
}
