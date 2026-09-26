// Hand-drawn illustrations for the "How returns work" page. They are decorative: every
// picture sits next to text that says the same thing, so each one is hidden from screen readers.
// Colors come from the design tokens in globals.css (emitted as CSS variables), never raw hex.
import { cn } from "@/lib/cn";
import type { ReactNode } from "react";

const c = {
  brand50: "var(--color-brand-50)",
  brand100: "var(--color-brand-100)",
  brand200: "var(--color-brand-200)",
  brand300: "var(--color-brand-300)",
  brand500: "var(--color-brand-500)",
  brand600: "var(--color-brand-600)",
  brand700: "var(--color-brand-700)",
  brand900: "var(--color-brand-900)",
  accent100: "var(--color-accent-100)",
  accent200: "var(--color-accent-200)",
  accent300: "var(--color-accent-300)",
  accent400: "var(--color-accent-400)",
  accent600: "var(--color-accent-600)",
  accent700: "var(--color-accent-700)",
  ink: "var(--color-ink)",
  line: "var(--color-line)",
  lineStrong: "var(--color-line-strong)",
  sunken: "var(--color-sunken)",
  subtle: "var(--color-subtle)",
  raised: "var(--color-raised)",
  success: "var(--color-success-600)",
  danger: "var(--color-danger-600)",
  warning: "var(--color-warning-600)",
};

const FONT = "var(--font-sans), system-ui, sans-serif";

function Art({ viewBox, className, children }: { viewBox: string; className?: string; children: ReactNode }) {
  return (
    <svg viewBox={viewBox} className={className} aria-hidden="true" focusable="false">
      {children}
    </svg>
  );
}

/* ---------- Hero: box → store → card ---------- */

export function BoxArt({ className }: { className?: string }) {
  return (
    <Art viewBox="0 0 120 120" className={className}>
      <circle cx="60" cy="60" r="56" fill={c.brand50} />
      <polygon points="30,50 90,50 82,36 38,36" fill={c.accent300} />
      <polygon points="54,50 66,50 64,36 56,36" fill={c.accent100} />
      <rect x="30" y="50" width="60" height="44" rx="3" fill={c.accent400} />
      <rect x="54" y="50" width="12" height="44" fill={c.accent200} />
      <rect x="35" y="70" width="15" height="12" rx="1.5" fill={c.raised} />
      <rect x="37.5" y="73.5" width="9" height="1.8" fill={c.subtle} />
      <rect x="37.5" y="77" width="6" height="1.8" fill={c.subtle} />
    </Art>
  );
}

export function StoreArt({ className }: { className?: string }) {
  return (
    <Art viewBox="0 0 120 120" className={className}>
      <circle cx="60" cy="60" r="56" fill={c.brand50} />
      <rect x="30" y="46" width="60" height="46" fill={c.raised} stroke={c.brand600} strokeWidth="3" />
      <rect x="26" y="32" width="68" height="14" rx="2" fill={c.brand600} />
      {[34.5, 51.5, 68.5, 85.5].map((x) => (
        <rect key={x} x={x} y="32" width="8.5" height="14" fill={c.accent400} />
      ))}
      {[30.25, 38.75, 47.25, 55.75, 64.25, 72.75, 81.25, 89.75].map((cx, i) => (
        <circle key={cx} cx={cx} cy="46" r="4.25" fill={i % 2 === 0 ? c.brand600 : c.accent400} />
      ))}
      <rect x="36" y="56" width="12" height="12" rx="2" fill={c.brand100} />
      <rect x="72" y="56" width="12" height="12" rx="2" fill={c.brand100} />
      <rect x="52" y="64" width="16" height="28" fill={c.brand100} />
      <circle cx="64.5" cy="79" r="1.6" fill={c.brand700} />
    </Art>
  );
}

export function CardArt({ className }: { className?: string }) {
  return (
    <Art viewBox="0 0 120 120" className={className}>
      <circle cx="60" cy="60" r="56" fill={c.brand50} />
      <rect x="20" y="36" width="72" height="46" rx="7" fill={c.brand600} />
      <rect x="20" y="46" width="72" height="9" fill={c.brand900} />
      <rect x="29" y="62" width="13" height="10" rx="2" fill={c.accent400} />
      <circle cx="86" cy="80" r="17" fill={c.success} stroke={c.raised} strokeWidth="3" />
      <text x="86" y="86.5" textAnchor="middle" fontSize="19" fontWeight="700" fill={c.raised} fontFamily={FONT}>
        $
      </text>
    </Art>
  );
}

