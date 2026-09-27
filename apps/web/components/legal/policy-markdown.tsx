import Link from "next/link";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

const linkClass =
  "font-medium text-brand-700 underline decoration-brand-300 underline-offset-4 hover:decoration-brand-700";

/** The slice of a Markdown syntax-tree node the table label needs. */
type TreeNode = { type: string; tagName?: string; value?: string; children?: TreeNode[] };

function textOf(node: TreeNode): string {
  return node.type === "text" ? (node.value ?? "") : (node.children ?? []).map(textOf).join("");
}

/** A table's header-cell text, in order: ["Item", "Refunded"]. */
function columnHeadings(node: TreeNode | undefined): string[] {
  if (!node) return [];
  if (node.tagName === "th") return [textOf(node).trim()];
  return (node.children ?? []).flatMap(columnHeadings).filter(Boolean);
}

// Policy text is our own approved content; react-markdown renders no raw HTML regardless.
const components: Components = {
  p: ({ children }) => <p className="leading-relaxed">{children}</p>,
  ul: ({ children }) => <ul className="list-disc space-y-1.5 pl-6 marker:text-brand-400">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal space-y-1.5 pl-6 marker:text-muted">{children}</ol>,
  strong: ({ children }) => <strong className="font-semibold text-ink">{children}</strong>,
  a: ({ href = "", children }) =>
    href.startsWith("/") || href.startsWith("#") ? (
      <Link href={href} className={linkClass}>
        {children}
      </Link>
    ) : (
      <a href={href} className={linkClass} rel="noreferrer">
        {children}
      </a>
    ),
  blockquote: ({ children }) => (
    <blockquote className="rounded-2xl border border-brand-100 bg-brand-50 p-5 text-brand-900 [&_p]:leading-relaxed">
      {children}
    </blockquote>
  ),
  // Wide tables scroll sideways on phones. The wrapper is a named, focusable region so keyboard
  // users can scroll it too (WCAG 2.1.1); it's named after the table's column headings.
  table: ({ node, children }) => (
    <div
      role="region"
      aria-label={`Table: ${columnHeadings(node).join(", ")}`}
      tabIndex={0}
      className="overflow-x-auto rounded-2xl bg-raised shadow-xs ring-1 ring-inset ring-line focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
    >
      <table className="w-full min-w-[32rem] border-collapse text-left text-sm">{children}</table>
    </div>
  ),
  thead: ({ children }) => <thead className="bg-canvas">{children}</thead>,
  th: ({ children }) => (
    <th scope="col" className="border-b border-line-strong px-4 py-2.5 font-semibold text-ink">
      {children}
    </th>
  ),
  td: ({ children }) => <td className="border-b border-line px-4 py-2.5 align-top text-ink-soft">{children}</td>,
  code: ({ children }) => <code className="rounded bg-canvas px-1 py-0.5 font-mono text-[0.85em]">{children}</code>,
};

export function PolicyMarkdown({ children }: { children: string }) {
  return (
    <div className="space-y-3 text-[1.0625rem] text-ink-soft">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {children}
      </ReactMarkdown>
    </div>
  );
}
