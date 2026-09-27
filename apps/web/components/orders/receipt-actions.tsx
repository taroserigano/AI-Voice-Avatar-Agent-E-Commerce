"use client";

import { Button } from "@/components/ui/button";
import { PrinterIcon } from "./order-icons";

/** Opens the browser's print dialog (save as PDF lives there too). */
export function PrintButton() {
  return (
    <Button variant="primary" size="sm" onClick={() => window.print()}>
      <PrinterIcon className="size-4" />
      Print or save as PDF
    </Button>
  );
}