export function FlowArrow({ className }: { className?: string }) {
  return (
    <Art viewBox="0 0 32 16" className={className}>
      <path d="M2 8h24" stroke={c.brand500} strokeWidth="3" strokeLinecap="round" strokeDasharray="1 6" />
      <path d="M22 2l7 6-7 6" fill="none" stroke={c.brand500} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
    </Art>
  );
}

/* ---------- The four steps ---------- */

function StepFrame({ children }: { children: ReactNode }) {
  return (
    <Art viewBox="0 0 200 130" className="h-auto w-full">
      <rect width="200" height="130" rx="14" fill={c.brand50} />
      {children}
    </Art>
  );
}

export function StepPickArt() {
  return (
    <StepFrame>
      <rect x="30" y="16" width="140" height="100" rx="10" fill={c.raised} stroke={c.line} strokeWidth="1.5" />
      <rect x="35" y="53" width="130" height="32" rx="7" fill={c.brand50} stroke={c.brand600} strokeWidth="2" />
      {[28, 58, 88].map((y, i) => (
        <g key={y}>
          <rect x="41" y={y} width="22" height="22" rx="5" fill={i === 1 ? c.brand100 : c.sunken} />
          <rect x="70" y={y + 4} width="56" height="6" rx="3" fill={i === 1 ? c.brand300 : c.lineStrong} />
          <rect x="70" y={y + 14} width="36" height="5" rx="2.5" fill={c.line} />
        </g>
      ))}
      {/* tiny headphones on the chosen item */}
      <path d="M46 71a6 6 0 0 1 12 0" fill="none" stroke={c.brand700} strokeWidth="2.2" />
      <rect x="44" y="69" width="4" height="7" rx="1.5" fill={c.brand700} />
      <rect x="56" y="69" width="4" height="7" rx="1.5" fill={c.brand700} />
      <circle cx="149" cy="69" r="9" fill={c.brand600} />
      <path d="M145 69l3 3 5.5-6" fill="none" stroke={c.raised} strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M156 80v22l6-6 5 10 4.5-2-5-10h8.5z" fill={c.ink} stroke={c.raised} strokeWidth="1.5" strokeLinejoin="round" />
    </StepFrame>
  );
}

export function StepQuoteArt() {
  return (
    <StepFrame>
      <path
        d="M58 14h84v90l-8.4 6-8.4-6-8.4 6-8.4-6-8.4 6-8.4-6-8.4 6-8.4-6-8.4 6-8.4-6z"
        fill={c.raised}
        stroke={c.line}
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <rect x="70" y="26" width="42" height="6" rx="3" fill={c.lineStrong} />
      <rect x="70" y="40" width="58" height="5" rx="2.5" fill={c.line} />
      <rect x="70" y="50" width="46" height="5" rx="2.5" fill={c.line} />
      <path d="M70 64h60" stroke={c.lineStrong} strokeWidth="1.5" strokeDasharray="3 3" />
      <text x="70" y="89" fontSize="20" fontWeight="800" fill={c.success} fontFamily={FONT}>
        $29.16
      </text>
      <circle cx="146" cy="26" r="15" fill={c.accent400} stroke={c.raised} strokeWidth="3" />
      <path d="M146 18.5V26h6" fill="none" stroke={c.ink} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </StepFrame>
  );
}

export function StepConfirmArt() {
  return (
    <StepFrame>
      <rect x="84" y="8" width="62" height="114" rx="11" fill={c.ink} />
      <rect x="89" y="16" width="52" height="98" rx="6" fill={c.raised} />
      <rect x="96" y="26" width="30" height="5" rx="2.5" fill={c.lineStrong} />
      <rect x="96" y="37" width="38" height="4" rx="2" fill={c.line} />
      <rect x="96" y="46" width="26" height="4" rx="2" fill={c.line} />
      <rect x="96" y="82" width="38" height="16" rx="8" fill={c.brand600} />
      <path d="M109 90l3 3 6-6.5" fill="none" stroke={c.raised} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="124" cy="94" r="7" fill="none" stroke={c.accent600} strokeWidth="2.5" />
      <circle cx="124" cy="94" r="13" fill="none" stroke={c.accent600} strokeWidth="2" opacity=".5" />
      {/* spoken "yes" */}
      <rect x="18" y="40" width="54" height="30" rx="10" fill={c.success} />
      <path d="M62 68l14 8-4-10z" fill={c.success} />
      <text x="45" y="60.5" textAnchor="middle" fontSize="15" fontWeight="700" fill={c.raised} fontFamily={FONT}>
        “Yes”
      </text>
    </StepFrame>
  );
}

