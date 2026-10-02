import { ArrowRightIcon, ChatIcon, HeadsetIcon, NotebookIcon } from "@/components/icons";
import { buttonClasses } from "@/components/ui/button";
import { cn } from "@/lib/cn";
import Link from "next/link";

/** "Need help with this order?": Xena already knows which order, plus the help topics. */
export function OrderHelpCard({ orderId, orderNumber }: { orderId: string; orderNumber: string }) {
  return (
    <aside aria-labelledby="order-help-heading" className="rounded-3xl border border-line bg-raised p-5 shadow-xs sm:p-6">
      <div className="flex items-start gap-3.5">
        <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-brand-50 text-brand-700">
          <HeadsetIcon className="size-5" />
        </span>
        <div className="min-w-0">
          <h2 id="order-help-heading" className="font-display text-lg font-semibold text-ink">
            Need help with this order?
          </h2>
          <p className="mt-1 text-sm text-muted">
            Xena, our support assistant, can check delivery, start a return, or hand you to a person.
          </p>
        </div>
      </div>
      <div className="mt-4 flex flex-col gap-2">
        <Link href={`/support?order=${orderId}`} className={cn(buttonClasses("secondary", "md"), "w-full")}>
          <ChatIcon className="size-4.5" />
          Ask Xena about this order
          <span className="sr-only"> (#{orderNumber})</span>
        </Link>
        <Link
          href="/help"
          className="group inline-flex min-h-11 items-center justify-center gap-1.5 rounded-full text-sm font-semibold text-brand-700 hover:text-brand-900"
        >
          <NotebookIcon className="size-4" />
          Browse help topics
          <ArrowRightIcon className="size-4 transition-transform duration-200 ease-snappy group-hover:translate-x-0.5" />
        </Link>
      </div>
    </aside>
  );
}
