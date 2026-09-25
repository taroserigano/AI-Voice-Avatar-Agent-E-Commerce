import type { Metadata } from "next";

export const metadata: Metadata = { title: "Privacy" };

export default function PrivacyPage() {
  return (
    <>
      <h1>Privacy</h1>
      <p>
        <strong>Sandbox notice:</strong> Larkspur is a portfolio demonstration. This page describes how
        the demo handles data; a real privacy policy must be written and approved before any live use.
      </p>
      <h2>What we store</h2>
      <p>
        Your name, email, a hashed password, your cart, and your orders. Payment card details are
        entered on Stripe&apos;s hosted page and never reach our servers.
      </p>
      <h2>Monitoring</h2>
      <p>
        We record technical traces and logs to keep the service working. Emails, names, addresses,
        and card-like numbers are removed before these are stored, and customers appear only as a
        one-way hash.
      </p>
      <h2>The assistant</h2>
      <p>
        When you use the text or voice assistant, we send only what it needs to answer. Audio
        recording is off by default.
      </p>
    </>
  );
}