export function StepShipArt() {
  return (
    <StepFrame>
      <path d="M16 100h168" stroke={c.lineStrong} strokeWidth="2" strokeLinecap="round" />
      {/* box waiting at the curb */}
      <polygon points="28,66 70,66 65,56 33,56" fill={c.accent300} />
      <rect x="28" y="66" width="42" height="34" rx="3" fill={c.accent400} />
      <rect x="45" y="66" width="8" height="34" fill={c.accent200} />
      <rect x="31" y="76" width="11" height="9" rx="1" fill={c.raised} />
      {/* truck heading back to us */}
      <rect x="86" y="46" width="66" height="44" rx="4" fill={c.brand600} />
      <path d="M152 58h20l14 16v16h-34z" fill={c.brand500} />
      <path d="M156 62h14l9 11h-23z" fill={c.brand100} />
      <path d="M136 68h-30m6-6-6 6 6 6" fill="none" stroke={c.raised} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      {[106, 168].map((cx) => (
        <g key={cx}>
          <circle cx={cx} cy="91" r="9" fill={c.ink} />
          <circle cx={cx} cy="91" r="3.5" fill={c.lineStrong} />
        </g>
      ))}
    </StepFrame>
  );
}

/* ---------- What can be returned ---------- */

export function CalendarArt({ className }: { className?: string }) {
  return (
    <Art viewBox="0 0 96 96" className={className}>
      <rect x="14" y="20" width="68" height="62" rx="9" fill={c.raised} stroke={c.line} strokeWidth="2" />
      <path d="M14 29a9 9 0 0 1 9-9h50a9 9 0 0 1 9 9v7H14z" fill={c.success} />
      <rect x="29" y="13" width="6" height="14" rx="3" fill={c.ink} />
      <rect x="61" y="13" width="6" height="14" rx="3" fill={c.ink} />
      <text x="48" y="71" textAnchor="middle" fontSize="27" fontWeight="800" fill={c.ink} fontFamily={FONT}>
        30
      </text>
    </Art>
  );
}

export function ElectronicsArt({ className }: { className?: string }) {
  return (
    <Art viewBox="0 0 96 96" className={className}>
      <path d="M22 56a24 24 0 0 1 48 0" fill="none" stroke={c.brand600} strokeWidth="6" strokeLinecap="round" />
      <rect x="15" y="52" width="14" height="24" rx="6" fill={c.brand600} />
      <rect x="63" y="52" width="14" height="24" rx="6" fill={c.brand600} />
      <path d="M74 74l12 12" stroke={c.warning} strokeWidth="7" strokeLinecap="round" />
      <circle cx="66" cy="66" r="13" fill={c.raised} stroke={c.warning} strokeWidth="5" />
    </Art>
  );
}

export function GiftCardArt({ className }: { className?: string }) {
  return (
    <Art viewBox="0 0 96 96" className={className}>
      <rect x="10" y="26" width="66" height="44" rx="7" fill={c.accent300} />
      <rect x="32" y="26" width="8" height="44" fill={c.accent400} />
      <rect x="10" y="44" width="66" height="8" fill={c.accent400} />
      <circle cx="31" cy="44" r="5" fill="none" stroke={c.accent700} strokeWidth="3" />
      <circle cx="41" cy="44" r="5" fill="none" stroke={c.accent700} strokeWidth="3" />
      <circle cx="74" cy="70" r="15" fill={c.danger} stroke={c.raised} strokeWidth="3" />
      <path d="M68 64l12 12m0-12L68 76" stroke={c.raised} strokeWidth="3.5" strokeLinecap="round" />
    </Art>
  );
}

/* ---------- Line icons the shared set doesn't have (same 24px / 1.75 stroke style) ---------- */

function LineIcon({ className, children }: { className?: string; children: ReactNode }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={cn("size-5 shrink-0", className)}
      fill="none"
      stroke="currentColor"
      strokeWidth="1.75"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {children}
    </svg>
  );
}

export const BoltIcon = ({ className }: { className?: string }) => (
  <LineIcon className={className}>
    <path d="M13 2 4 14h7l-1 8 9-12h-7z" />
  </LineIcon>
);
export const ScanIcon = ({ className }: { className?: string }) => (
  <LineIcon className={className}>
    <path d="M3 7V5a2 2 0 0 1 2-2h2M17 3h2a2 2 0 0 1 2 2v2M21 17v2a2 2 0 0 1-2 2h-2M7 21H5a2 2 0 0 1-2-2v-2" />
    <path d="M8 8v8M12 8v8M16 8v8" />
  </LineIcon>
);
export const WarehouseIcon = ({ className }: { className?: string }) => (
  <LineIcon className={className}>
    <path d="M3 21V9l9-5 9 5v12" />
    <path d="M7 21v-8h10v8M7 17h10" />
  </LineIcon>
);
