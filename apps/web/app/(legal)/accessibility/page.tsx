import type { Metadata } from "next";

export const metadata: Metadata = { title: "Accessibility" };

export default function AccessibilityPage() {
  return (
    <>
      <h1>Accessibility</h1>
      <p>
        Larkspur aims to meet the Web Content Accessibility Guidelines (WCAG) 2.2 at level AA. Every
        page works with a keyboard, shows where focus is, and labels its controls for screen readers.
        Sign-in works with password managers and allows pasting.
      </p>
      <h2>Known gaps</h2>
      <p>
        A full audit is scheduled before any pilot. If something doesn&apos;t work for you, the
        assistant can hand you to a person, and every task can also be done without it.
      </p>
    </>
  );
}
