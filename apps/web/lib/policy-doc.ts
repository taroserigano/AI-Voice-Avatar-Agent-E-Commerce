import { parse as parseYaml } from "yaml";

/**
 * Approved policy documents (content/policies/*.md) split into citable sections. Mirrors
 * services/commerce/src/commerce/policies/documents.py: with section_prefix "rr",
 * "## 7. How much you get back" is `rr-7` and "### 7.2 Splitting discounts" is `rr-7-2`.
 * The assistant cites these IDs and the policy page uses them as anchors.
 */

export type PolicySection = {
  id: string;
  number: string;
  title: string;
  level: 2 | 3;
  body: string;
};

export type PolicyDoc = {
  id: string;
  title: string;
  version: string;
  effectiveDate: string;
  status: string;
  summary: string[];
  rules: Record<string, unknown>;
  intro: string;
  sections: PolicySection[];
};

export type TocEntry = { id: string; number: string; title: string; children: TocEntry[] };

const FRONT_MATTER = /^---\r?\n([\s\S]*?)\r?\n---\r?\n/;
const HEADING = /^(#{2,3})\s+(\d+)(?:\.(\d+))?\.?\s+(.+?)\s*$/;

function asDateString(value: unknown): string {
  if (value instanceof Date) return value.toISOString().slice(0, 10);
  return String(value ?? "");
}

export function parsePolicy(text: string): PolicyDoc {
  const match = FRONT_MATTER.exec(text);
  if (!match) throw new Error("policy document has no front matter");
  const meta = (parseYaml(match[1] ?? "") ?? {}) as Record<string, unknown>;
  const prefix = typeof meta.section_prefix === "string" ? meta.section_prefix : null;
  const body = text.slice(match[0].length);

  const intro: string[] = [];
  const sections: PolicySection[] = [];
  let current: (PolicySection & { lines: string[] }) | null = null;
  const close = () => {
    if (current) {
      const { lines, ...rest } = current;
      sections.push({ ...rest, body: lines.join("\n").trim() });
    }
  };

  for (const line of body.split(/\r?\n/)) {
    const heading = prefix ? HEADING.exec(line) : null;
    if (heading) {
      close();
      const [, hashes = "##", major = "", minor, title = ""] = heading;
      current = {
        id: `${prefix}-${major}${minor ? `-${minor}` : ""}`,
        number: minor ? `${major}.${minor}` : major,
        title,
        level: hashes.length === 2 ? 2 : 3,
        body: "",
        lines: [],
      };
    } else if (current) {
      current.lines.push(line);
    } else {
      intro.push(line);
    }
  }
  close();

  return {
    id: String(meta.id),
    title: String(meta.title),
    version: String(meta.version),
    effectiveDate: asDateString(meta.effective_date),
    status: String(meta.status ?? ""),
    summary: Array.isArray(meta.summary) ? meta.summary.map(String) : [],
    rules: (meta.rules ?? {}) as Record<string, unknown>,
    intro: intro.join("\n").trim().replace(/^#\s+.*(\r?\n)+/, "").trim(),
    sections,
  };
}

/** Top-level sections with their subsections, for a table of contents. */
export function tableOfContents(doc: PolicyDoc): TocEntry[] {
  const toc: TocEntry[] = [];
  for (const s of doc.sections) {
    const entry = { id: s.id, number: s.number, title: s.title, children: [] };
    if (s.level === 2 || toc.length === 0) toc.push(entry);
    else toc[toc.length - 1]?.children.push(entry);
  }
  return toc;
}

/** "2026-09-26" -> "September 26, 2026" (no time zone shift). */
export function formatEffectiveDate(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  if (!y || !m || !d) return iso;
  return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "numeric",
    timeZone: "UTC",
  });
}
