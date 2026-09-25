import type { Metadata } from "next";

export const metadata: Metadata = { title: "Terms" };

export default function TermsPage() {
  return (
    <>
      <h1>Terms</h1>
      <p>
        <strong>Sandbox notice:</strong> Larkspur is a portfolio demonstration, not a real store.
        Payments run in Stripe test mode, nothing ships, and no real money moves.
      </p>
      <h2>Returns</h2>
      <p>
        The sandbox return policy is 30 days from delivery. Gift cards are final sale. Electronics
        are refunded after inspection. Refunds go back to the original payment method.
      </p>
    </>
  );
}
